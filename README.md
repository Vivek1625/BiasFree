# 🔍 BiasFree — AI Bias Detection Tool

> **Google Solution Challenge 2026 | GDG MJCET | PS4 — Unbiased AI Decision | SDG 10.3 — Reduced Inequalities**

## 🚀 Live Demo
🌐 [https://biasfree-642026.web.app](https://biasfree-642026.web.app)

## 📌 One-Line USP
BiasFree is the only bias detection tool that combines statistical fairness analysis with Gemini AI explanations — making AI ethics accessible to any organization without a data science team.

## 🎯 Problem Statement
AI systems used in hiring, loans, and admissions often discriminate against groups based on gender, race, age, or caste — without anyone realizing it. Organizations lack accessible tools to detect and fix this bias.

## ✅ What BiasFree Does
1. User uploads a CSV dataset (hiring, loans, admissions, etc.)
2. App auto-detects sensitive columns (gender, race, age, caste)
3. App auto-detects outcome column (hired, approved, income)
4. Computes **Disparate Impact Ratio** for each sensitive column using the **80% Rule (Four-Fifths Rule)**
5. Shows **Fairness Score 0–100**
6. Gemini AI explains bias in plain English with 4 sections: Summary / What This Means / Root Causes / How to Fix It
7. Shows **Suggested Fixes** panel
8. Saves everything to Firestore
9. Requires Google Sign-In

## 📊 The 80% Rule (Core Algorithm)
Disparate Impact Ratio = Lowest Group Rate / Highest Group Rate
Below 0.8  → HIGH BIAS (legally significant)
0.8 - 0.9  → MEDIUM BIAS
Above 0.9  → LOW BIAS

## 🛠️ Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML, CSS, JavaScript (single index.html) |
| Authentication | Firebase Authentication (Google Sign-In) |
| Database | Firestore (saves every analysis) |
| Backend | Firebase Cloud Functions (Python 3.12) |
| AI | Gemini API via google-genai package |
| Hosting | Firebase Hosting |

## 🏗️ Architecture
User → Firebase Hosting (index.html)
→ Firebase Auth (Google Sign-In)
→ Cloud Function (analyze_bias)
→ pandas (CSV processing)
→ 80% Rule Algorithm
→ Gemini API (plain English explanation)
→ Firestore (save results)

## 📁 Project Structure
BiasFree/
├── public/
│   └── index.html          # Frontend UI
├── functions/
│   ├── main.py             # Cloud Function (bias analysis + Gemini)
│   └── requirements.txt    # Python dependencies
├── firebase.json           # Firebase config
├── firestore.rules         # Firestore security rules
└── BUILD_LOG.md            # Daily build log

## 🚀 Setup & Deployment
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Deploy functions
firebase deploy --only functions

# Deploy hosting
firebase deploy --only hosting
```

## 🔐 Environment Variables
Set the Gemini API key as a Firebase secret:
```bash
firebase functions:secrets:set GEMINI_API_KEY
```

## 🌍 SDG Alignment
**SDG 10.3 — Reduce Inequalities**
BiasFree directly supports SDG 10.3 by providing organizations a free, accessible tool to detect and eliminate discriminatory bias in AI decision-making systems before they impact real people.

## 👨💻 Developer
**Vivek** — Solo developer, GCET
GitHub: [Vivek1625](https://github.com/Vivek1625)
