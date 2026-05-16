"""
Chama Dispute Arbitrator - Vertex AI Agent Configuration
"""

from google.cloud import aiplatform
from vertexai.preview import reasoning_engines
from agent_tools import (
    search_bylaws, get_member_financial_status,
    calculate_loan_eligibility, verify_ledger_transaction,
)

PROJECT_ID = "your-project-id"  # TODO: Replace with your GCP project ID
LOCATION = "us-central1"

AGENT_SYSTEM_PROMPT = """
Wewe ni Msuluhishi wa Migogoro ya Chama (Chama Dispute Arbitrator) wa Mama Bidii Chama.

ROLE: Elite, unbiased legal and financial arbitrator for Kenyan chamas.
You use: 1) Bylaws (cite ARTICLE & Section), 2) M-Pesa records, 3) Fair reasoning.

LANGUAGE: Accept Swahili, Sheng, English. Respond in user's dominant language.
Sheng: "mse"=member, "doh"=money, "kulipa"=pay, "frao"=fraud

PROTOCOL:
Step 1: ANALYZE - Identify core grievance
Step 2: VERIFY - Use verify_ledger_transaction / get_member_financial_status
Step 3: CROSS-REFERENCE - Use search_bylaws for applicable rule
Step 4: VERDICT - Cite bylaw section, state financial correction in KES

RULES:
- ALWAYS cite specific bylaw articles
- NEVER fabricate financial figures
- If ledger contradicts claim, present timestamped proof
- Be fair to BOTH parties
- If bylaws don't cover scenario, say so explicitly

RESPONSE FORMAT:
📋 MUHTASARI (Summary) | 📜 SHERIA (Bylaws) | 📊 USHAHIDI (Evidence) | ⚖️ UAMUZI (Verdict) | 💡 MAPENDEKEZO (Next steps)
"""


def create_agent():
    """Create and deploy Vertex AI Agent."""
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    agent = reasoning_engines.LangchainAgent(
        model="gemini-2.0-flash",
        tools=[search_bylaws, get_member_financial_status,
               calculate_loan_eligibility, verify_ledger_transaction],
        model_kwargs={"temperature": 0.1, "system_instruction": AGENT_SYSTEM_PROMPT},
    )

    remote_agent = reasoning_engines.ReasoningEngine.create(
        agent,
        requirements=["google-cloud-aiplatform[reasoningengine,langchain]"],
        display_name="Mama Bidii Chama Dispute Arbitrator",
    )

    print(f"Agent deployed! Resource: {remote_agent.resource_name}")
    return remote_agent.resource_name


if __name__ == "__main__":
    create_agent()
