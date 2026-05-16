# 🏛️ Mama Bidii Chama Dispute Arbitrator

**AI-powered arbitration for Kenyan chama (savings group) disputes.**

Built for the LP Hackathon 2026 — an intelligent agent that resolves financial disputes using chama bylaws and M-Pesa transaction records.

## 🚀 What It Does

- **Resolves disputes** between chama members and the executive committee
- **Verifies financial claims** against timestamped M-Pesa ledger records
- **Cites specific bylaws** (Article & Section) for every ruling
- **Supports Swahili, Sheng & English** — responds in the user's language

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User      │────▶│  Cloud Run API   │────▶│  Agent Tools    │
│  (Dispute)  │◀────│  /chat endpoint  │◀────│  - search_bylaws│
└─────────────┘     └──────────────────┘     │  - member_status│
                                              │  - loan_check   │
                                              │  - verify_ledger│
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │     Data Layer   │
                                              │  - bylaws.txt    │
                                              │  - mpesa.csv     │
                                              │  - members.json  │
                                              └─────────────────┘
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/health` | GET | Health check |
| `/chat` | POST | Submit dispute for arbitration |
| `/members` | GET | List all chama members |
| `/member/<name>` | GET | Get member financial status |
| `/loan-check/<name>` | GET | Check loan eligibility |

## 💬 Example Usage

```bash
# Health check
curl https://YOUR_CLOUD_RUN_URL/health

# Submit a dispute
curl -X POST https://YOUR_CLOUD_RUN_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Jane hajalipa mwezi mbili, anatakiwa suspend?", "member_name": "Jane Wambui"}'

# Check loan eligibility
curl https://YOUR_CLOUD_RUN_URL/loan-check/Mary%20Akinyi
```

## 🛠️ Agent Tools

| Tool | Function | Data Source |
|------|----------|-------------|
| `search_bylaws` | Search chama constitution | `data/chama_bylaws.txt` |
| `get_member_financial_status` | Full member financial lookup | `data/members.json` + `data/mpesa_records.csv` |
| `calculate_loan_eligibility` | Loan qualification check | Bylaws Art. 2 + member data |
| `verify_ledger_transaction` | Fact-check M-Pesa transactions | `data/mpesa_records.csv` |

## 📜 Chama Bylaws Covered

- **Article 1**: Membership & Contributions (KES 2,000/month, late fees, suspension)
- **Article 2**: Loans (eligibility, 3x max, 10% interest, 12-month repayment)
- **Article 3**: Withdrawal (30-day notice, clear loans first)
- **Article 4**: Emergency Fund (medical only, 48hr approval)
- **Article 5**: Dispute Resolution (arbitration, 14-day decision)

## 🚀 Deploy

```bash
# Deploy to Cloud Run
gcloud run deploy chama-arbitrator --source . --region us-central1 --allow-unauthenticated
```

## 👥 Team

Built by **mumbly6** at LP Hackathon 2026.

## 📄 License

MIT
