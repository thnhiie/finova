# FINOVA — Render deployment starter

This is a Flask starter app based on the FINOVA specification in the supplied Word document. It includes the supplied logo and a responsive light/dark interface with fixed navigation, account registration/login, profile editing, financial inputs, calculations, five scenario simulations, what-if analysis, goal planning, evaluation, FAQ, support requests, a grounded rule-based chatbot, and a downloadable financial report.

## Deploy to Render

1. Create a new GitHub repository and upload all files in this folder.
2. In Render, choose **New + → Blueprint** and select the repository (or create a Web Service).
3. If creating a Web Service, use:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Add a `SECRET_KEY` environment variable with a long random value. Do not use the development fallback for a public deployment.
5. Deploy. The app creates a local SQLite database on first start.

## Important implementation notes

- The supplied logo is at `static/logo.png`.
- The app uses VND and formats amounts with commas, rejects negative financial inputs, and includes examples beside fields.
- Scenario assumptions are explicit demo assumptions: Severely Conservative (income −25%, expenses +25%), Conservative (income −10%, expenses +10%), Baseline, Optimistic (income +10%), Highly Optimistic (income +20%, expenses −5%).
- The scenario “suitability” scores are rule-based illustrative indicators, not probabilities or validated AI rankings.
- The chatbot is rule-based and does **not** pretend to call an LLM. To implement the four specified LLM tasks (input/Excel parsing, goal prioritization, trade-off/risk explanation, and RAG support chatbot), connect a server-side LLM provider using an environment variable, add retrieval documents, validate all outputs against Python calculations, and never expose API keys in client-side code.
- Password recovery in this prototype lets a user set a new password after entering an email; it does not send a verification email. Replace it with a secure email token flow before production.
- The export currently produces an Excel-compatible CSV report, not a native `.xlsx` workbook. Native XLSX import/export, saved multiple planning options, file-based Excel parsing, uploaded attachment storage, production email delivery, and self-service account deletion are not implemented yet.
- SQLite on a typical ephemeral Render filesystem may not persist across deploys/restarts. For durable multi-user production use, attach a persistent disk or switch to Render PostgreSQL and add backups.
- This is an educational prototype, not a certified financial tool or investment advice. Review security, privacy, financial formulas, testing, and legal requirements before using real customer data.

## Local run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.
