"""
Chama Dispute Arbitrator - Agent Tools
Tools for searching bylaws, verifying financial records, and calculating loan eligibility.
These functions are registered as Vertex AI Agent tools.
"""

from typing import Dict, List
import json
import csv
import os

# Resolve data directory relative to this script
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def search_bylaws(query: str) -> str:
    """
    Tool to search chama bylaws.
    Returns relevant articles with section numbers.

    Args:
        query: The dispute or question to search bylaws for.

    Returns:
        Relevant bylaw articles and sections matching the query.
    """
    # Load full bylaws text
    bylaws_path = os.path.join(DATA_DIR, "chama_bylaws.txt")
    try:
        with open(bylaws_path, "r", encoding="utf-8") as f:
            full_bylaws = f.read()
    except FileNotFoundError:
        return "ERROR: Bylaws file not found at expected path."

    # Keyword-to-article mapping for fast local lookup
    # In production, this is replaced by Vertex AI Search (RAG) API call
    bylaws_knowledge = {
        "missed contributions": "ARTICLE 1, Section 1.3: Three consecutive missed contributions result in automatic suspension",
        "missed payment": "ARTICLE 1, Section 1.3: Three consecutive missed contributions result in automatic suspension",
        "suspend": "ARTICLE 1, Section 1.3: Three consecutive missed contributions result in automatic suspension",
        "suspension": "ARTICLE 1, Section 1.3: Three consecutive missed contributions result in automatic suspension",
        "reinstate": "ARTICLE 1, Section 1.4: Suspended members must clear all arrears to be reinstated",
        "late fee": "ARTICLE 1, Section 1.2: Late fee of KES 200 per week applies after due date",
        "late payment": "ARTICLE 1, Section 1.2: Late fee of KES 200 per week applies after due date",
        "contribution": "ARTICLE 1, Section 1.1: Monthly contribution is KES 2,000 due by 5th of each month",
        "monthly": "ARTICLE 1, Section 1.1: Monthly contribution is KES 2,000 due by 5th of each month",
        "loan eligibility": "ARTICLE 2, Section 2.1: Members eligible after 6 months of consistent contributions",
        "loan": "ARTICLE 2, Section 2.1-2.5: Eligible after 6 months, max 3x contributions, 10% interest, 12 month repayment, no new loans while outstanding",
        "mkopo": "ARTICLE 2, Section 2.1-2.5: Eligible after 6 months, max 3x contributions, 10% interest, 12 month repayment, no new loans while outstanding",
        "maximum loan": "ARTICLE 2, Section 2.2: Maximum loan is 3 times total contributions",
        "interest": "ARTICLE 2, Section 2.3: Interest rate is 10% per annum",
        "repayment": "ARTICLE 2, Section 2.4: Repayment period maximum 12 months",
        "outstanding loan": "ARTICLE 2, Section 2.5: No new loans while existing loan is outstanding",
        "withdraw": "ARTICLE 3, Section 3.1-3.4: 30 days notice, entitled to contributions only, clear loans first, no withdrawal during repayment",
        "withdrawal": "ARTICLE 3, Section 3.1-3.4: 30 days notice, entitled to contributions only, clear loans first, no withdrawal during repayment",
        "emergency": "ARTICLE 4, Section 4.1-4.4: 10% to emergency fund, medical only, documents required, 48hr committee approval",
        "hospital": "ARTICLE 4, Section 4.3: Supporting documents required (hospital receipt, doctor's note)",
        "medical": "ARTICLE 4, Section 4.2: Only accessible for medical emergencies",
        "document": "ARTICLE 4, Section 4.3: Supporting documents required (hospital receipt, doctor's note)",
        "dispute": "ARTICLE 5, Section 5.1-5.4: Referred to arbitration, treasurer presents records, 14 day decision, majority vote",
        "arbitration": "ARTICLE 5, Section 5.1: All disputes referred to arbitration",
    }

    # Search for matching keywords in query
    query_lower = query.lower()
    matches = []
    seen_articles = set()

    for keyword, article in bylaws_knowledge.items():
        if keyword in query_lower and article not in seen_articles:
            matches.append(article)
            seen_articles.add(article)

    if matches:
        return "\n\n".join(matches)

    # Fallback: return full bylaws text for the agent to parse
    return f"No specific match found. Full bylaws for reference:\n\n{full_bylaws}"


def get_member_financial_status(member_name: str) -> Dict:
    """
    Tool to get member's financial position from records.
    Returns contribution history, late fees, loans, and account status.

    Args:
        member_name: Name of the chama member to look up.

    Returns:
        Dictionary with member's financial status including contributions,
        missed payments, late fees, loan balance, and account status.
    """
    members_path = os.path.join(DATA_DIR, "members.json")
    mpesa_path = os.path.join(DATA_DIR, "mpesa_records.csv")

    # Load member data
    try:
        with open(members_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": "Members database not found."}

    # Find member (case-insensitive, partial match)
    member_record = None
    for member in data["members"]:
        if member_name.lower() in member["name"].lower() or member["name"].lower() in member_name.lower():
            member_record = member
            break

    if not member_record:
        return {"error": f"Member '{member_name}' not found in records."}

    # Load M-Pesa transaction history for this member
    transactions = []
    try:
        with open(mpesa_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if member_record["name"].lower() in row["Member"].lower():
                    transactions.append({
                        "date": row["Date"],
                        "amount": int(row["Amount"]),
                        "type": row["Type"],
                        "reference": row["Reference"],
                    })
    except FileNotFoundError:
        pass  # Continue without transaction history

    # Determine account status
    status = "SUSPENDED" if member_record["missed_payments"] >= 3 else "ACTIVE"

    return {
        "name": member_record["name"],
        "member_id": member_record["id"],
        "phone": member_record["phone"],
        "joined": member_record["joined"],
        "total_contributions": member_record["total_contributions"],
        "missed_payments": member_record["missed_payments"],
        "late_fees_owed": member_record["late_fees_owed"],
        "loan_balance": member_record["loan_balance"],
        "status": status,
        "transaction_history": transactions,
    }


def calculate_loan_eligibility(member_name: str) -> Dict:
    """
    Tool to calculate if member is eligible for loan and maximum amount.
    Cross-references bylaws ARTICLE 2 with member's financial records.

    Args:
        member_name: Name of the chama member to check eligibility for.

    Returns:
        Dictionary with eligibility status, maximum loan amount,
        reason for decision, and bylaw references.
    """
    status = get_member_financial_status(member_name)

    if "error" in status:
        return status

    # Check membership duration (Article 2.1: eligible after 6 months)
    from datetime import datetime

    joined_date = datetime.strptime(status["joined"], "%Y-%m-%d")
    months_active = (datetime.now() - joined_date).days / 30

    if months_active < 6:
        return {
            "member": status["name"],
            "eligible": False,
            "max_loan_amount": 0,
            "reason": f"Member has only been active {int(months_active)} months. Minimum 6 months required.",
            "bylaw_reference": "ARTICLE 2, Section 2.1: Members eligible after 6 months of consistent contributions",
        }

    # Check account status
    if status["status"] == "SUSPENDED":
        return {
            "member": status["name"],
            "eligible": False,
            "max_loan_amount": 0,
            "reason": f"Member is SUSPENDED with {status['missed_payments']} missed payments. Must clear arrears first.",
            "bylaw_reference": "ARTICLE 1, Section 1.4: Suspended members must clear all arrears to be reinstated",
        }

    # Check outstanding loan (Article 2.5)
    has_outstanding_loan = status["loan_balance"] > 0
    if has_outstanding_loan:
        return {
            "member": status["name"],
            "eligible": False,
            "max_loan_amount": 0,
            "current_loan_balance": status["loan_balance"],
            "reason": f"Outstanding loan of KES {status['loan_balance']:,} must be cleared first.",
            "bylaw_reference": "ARTICLE 2, Section 2.5: No new loans while existing loan is outstanding",
        }

    # Check late fees
    if status["late_fees_owed"] > 0:
        return {
            "member": status["name"],
            "eligible": False,
            "max_loan_amount": 0,
            "late_fees_owed": status["late_fees_owed"],
            "reason": f"Outstanding late fees of KES {status['late_fees_owed']:,} must be cleared first.",
            "bylaw_reference": "ARTICLE 1, Section 1.2 & ARTICLE 2, Section 2.1: Consistent contributions required",
        }

    # Calculate maximum loan (Article 2.2: 3x total contributions)
    max_loan_amount = status["total_contributions"] * 3

    return {
        "member": status["name"],
        "eligible": True,
        "max_loan_amount": max_loan_amount,
        "total_contributions": status["total_contributions"],
        "interest_rate": "10% per annum",
        "max_repayment_period": "12 months",
        "reason": "Member meets all eligibility criteria.",
        "bylaw_reference": "ARTICLE 2, Section 2.1, 2.2, 2.3, 2.4, 2.5",
    }


def verify_ledger_transaction(member_name: str, month: str = None, transaction_type: str = None) -> Dict:
    """
    Tool to verify specific transactions in the M-Pesa ledger.
    Used to fact-check claims during disputes.

    Args:
        member_name: Name of the chama member.
        month: Optional month to filter (e.g., "2024-01", "January").
        transaction_type: Optional type filter (Contribution, Late Fee, MISSED, Loan Disbursement).

    Returns:
        Dictionary with matching transactions and verification summary.
    """
    mpesa_path = os.path.join(DATA_DIR, "mpesa_records.csv")

    try:
        with open(mpesa_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_transactions = list(reader)
    except FileNotFoundError:
        return {"error": "M-Pesa records file not found."}

    # Filter by member name
    member_txns = [
        row for row in all_transactions
        if member_name.lower() in row["Member"].lower()
    ]

    if not member_txns:
        return {
            "error": f"No transactions found for '{member_name}'.",
            "available_members": list(set(row["Member"] for row in all_transactions)),
        }

    # Filter by month if provided
    if month:
        month_lower = month.lower()
        # Handle both "2024-01" and "January" formats
        month_map = {
            "january": "01", "february": "02", "march": "03",
            "april": "04", "may": "05", "june": "06",
            "july": "07", "august": "08", "september": "09",
            "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        }
        for name, num in month_map.items():
            if name in month_lower:
                month_lower = f"2024-{num}"
                break
        member_txns = [row for row in member_txns if month_lower in row["Date"]]

    # Filter by transaction type if provided
    if transaction_type:
        member_txns = [
            row for row in member_txns
            if transaction_type.lower() in row["Type"].lower()
        ]

    # Build result
    results = []
    for txn in member_txns:
        results.append({
            "date": txn["Date"],
            "member": txn["Member"],
            "amount": f"KES {int(txn['Amount']):,}",
            "type": txn["Type"],
            "reference": txn["Reference"],
        })

    return {
        "member": member_name,
        "total_matching_transactions": len(results),
        "transactions": results,
        "verification_timestamp": "2026-05-16T14:46:00+03:00",
        "source": "M-Pesa Records Ledger (mpesa_records.csv)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tool Registry for Vertex AI Agent Builder
# ─────────────────────────────────────────────────────────────────────────────

TOOLS_REGISTRY = [
    {
        "name": "search_bylaws",
        "description": "Tafuta sheria za chama. Search chama bylaws for rules and articles relevant to a dispute.",
        "function": search_bylaws,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The dispute or question to search bylaws for",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_member_financial_status",
        "description": "Pata hali ya kifedha ya mwanachama. Get member's full financial status from M-Pesa records.",
        "function": get_member_financial_status,
        "parameters": {
            "type": "object",
            "properties": {
                "member_name": {
                    "type": "string",
                    "description": "Name of the chama member",
                }
            },
            "required": ["member_name"],
        },
    },
    {
        "name": "calculate_loan_eligibility",
        "description": "Hesabu kama mwanachama anastahili mkopo. Calculate if member qualifies for a loan and max amount.",
        "function": calculate_loan_eligibility,
        "parameters": {
            "type": "object",
            "properties": {
                "member_name": {
                    "type": "string",
                    "description": "Name of the chama member",
                }
            },
            "required": ["member_name"],
        },
    },
    {
        "name": "verify_ledger_transaction",
        "description": "Thibitisha malipo kwenye rekodi za M-Pesa. Verify specific transactions in the ledger for fact-checking disputes.",
        "function": verify_ledger_transaction,
        "parameters": {
            "type": "object",
            "properties": {
                "member_name": {
                    "type": "string",
                    "description": "Name of the chama member",
                },
                "month": {
                    "type": "string",
                    "description": "Optional: month to filter (e.g., '2024-01' or 'January')",
                },
                "transaction_type": {
                    "type": "string",
                    "description": "Optional: type filter (Contribution, Late Fee, MISSED, Loan Disbursement)",
                },
            },
            "required": ["member_name"],
        },
    },
]
