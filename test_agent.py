"""
Chama Dispute Arbitrator - Local Test Suite
Tests agent tools locally before Vertex AI deployment.
Run: python test_agent.py
"""

import json
from agent_tools import (
    search_bylaws,
    get_member_financial_status,
    calculate_loan_eligibility,
    verify_ledger_transaction,
)


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_search_bylaws():
    """Test bylaw search with various queries."""
    separator("TEST 1: search_bylaws")

    queries = [
        "What happens if member misses 3 contributions?",
        "late fee charges",
        "loan eligibility requirements",
        "emergency fund access",
        "withdrawal process",
    ]

    for q in queries:
        print(f"\n🔍 Query: {q}")
        result = search_bylaws(q)
        print(f"📜 Result: {result}")


def test_member_status():
    """Test member financial status lookup."""
    separator("TEST 2: get_member_financial_status")

    for name in ["Jane Wambui", "Mary Akinyi", "Unknown Person"]:
        print(f"\n👤 Member: {name}")
        result = get_member_financial_status(name)
        print(json.dumps(result, indent=2))


def test_loan_eligibility():
    """Test loan eligibility calculation."""
    separator("TEST 3: calculate_loan_eligibility")

    for name in ["Jane Wambui", "Mary Akinyi"]:
        print(f"\n💰 Checking: {name}")
        result = calculate_loan_eligibility(name)
        print(json.dumps(result, indent=2))


def test_verify_ledger():
    """Test ledger transaction verification."""
    separator("TEST 4: verify_ledger_transaction")

    # All transactions for Jane
    print("\n📒 Jane - All transactions:")
    print(json.dumps(verify_ledger_transaction("Jane Wambui"), indent=2))

    # Mary's contributions only
    print("\n📒 Mary - Contributions only:")
    print(json.dumps(verify_ledger_transaction("Mary Akinyi", transaction_type="Contribution"), indent=2))

    # Jane in February
    print("\n📒 Jane - February:")
    print(json.dumps(verify_ledger_transaction("Jane Wambui", month="February"), indent=2))


def test_dispute_scenarios():
    """Simulate real dispute scenarios."""
    separator("TEST 5: Real Dispute Scenarios")

    # Scenario 1: "Jane hajalipa mwezi tatu. Suspend?"
    print("\n⚖️ SCENARIO 1: Should Jane be suspended?")
    jane_status = get_member_financial_status("Jane Wambui")
    suspension_rule = search_bylaws("missed contributions suspend")
    print(f"   Missed payments: {jane_status['missed_payments']}")
    print(f"   Bylaw: {suspension_rule}")
    print(f"   Verdict: {'SUSPEND' if jane_status['missed_payments'] >= 3 else 'NOT YET - only ' + str(jane_status['missed_payments']) + ' missed'}")

    # Scenario 2: "Mary wants another loan of 10k"
    print("\n⚖️ SCENARIO 2: Can Mary get a new loan?")
    mary_loan = calculate_loan_eligibility("Mary Akinyi")
    print(f"   Eligible: {mary_loan['eligible']}")
    print(f"   Reason: {mary_loan['reason']}")
    print(f"   Bylaw: {mary_loan['bylaw_reference']}")

    # Scenario 3: Verify disputed payment
    print("\n⚖️ SCENARIO 3: Did Jane pay January contribution?")
    jan_txn = verify_ledger_transaction("Jane Wambui", month="January", transaction_type="Contribution")
    print(f"   Transactions found: {jan_txn['total_matching_transactions']}")
    if jan_txn['transactions']:
        for t in jan_txn['transactions']:
            print(f"   ✅ {t['date']}: {t['amount']} ({t['type']})")


# ─────────────────────────────────────────────────────────────────────────────
# Vertex AI Remote Agent Test (uncomment after deployment)
# ─────────────────────────────────────────────────────────────────────────────

REMOTE_TEST_CASES = [
    "Jane hajalipa contribution mwezi mbili. Anatakiwa suspend?",
    "Huyu mse Mary anataka loan ya 10k. Anastahili?",
    "Can I access emergency fund for hospital bill? Need documents?",
    "Nina late fees ngapi kama nimelipa siku 15 late?",
]


def test_remote_agent(agent_resource_name: str):
    """Test deployed Vertex AI agent with sample disputes."""
    from vertexai.preview import reasoning_engines

    agent = reasoning_engines.ReasoningEngine(agent_resource_name)

    for i, dispute in enumerate(REMOTE_TEST_CASES, 1):
        separator(f"REMOTE TEST {i}")
        print(f"📝 Dispute: {dispute}")
        response = agent.query(input=dispute)
        print(f"\n🤖 Response:\n{response['output']}")
        print(f"\n🔧 Tools called: {[s[0].tool for s in response.get('intermediate_steps', [])]}")


if __name__ == "__main__":
    print("🏛️  MAMA BIDII CHAMA - Dispute Arbitrator Tool Tests")
    print("=" * 60)

    test_search_bylaws()
    test_member_status()
    test_loan_eligibility()
    test_verify_ledger()
    test_dispute_scenarios()

    print(f"\n{'='*60}")
    print("✅ All local tests complete!")
    print("=" * 60)

    # Uncomment after deploying to Vertex AI:
    # test_remote_agent("projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_ID")
