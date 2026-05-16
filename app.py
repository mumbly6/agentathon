"""
Mama Bidii Chama Dispute Arbitrator - Cloud Run API
Endpoints: /health, /chat
"""

import os
import json
from flask import Flask, request, jsonify
from agent_tools import (
    search_bylaws,
    get_member_financial_status,
    calculate_loan_eligibility,
    verify_ledger_transaction,
)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Mama Bidii Chama Dispute Arbitrator",
        "version": "1.0.0",
    })


@app.route("/chat", methods=["POST"])
def chat():
    """
    Dispute resolution chat endpoint.
    Accepts JSON: {"message": "user dispute text", "member_name": "optional"}
    Returns arbitration response with bylaw references and financial evidence.
    """
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Please provide a 'message' field with your dispute."}), 400

    # Extract member name if provided
    member_name = data.get("member_name", "")

    # Build response by calling agent tools
    response_parts = []

    # 1. Search bylaws for relevant rules
    bylaw_result = search_bylaws(message)
    response_parts.append({
        "section": "SHERIA HUSIKA (Applicable Bylaws)",
        "content": bylaw_result,
    })

    # 2. If member name given, get financial status
    if member_name:
        financial_status = get_member_financial_status(member_name)
        response_parts.append({
            "section": "USHAHIDI WA KIFEDHA (Financial Evidence)",
            "content": financial_status,
        })

        # 3. Check loan eligibility if query is loan-related
        loan_keywords = ["loan", "mkopo", "borrow", "eligib"]
        if any(kw in message.lower() for kw in loan_keywords):
            loan_result = calculate_loan_eligibility(member_name)
            response_parts.append({
                "section": "USTAHILI WA MKOPO (Loan Eligibility)",
                "content": loan_result,
            })

        # 4. Verify ledger
        ledger = verify_ledger_transaction(member_name)
        response_parts.append({
            "section": "REKODI ZA M-PESA (Ledger Verification)",
            "content": ledger,
        })

    return jsonify({
        "dispute": message,
        "arbitration": response_parts,
        "disclaimer": "Uamuzi huu unategemea sheria za Mama Bidii Chama na rekodi za M-Pesa.",
    })


@app.route("/members", methods=["GET"])
def list_members():
    """List all chama members."""
    members_path = os.path.join(os.path.dirname(__file__), "data", "members.json")
    with open(members_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/member/<name>", methods=["GET"])
def member_status(name):
    """Get a specific member's financial status."""
    result = get_member_financial_status(name)
    return jsonify(result)


@app.route("/loan-check/<name>", methods=["GET"])
def loan_check(name):
    """Check loan eligibility for a member."""
    result = calculate_loan_eligibility(name)
    return jsonify(result)


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        "service": "Mama Bidii Chama Dispute Arbitrator",
        "description": "AI-powered arbitration for Kenyan chama disputes using bylaws and M-Pesa records.",
        "endpoints": {
            "GET /health": "Health check",
            "POST /chat": "Submit a dispute for arbitration. Body: {\"message\": \"...\", \"member_name\": \"...\"}",
            "GET /members": "List all chama members",
            "GET /member/<name>": "Get member financial status",
            "GET /loan-check/<name>": "Check loan eligibility",
        },
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
