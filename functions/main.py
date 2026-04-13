from firebase_functions import https_fn
import pandas as pd
import numpy as np
import json
import os
from flask import jsonify

@https_fn.on_request(secrets=["GEMINI_API_KEY"])
def analyze_bias(request: https_fn.Request) -> https_fn.Response:
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    headers = {"Access-Control-Allow-Origin": "*"}

    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"success": False, "error": "No file uploaded"}), 400, headers

        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({"success": False, "error": f"Could not read CSV: {str(e)}"}), 400, headers

        if df.empty or len(df) < 10:
            return jsonify({"success": False, "error": "Dataset too small. Need at least 10 rows."}), 400, headers

        sensitive_keywords = [
            "gender", "sex", "race", "ethnicity", "age",
            "religion", "nationality", "disability", "caste",
            "region", "color", "colour"
        ]

        def detect_outcome_column(df, sensitive_keywords):
            exclude_patterns = ['id', '_id', 'index', 'no', 'number', 'num', 'code']
            outcome_keywords = [
                'status', 'approved', 'hired', 'income', 'loan', 'target', 
                'label', 'outcome', 'result', 'decision', 'salary', 'wage', 
                'pay', 'earning', 'revenue', 'profit', 'loss', 'pass', 'fail', 
                'win', 'lose', 'graduate', 'dropout', 'recidivism', 'parole', 
                'bail', 'sentence'
            ]
            
            outcome_like_values = {
                'yes', 'no', 'true', 'false', '0', '1', 'approved', 'rejected', 
                'hired', 'fired', '<=50k', '>50k', 'y', 'n'
            }
            
            candidates = []
            total_cols = len(df.columns)
            for i, col in enumerate(df.columns):
                col_lower = col.lower()
                
                # Rule 6: Sensitive columns completely excluded
                if any(keyword in col_lower for keyword in sensitive_keywords):
                    continue
                    
                if any(pat in col_lower for pat in exclude_patterns):
                    continue
                
                num_unique = df[col].nunique()
                if num_unique < 2:
                    continue
                    
                unique_values = set(str(v).strip().lower() for v in df[col].dropna().unique())
                has_outcome_values = any(v in outcome_like_values for v in unique_values)
                
                # Rule 3: Reject non-binary without outcome values
                if num_unique > 2 and not has_outcome_values:
                    continue
                    
                score = 0
                
                # Rule 1: Binary columns get +5
                if num_unique == 2:
                    score += 5
                    
                # Rule 2: Keyword match +2 per hit
                for kw in outcome_keywords:
                    if kw in col_lower:
                        score += 2
                        
                # Rule 4: Values match outcome-like strings +4
                if has_outcome_values:
                    score += 4
                    
                # Rule 5: Position bonus
                position_from_end = total_cols - i
                if position_from_end == 1:
                    score += 3
                elif position_from_end == 2:
                    score += 2
                elif position_from_end == 3:
                    score += 1
                    
                candidates.append((col, score))
            
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                return candidates[0][0]
            return None

        outcome_col = detect_outcome_column(df, sensitive_keywords)
        if not outcome_col:
            outcome_col = df.columns[-1]

        def detect_sensitive_columns(df, outcome_column, sensitive_keywords):
            cols = []
            for col in df.columns:
                if col == outcome_column:
                    continue
                
                # Skip raw age columns with too many unique values
                if 'age' in col.lower() and df[col].nunique() > 15:
                    continue
                    
                if any(keyword in col.lower() for keyword in sensitive_keywords):
                    cols.append(col)
            
            if not cols:
                cols = [col for col in df.columns if col != outcome_column][:3]
            return cols

        sensitive_cols = detect_sensitive_columns(df, outcome_col, sensitive_keywords)

        bias_results = {}

        for sens_col in sensitive_cols:
            try:
                groups = df[sens_col].dropna().unique()
                if len(groups) < 2:
                    continue

                group_stats = {}

                for group in groups:
                    group_df = df[df[sens_col] == group]
                    outcome_series = group_df[outcome_col]

                    if outcome_series.dtype == object or outcome_series.dtype.name == "category":
                        positive_values = [
                            "yes", "hired", "approved", "accepted",
                            "1", "true", "admit", "selected",
                            "promoted", "passed", ">50k", ">50K"
                        ]
                        positive_rate = outcome_series.astype(str).str.strip().str.lower().isin(positive_values).mean()
                    else:
                        positive_rate = (outcome_series > 0).mean()

                    group_stats[str(group)] = {
                        "count": int(len(group_df)),
                        "positive_rate": round(float(positive_rate), 4),
                        "percentage": round(float(len(group_df) / len(df) * 100), 1)
                    }

                rates = [v["positive_rate"] for v in group_stats.values() if v["count"] >= 5]

                if not rates or max(rates) == 0:
                    continue

                disparate_impact = round(min(rates) / max(rates), 4)
                min_group = min(group_stats, key=lambda g: group_stats[g]["positive_rate"])
                max_group = max(group_stats, key=lambda g: group_stats[g]["positive_rate"])

                if disparate_impact < 0.8:
                    bias_level = "HIGH"
                elif disparate_impact < 0.9:
                    bias_level = "MEDIUM"
                else:
                    bias_level = "LOW"

                bias_results[sens_col] = {
                    "disparate_impact_ratio": disparate_impact,
                    "bias_level": bias_level,
                    "is_biased": disparate_impact < 0.8,
                    "most_disadvantaged_group": min_group,
                    "most_advantaged_group": max_group,
                    "outcome_column": outcome_col,
                    "group_statistics": group_stats
                }

            except Exception:
                continue

        if bias_results:
            ratios = [r["disparate_impact_ratio"] for r in bias_results.values()]
            fairness_score = int(np.mean(ratios) * 100)
            fairness_score = max(0, min(100, fairness_score))
        else:
            fairness_score = 100

        fixes = []
        for col, result in bias_results.items():
            if result["bias_level"] == "HIGH":
                fixes.append(f"Remove or anonymize the '{col}' column before training your model")
                fixes.append(f"Apply re-weighting to give '{result['most_disadvantaged_group']}' group equal representation")
            elif result["bias_level"] == "MEDIUM":
                fixes.append(f"Monitor '{col}' closely and consider fairness constraints during model training")

        if not fixes:
            fixes = ["Dataset appears relatively fair across detected sensitive columns. Continue monitoring with new data."]

        prompt = f"""Analyze this AI bias detection result and explain it in plain English.

Dataset: {len(df)} rows
Outcome column: {outcome_col}
Sensitive columns: {', '.join(sensitive_cols)}
Fairness score: {fairness_score}/100

Bias results:
{json.dumps(bias_results, indent=2)}

Provide exactly 4 sections:
1. Summary - What did we find?
2. What This Means - Plain English explanation
3. Root Causes - Why does this bias exist?
4. How To Fix It - Concrete actionable steps"""

        gemini_explanation = get_gemini_explanation(prompt)

        return jsonify({
            "success": True,
            "dataset_summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
                "outcome_column": outcome_col,
                "sensitive_columns_detected": sensitive_cols
            },
            "overall_fairness_score": fairness_score,
            "bias_analysis": bias_results,
            "suggested_fixes": fixes,
            "gemini_explanation": gemini_explanation
        }), 200, headers

    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500, headers


def get_gemini_explanation(prompt):
    models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite"
    ]
    
    try:
        from google import genai
        import time
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        errors = []
        for model in models:
            retries = 5
            for attempt in range(retries):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    error_str = str(e)
                    try:
                        import json
                        if "{" in error_str:
                            err_json = error_str[error_str.find("{"):]
                            err_dict = json.loads(err_json)
                            msg = err_dict.get("error", {}).get("message", error_str)
                            code = err_dict.get("error", {}).get("code", 500)
                        else:
                            msg = error_str
                            code = 500
                    except:
                        msg = error_str
                        code = 500
                    
                    if code == 503 and attempt < retries - 1:
                        backoff = 2 ** attempt
                        print(f"Warning: Model {model} returned 503. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        continue
                        
                    print(f"Warning: Model {model} failed - {msg}")
                    errors.append(f"[{model}]: {code} - {msg}")
                    break # Break out of retry loop on non-503 or max retries, move to next model
                
        return "Gemini explanation unavailable. All models failed. Errors: " + " | ".join(errors)
    except Exception as e:
        return f"Gemini config error: {str(e)}"
