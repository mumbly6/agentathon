"""
Mama Bidii Chama Dispute Arbitrator - Cloud Run API
Endpoints: /, /health, /chat, /members, /member/<name>, /loan-check/<name>
"""

import os
import json
from flask import Flask, request, jsonify, render_template
from agent_tools import (
    search_bylaws,
    get_member_financial_status,
    calculate_loan_eligibility,
    verify_ledger_transaction,
)

app = Flask(__name__)

# Gemini integration via Google AI API key
GEMINI_ENABLED = False
client = None

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_ENABLED = True
        print("✅ Gemini connected via API key")
    except Exception as e:
        print(f"⚠️ Gemini init failed: {e}")
else:
    print("⚠️ No GEMINI_API_KEY set, using tool-only mode")

SYSTEM_PROMPT = """You are Msuluhishi wa Migogoro ya Mama Bidii Chama (Chama Dispute Arbitrator).
You resolve disputes using bylaws and M-Pesa records. Respond in the user's language (Swahili/Sheng/English).
Always cite specific ARTICLE & Section numbers. Never fabricate financial data.
Structure: 📋 Summary → 📜 Bylaws → 📊 Evidence → ⚖️ Verdict → 💡 Next Steps."""


@app.route("/")
def index():
    """Serve the frontend UI."""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "Mama Bidii Chama Dispute Arbitrator",
                     "version": "1.0.0", "gemini": GEMINI_ENABLED})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Please provide a 'message' field."}), 400

    member_name = data.get("member_name", "")

    # Gather tool evidence
    arbitration = []
    bylaw_result = search_bylaws(message)
    arbitration.append({"section": "📜 SHERIA (Bylaws)", "content": bylaw_result})

    if member_name:
        financial_status = get_member_financial_status(member_name)
        arbitration.append({"section": "📊 USHAHIDI (Financial Evidence)", "content": financial_status})

        loan_kws = ["loan", "mkopo", "borrow", "eligib"]
        if any(kw in message.lower() for kw in loan_kws):
            arbitration.append({"section": "🏦 MKOPO (Loan Check)", "content": calculate_loan_eligibility(member_name)})

        arbitration.append({"section": "📒 REKODI (Ledger)", "content": verify_ledger_transaction(member_name)})

    # If Gemini available, generate natural language verdict
    ai_response = None
    if GEMINI_ENABLED:
        try:
            context = json.dumps(arbitration, default=str, indent=2)
            prompt = f"{SYSTEM_PROMPT}\n\nDISPUTE: {message}\nMEMBER: {member_name or 'Not specified'}\n\nEVIDENCE FROM TOOLS:\n{context}\n\nGive your arbitration verdict:"
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            ai_response = resp.text
        except Exception as e:
            ai_response = f"Gemini error: {str(e)}"

    return jsonify({"dispute": message, "arbitration": arbitration,
                     "ai_response": ai_response,
                     "disclaimer": "Uamuzi huu unategemea sheria za Mama Bidii Chama na rekodi za M-Pesa."})


@app.route("/members", methods=["GET"])
def list_members():
    p = os.path.join(os.path.dirname(__file__), "data", "members.json")
    with open(p, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/member/<name>", methods=["GET"])
def member_status(name):
    return jsonify(get_member_financial_status(name))


@app.route("/loan-check/<name>", methods=["GET"])
def loan_check(name):
    return jsonify(calculate_loan_eligibility(name))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
