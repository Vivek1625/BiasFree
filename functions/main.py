from firebase_functions import https_fn
from firebase_functions.params import SecretParam
import pandas as pd
import numpy as np
import json
import os
import google.generativeai as genai
from flask import jsonify

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

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
            "region", "marital", "color", "colour"
        ]
        sensitive_cols = [
            col for col in df.columns
            if any(keyword in col.lower() for keyword in sensitive_keywords)
        ]

        outcome_keywords = [
    "income", "salary", "hired", "approved", "accepted", "outcome", 
    "decision", "result", "label", "target", "loan", "admit",
    "selected", "promoted", "passed"
]
        outcome_col = None
        for col in df.columns:
            if any(col.lower() == keyword for keyword in outcome_keywords):
                outcome_col = col
                break
        if not outcome_col:
            for col in df.columns:
                if any(keyword in col.lower() for keyword in outcome_keywords):
                    outcome_col = col
                    break
        if not outcome_col:
            outcome_col = df.columns[-1]

        if not sensitive_cols:
            sensitive_cols = [col for col in df.columns if col != outcome_col][:3]

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

        gemini_explanation = get_gemini_explanation(
            dataset_size=len(df),
            outcome_col=outcome_col,
            sensitive_cols=sensitive_cols,
            bias_results=bias_results,
            fairness_score=fairness_score
        )

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


def get_gemini_explanation(dataset_size, outcome_col, sensitive_cols, bias_results, fairness_score):
    try:
        findings_text = ""
        for col, result in bias_results.items():
            findings_text += f"\n- Column '{col}': {result['bias_level']} BIAS"
            findings_text += f"\n  Disparate Impact Ratio: {result['disparate_impact_ratio']}"
            findings_text += f"\n  Most disadvantaged group: {result['most_disadvantaged_group']}"
            findings_text += f"\n  Group breakdown: {json.dumps(result['group_statistics'])}"

        if not findings_text:
            findings_text = "No significant bias detected."

        prompt = f"""You are a fairness and AI bias expert helping a non-technical audience understand bias in their dataset.

Dataset: {dataset_size} records
Outcome column: '{outcome_col}'
Sensitive columns checked: {', '.join(sensitive_cols) if sensitive_cols else 'none detected'}
Overall Fairness Score: {fairness_score}/100

Bias Findings:
{findings_text}

Respond with exactly these 4 sections:

**Summary**
2 sentences explaining what bias was found overall.

**What This Means**
Simple explanation of who is being treated unfairly and how serious it is.

**Root Causes**
2-3 sentences on why this bias likely exists in the real world.

**How to Fix It**
3 specific actionable steps to reduce this bias.

Keep total response under 300 words. Use simple language an HR manager can understand."""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Gemini explanation unavailable: {str(e)}"
