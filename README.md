# Aegis Triage OS: Enterprise Clinical AI Intelligence

Aegis Triage OS is a production-hardened, multi-modal AI engine designed for clinical triaging, psychometric assessment, and geospatial epidemic monitoring. Built for enterprise-grade healthcare deployments.

## 🚀 Key Enterprise Features

- **Clinical AI Orchestration**: Multi-modal LangGraph execution pipeline with Gemini 1.5 Pro/Flash failover logic.
- **Geospatial Outbreak Intelligence**: Unsupervised epidemic clustering using HDBSCAN with Haversine geospatial calculations.
- **Enterprise Security**: 
    - JWT-based Authentication & Role-Based Access Control (RBAC).
    - PII Redaction Privacy Vault (Microsoft Presidio + Regex Fallback).
    - Cryptographic Webhook Verification (HMAC-SHA256).
- **Resilience & Observability**:
    - Circuit Breaker & Exponential Backoff Retry patterns for external AI services.
    - Structured logging with Request-ID tracing and latency monitoring.
    - PII Leakage Prevention Middleware as a final safety rail.
- **Clinical Data Governance**: DPDP-compliant consent logging and medical data encryption (Fernet).

## 🛠️ Tech Stack

- **Framework**: FastAPI (Async Performance)
- **AI/LLM**: Google GenAI (Gemini 1.5), LangGraph (Conversational State)
- **Database**: Supabase / PostgreSQL (Geospatial Indexing)
- **NLP/PII**: Microsoft Presidio, SpaCy (`en_core_web_lg`)
- **Reporting**: ReportLab (Asynchronous EHR PDF Generation)
- **Spatial**: Scikit-learn (HDBSCAN)

## 📦 Deployment

### Local Setup
1. Clone the repository.
2. Create a `.env` file based on `.env.example`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `uvicorn main:app --reload`

### Docker (Recommended)
```bash
docker build -t aegis-triage-os .
docker run -p 8000:8000 --env-file .env aegis-triage-os
```

## 🔐 API Roles & Access

- **PATIENT**: Access to triage and basic health reports.
- **DOCTOR**: Access to priority queues and telemedicine routing.
- **ADMIN**: Full access to geospatial outbreak dashboards and audit logs.

## 📜 Medical Disclaimer
Aegis OS is an AI assistant, not a replacement for professional medical diagnosis. All responses include a mandatory clinical disclaimer header.
