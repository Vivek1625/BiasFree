# 🚀 BiasFree Build Log

### Day 1: Ideation & Research
- Defined the core problem: Algorithmic bias in hiring and lending.
- Mapped project to **SDG 10.3** (Reduced Inequalities).
- Selected the **80% Rule (Four-Fifths Rule)** as the mathematical engine.

### Day 2: Frontend & Firebase Setup
- Developed the UI dashboard using HTML5, CSS3, and JavaScript.
- Integrated **Firebase Authentication** for secure user access.
- Configured **Firestore** for storing bias audit reports.

### Day 3: Backend & Git Initialization
- Initialized local Git repository and pushed to GitHub.
- Scaffolded Firebase Cloud Functions (Python environment).
- Integrated `pandas` for data processing and `google-generativeai` for Gemini insights.

### Day 4: Backend Logic Complete
- Wrote complete Python Cloud Function in main.py
- Implemented real CSV bias detection using pandas
- Implemented Disparate Impact Ratio (80% Rule) calculation
- Auto-detection of sensitive columns (gender, race, age, caste, etc.)
- Auto-detection of outcome column (hired, approved, income, etc.)
- Integrated Gemini API for plain-English bias explanations
- Added Suggested Fixes panel to frontend
- Added error handling and dataset info display
- Cleaned up project: removed script.js, config.js, firebase.js, style.css
- CLOUD_FUNCTION_URL updated to live deployed URL

## Day 5: Debugging & Cloud Upgrade
- Diagnosed Gemini 404 error with model name format
- Upgraded Google Cloud account to Tier 1 Postpay billing
- Set GEMINI_API_KEY secret in Firebase Secret Manager
- Multiple deploy attempts to fix Gemini integration
- Identified root cause: google-generativeai SDK fully deprecated

## Day 6 & 7: SDK Migration & Baseline Fixes
- Migrated from google-generativeai to google-genai SDK
- Updated requirements.txt: replaced google-generativeai==0.5.4 with google-genai
- Rewrote get_gemini_explanation() using new google.genai.Client API
- Fixed outcome column auto-detection bug (was picking Loan_ID instead of Loan_Status)
- Implemented keyword scoring + low cardinality heuristic for correct outcome detection
- Submitted Google Cloud billing account verification (PAN + utility bill)

## Day 8: Gemini Model Optimization & Quota Handling
- Transitioned core model integration initially to gemini-2.0-flash and gemini-2.0-flash-lite
- Encountered and root-caused `429 RESOURCE_EXHAUSTED` free-tier quota constraints
- Designed and implemented a dynamic multi-model fallback strategy to prevent downtime
- Configured Cloud Function to recursively cycle through models dynamically upon API rejection

## Day 9: 2026 Suite Upgrade & Observability
- Resolved `404 NOT_FOUND` deployment bugs caused by deprecated legacy models (gemini-1.5-pro)
- Upgraded the AI failover array to the current 2026 suite (`gemini-3.1-flash-lite`, `gemini-3.0-flash`, `gemini-2.5-flash`, `gemini-2.0-flash`)
- Enhanced AI error handling by writing custom JSON parsing to trace and accumulate granular errors across all model attempts
- Pushed final production-ready code fixes to GitHub

## Day 10: Model Fallback Sequence Optimization
- Added `gemini-3.1-flash-lite-preview` to the model fallback sequence in `main.py` to ensure the latest preview models are prioritized.

## Day 11: Client-Side Architecture Shift & API Security
- Pivoted from Firebase Cloud Functions to a 100% client-side architecture to bypass Google Cloud billing verification blocks.
- Migrated Gemini AI generation functionality entirely into the frontend (`index.html`) using the `fetch` API.
- Implemented a "Professional Safety Net" to gracefully intercept API rate limits (`429`) and display pre-computed fallback reports.
- Optimized the dynamic model priority list to prevent rapid quota burn by initiating logic with stable models (`gemini-2.5-flash`).
- Hardened application security by securing the exposed Gemini API key via strict Google Cloud HTTP Referrer Application Restrictions.

## Day 12: API Security & Config Separation
- Resolved Google Cloud API leakage block by extracting the Gemini API key from the public HTML files.
- Implemented a two-step client-side security architecture utilizing a `.gitignore`d `config.js` file to safely inject sensitive credentials at runtime.
- Prevented future GitHub secret detection bots from automatically revoking the API key while maintaining a static, serverless deployment architecture.

## Day 13: Presentation Polish & Core Features
- Implemented robust Markdown parsing for Gemini AI outputs, ensuring plain-English reports render with proper structural elements (`<h3>`, `<strong>`, `<ul>`).
- Designed and integrated a dynamic, visual fairness score gauge (Red/Yellow/Green) to instantly contextualize numerical analysis.
- Expanded the auto-detection engine's `SENSITIVE_KEYWORDS` dictionary to include broader HR parameters (e.g., `marital`, `veteran`, `department`, `jobrole`).
- Refactored `generateFixes()` to synthesize quantitative, dataset-specific remediation strategies (e.g., target resampling ratios) rather than generic advice.
- Reframed the Gemini LLM prompt to explicitly analyze *dataset* characteristics rather than inferring *model* behavior, aligning with technical accuracy.
- Built a zero-backend PDF Report Generation tool leveraging CSS `@media print` directives for clean, standalone documentation.
- Developed an Analysis History dashboard (`history.html`) utilizing Firestore to track historical fairness scores and column-level bias metrics across sessions.
- Refined public privacy messaging and added a prominent USP to emphasize the project's accessibility.

## Day 14 & 15: Documentation, UX Polish, & Diagrams
- Generated comprehensive technical documentation summarizing the entire project context, API flows, and architecture for final submission.
- Adjusted UI elements: Removed the hero UN SDG 10 badge and dynamically displayed the SDG messaging only after analysis completes.
- Improved the unauthenticated user experience by keeping the History navigation link visible and prompting login, instead of hiding the feature entirely.
- Worked and made architecture diagram, logical order.