# 📜 Bulk Certificate Generator API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/pytest-16%20Passed-brightgreen.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An asynchronous backend API and processing engine built with **Python**, **FastAPI**, and **SQLAlchemy** that accepts bulk certificate generation requests for lists of recipients, generates high-resolution verified certificates, isolates errors, tracks real-time generation progress, and allows individual or zipped batch retrieval.

---

## 🎯 Key Objectives & Capabilities

- **Bulk Generation:** Accepts hundreds or thousands of recipients in a single API call without client timeouts.
- **Asynchronous Background Processing:** Uses decoupled background task execution; returns `202 Accepted` immediately with a `job_id` and tracking URL.
- **Fault Isolation & Partial Completion:** An invalid email, empty name, or processing error for one recipient **does not** abort the batch. Valid certificates continue generating, and the job status reflects `PARTIALLY_COMPLETED` with detailed error traces per recipient.
- **Predefined High-Resolution Template:** Generates 300 DPI executive-grade certificates with ornate borders, gold seals, customizable fonts, and signatures.
- **Dual Format Output:** Simultaneously exports print-ready **PDF** documents and web-optimized **PNG** images.
- **Cryptographic & QR Code Verification:** Every certificate embeds a unique certificate code and a scannable **QR code** pointing to a public verification endpoint (`/api/v1/certificates/verify/{code}`).
- **Batch ZIP Downloads:** One-click download of all successful certificates in a job bundled into a single ZIP archive.
- **Interactive Studio UI:** A dashboard running at `http://127.0.0.1:8000/` for interactive testing, live progress bar polling, preview modals, and certificate verification.
- **Interactive API Documentation:** Full OpenAPI Swagger (`/docs`) and ReDoc (`/redoc`) specifications.

---

## 🏗️ Architecture & System Design

```
                     ┌──────────────────────────────────────────────┐
                     │            Client / Web Dashboard            │
                     └───────┬──────────────────────────────▲───────┘
                             │ POST /api/v1/jobs            │ GET /jobs/{id}
                             │ (Bulk recipient payload)     │ (Polling progress)
                             ▼                              │
                     ┌──────────────────────────────────────────────┐
                     │           FastAPI Ingestion Layer            │
                     │  - Pydantic schema validation                │
                     │  - Creates CertificateJob (Status: PENDING)  │
                     │  - Pre-creates CertificateRecords            │
                     │  - Enqueues Background Task                  │
                     │  - Returns 202 Accepted                      │
                     └───────┬──────────────────────────────────────┘
                             │ Dispatches job_id
                             ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                   Asynchronous Background Worker                       │
 │                                                                        │
 │   For each recipient in job:                                           │
 │   ┌───────────────────────────────┐   Valid    ┌───────────────────┐   │
 │   │ Recipient Validation Layer    ├───────────►│ Certificate Engine│   │
 │   │ (Checks name & email regex)   │            │ (Pillow 300 DPI   │   │
 │   └──────────────┬────────────────┘            │  QR Code, PNG+PDF)│   │
 │                  │ Invalid                     └─────────┬─────────┘   │
 │                  ▼                                       ▼             │
 │   ┌───────────────────────────────┐            ┌───────────────────┐   │
 │   │ Status: FAILED                │            │ Status: SUCCESS   │   │
 │   │ (Records exact error_message) │            │ (Saves file paths)│   │
 │   └───────────────────────────────┘            └───────────────────┘   │
 │                                                                        │
 │   Aggregate Status: COMPLETED | PARTIALLY_COMPLETED | FAILED           │
 └──────────────────────────────────┬─────────────────────────────────────┘
                                    │ Updates DB & creates archives
                                    ▼
                     ┌──────────────────────────────┐
                     │     Relational Database      │
                     │  (SQLite / PostgreSQL via    │
                     │   SQLAlchemy 2.0 ORM)        │
                     └──────────────────────────────┘
```

---

## 📁 Project Structure

```
Bulk Certificate Generator/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration & environment settings
│   ├── database.py               # SQLAlchemy engine, session maker, get_db dependency
│   ├── main.py                   # FastAPI application entrypoint, CORS, lifespan
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py              # JobStatus and CertificateStatus enumerations
│   │   └── job.py                # CertificateJob and CertificateRecord relational models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── recipient.py          # RecipientInput validation schemas
│   │   ├── job.py                # JobCreateRequest and JobDetailResponse schemas
│   │   └── certificate.py        # CertificateItemResponse and Verification schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generator.py          # Certificate template engine (Pillow 300 DPI, QR, PDF)
│   │   ├── job_service.py        # Background task processor & fault isolation logic
│   │   └── archive_service.py    # ZIP packaging service for bulk downloads
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py               # Shared API dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py         # Consolidated API v1 router
│   │       ├── jobs.py           # /jobs endpoints (create, status, list, zip download)
│   │       └── certificates.py   # /certificates endpoints (download, verification)
│   └── static/
│       ├── index.html            # Certificate Studio Dashboard interface
│       ├── style.css             # Modern dark-mode UI styling
│       └── app.js                # Frontend client logic & live polling
├── storage/                      # Local file storage for generated assets
│   ├── certificates/             # Generated PDF and PNG files
│   └── archives/                 # Generated bulk ZIP bundles
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures, test client, and isolated test DB
│   ├── test_generator.py         # Certificate rendering, auto-scaling, and PDF tests
│   ├── test_validation.py        # Pydantic schema and input validation tests
│   ├── test_jobs_api.py          # Job creation, polling, and listing tests
│   ├── test_fault_isolation.py   # Fault isolation & partial completion tests
│   └── test_retrieval_and_verification.py # PDF/PNG download, ZIP download & QR verification
├── run.py                        # Convenience script to start the local server
├── requirements.txt              # Pinned Python package dependencies
├── .gitignore                    # Git ignore file
└── README.md                     # Comprehensive project documentation
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.11.5)
- Git

### 1. Clone or Navigate to the Repository
```bash
git clone <repository_url>
cd "Bulk Certificate Generator"
```

### 2. Create and Activate a Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell / Command Prompt):
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Start the local server using the startup script:
```bash
python run.py
```
Or directly with `uvicorn`:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
- **Interactive Studio UI:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Reference:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Running the Test Suite

The test suite thoroughly covers all requirements: job creation, schema validation, image/PDF rendering, status polling, fault isolation, individual downloads, bulk ZIP archives, and verification.

Execute all tests with `pytest`:
```bash
python -m pytest -v
```

### Test Coverage Summary:
- `tests/test_validation.py`: Tests empty names, bad email regex, malformed dates, empty lists, and 422 HTTP responses.
- `tests/test_generator.py`: Verifies Pillow template rendering, 2000x1414 resolution, PDF file creation, and long name auto-scaling.
- `tests/test_jobs_api.py`: Verifies job creation (`202 Accepted`), status polling, and job listing.
- `tests/test_fault_isolation.py`: Verifies that invalid recipients fail individually with specific error messages while valid recipients in the same batch succeed (`PARTIALLY_COMPLETED`).
- `tests/test_retrieval_and_verification.py`: Verifies PDF and PNG downloads, ZIP archive creation, and certificate authenticity verification.

---

## 📡 API Reference & Usage Examples

### 1. Submit a Certificate Generation Job
- **Endpoint:** `POST /api/v1/jobs`
- **Status Code:** `202 Accepted`

#### Request Body
```json
{
  "title": "Certificate of Excellence",
  "event_name": "Autonomous Drone Systems & Computer Vision",
  "issuer_name": "AEREO Academy",
  "issue_date": "2026-10-12",
  "recipients": [
    {
      "name": "Jane Doe",
      "email": "jane.doe@example.com"
    },
    {
      "name": "John Smith",
      "email": "john.smith@example.com"
    },
    {
      "name": "   ",
      "email": "invalid@example.com"
    }
  ]
}
```

#### Response (`202 Accepted`)
```json
{
  "job_id": "d858e121-345a-44d8-96e2-f8604d5880c7",
  "status": "PENDING",
  "title": "Certificate of Excellence",
  "event_name": "Autonomous Drone Systems & Computer Vision",
  "issuer_name": "AEREO Academy",
  "issue_date": "2026-10-12",
  "total_count": 3,
  "processed_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "progress_percentage": 0.0,
  "status_url": "/api/v1/jobs/d858e121-345a-44d8-96e2-f8604d5880c7",
  "created_at": "2026-10-12T12:16:26.388941",
  "updated_at": "2026-10-12T12:16:26.388941",
  "completed_at": null,
  "message": "Job is currently PENDING. Processed 0/3 recipients."
}
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Certificate of Excellence",
       "event_name": "Autonomous Drone Systems",
       "issuer_name": "AEREO Academy",
       "recipients": [
         {"name": "Alice Johnson", "email": "alice@example.com"},
         {"name": "Bob Smith", "email": "bob@example.com"}
       ]
     }'
```

---

### 2. Poll Job Status and Progress
- **Endpoint:** `GET /api/v1/jobs/{job_id}`
- **Status Code:** `200 OK`

#### Response (`200 OK`)
```json
{
  "job_id": "d858e121-345a-44d8-96e2-f8604d5880c7",
  "status": "PARTIALLY_COMPLETED",
  "title": "Certificate of Excellence",
  "event_name": "Autonomous Drone Systems & Computer Vision",
  "issuer_name": "AEREO Academy",
  "issue_date": "2026-10-12",
  "total_count": 3,
  "processed_count": 3,
  "success_count": 2,
  "failure_count": 1,
  "progress_percentage": 100.0,
  "status_url": "/api/v1/jobs/d858e121-345a-44d8-96e2-f8604d5880c7",
  "zip_download_url": "/api/v1/jobs/d858e121-345a-44d8-96e2-f8604d5880c7/download-zip",
  "certificates": [
    {
      "id": "2e071720-eb41-450e-b9b9-6231d604b931",
      "recipient_name": "Jane Doe",
      "recipient_email": "jane.doe@example.com",
      "certificate_code": "AEREO-2026-F4457C95",
      "status": "SUCCESS",
      "download_pdf_url": "/api/v1/certificates/2e071720-eb41-450e-b9b9-6231d604b931/download?format=pdf",
      "download_png_url": "/api/v1/certificates/2e071720-eb41-450e-b9b9-6231d604b931/download?format=png",
      "error_message": null,
      "created_at": "2026-10-12T12:16:26.398000",
      "generated_at": "2026-10-12T12:16:27.123000"
    },
    {
      "id": "e890c213-39d2-45e8-b0a1-43849f2910fa",
      "recipient_name": "",
      "recipient_email": "invalid@example.com",
      "certificate_code": "AEREO-2026-6D3E1A04",
      "status": "FAILED",
      "download_pdf_url": null,
      "download_png_url": null,
      "error_message": "Recipient name cannot be empty or only whitespace.",
      "created_at": "2026-10-12T12:16:26.399000",
      "generated_at": null
    }
  ]
}
```

---

### 3. Retrieve Individual Certificate
- **Endpoint:** `GET /api/v1/certificates/{cert_id}/download?format=pdf` (or `format=png`)
- **Content-Type:** `application/pdf` or `image/png`

#### cURL Example
```bash
# Download PDF
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/{cert_id}/download?format=pdf"

# Download PNG
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/{cert_id}/download?format=png"
```

---

### 4. Bulk Download All Certificates as ZIP
- **Endpoint:** `GET /api/v1/jobs/{job_id}/download-zip?format=pdf` (supports `pdf`, `png`, or `both`)
- **Content-Type:** `application/zip`

#### cURL Example
```bash
curl -O -J "http://127.0.0.1:8000/api/v1/jobs/{job_id}/download-zip?format=pdf"
```

---

### 5. Verify Authenticity of a Certificate
- **Endpoint:** `GET /api/v1/certificates/verify/{certificate_code}`
- **Description:** Encoded in the QR code of every certificate for instant verification.

#### Response (`200 OK`)
```json
{
  "is_valid": true,
  "certificate_code": "AEREO-2026-F4457C95",
  "recipient_name": "Jane Doe",
  "event_name": "Autonomous Drone Systems & Computer Vision",
  "issuer_name": "AEREO Academy",
  "issue_date": "2026-10-12",
  "issued_at": "2026-10-12T12:16:27.123000",
  "download_url": "http://localhost:8000/api/v1/certificates/2e071720-eb41-450e-b9b9-6231d604b931/download?format=pdf",
  "message": "Certificate is authentic and verified."
}
```

---

## 💡 Important Design Decisions & Trade-Offs

### 1. Framework Selection: Why FastAPI?
- **Asynchronous Native Performance:** Built upon Starlette and ASGI, FastAPI handles asynchronous I/O and concurrent requests with minimal overhead.
- **BackgroundTasks Support:** Provides decoupled background worker capabilities out-of-the-box without requiring an external queue broker (like Celery/RabbitMQ) for standard single-instance deployments, while easily decoupling to Celery/Redis for multi-node deployments.
- **Automatic OpenAPI Documentation:** Automatically generates live Swagger UI (`/docs`) and ReDoc specifications from Pydantic schemas.
- **Strict Data Validation:** Deep type safety via Pydantic v2 ensures robust schema parsing, email regex validation, and sanitization before hitting database layers.

### 2. Processing Strategy: Synchronous vs. Asynchronous
- **Decision:** Asynchronous background processing returning `HTTP 202 Accepted`.
- **Reasoning:** In bulk scenarios with 100 to 5,000 certificates, rendering high-resolution 300 DPI graphics takes 100ms–200ms per certificate. A synchronous request would take 20–100 seconds, violating HTTP gateway timeout limits (typically 30s) and freezing the client connection. Decoupling ingestion from generation guarantees sub-100ms API response times.

### 3. Fault Isolation Strategy
- **Decision:** Per-recipient try-catch isolation inside the worker loop.
- **Reasoning:** If 1 recipient out of 1,000 has corrupted data or triggers an unexpected exception, terminating the entire batch is unacceptable.
- **Implementation:** Each recipient is processed in an independent exception boundary. If validation or generation fails:
  - The recipient is flagged as `FAILED` with the exact error cause saved to `error_message`.
  - The job increments `failure_count`.
  - The remaining recipients continue processing.
  - The overall job status transitions to `PARTIALLY_COMPLETED` (or `COMPLETED` if all succeed, or `FAILED` if all fail).

### 4. Certificate Generation Library: Why Pillow?
- **Print-Quality Output:** Renders 2000x1414 pixel canvases at 300 DPI with geometric vector borders, typography auto-scaling, gold seals, and dynamic QR codes.
- **Dual Export:** Seamlessly exports both `.png` (for instant web/mobile preview) and print-ready `.pdf` documents directly from the bitmap without requiring external binaries like `wkhtmltopdf` or heavy headless browsers.
- **Cross-Platform Fonts:** Implements a robust font fallback chain that looks for standard serif/sans fonts (`Georgia`, `Arial`, `Times`) with graceful fallback to PIL's built-in fonts if executed in minimal Linux containers.

### 5. Relational Database & Thread Safety
- **Normalized Schema:** Separates `CertificateJob` (batch-level metadata, total count, success/failure metrics) from `CertificateRecord` (recipient data, generated certificate code, status, error trace, and file paths).
- **Thread Safety:** The background worker creates an isolated session via `SessionLocal()`, ensuring proper lifecycle management, transaction scoping, and safe execution across threads.

---

## 📈 Scalability & Production Readiness (Interview Talking Points)

During an interview discussion on how to scale this system to 100,000+ certificates/day:
1. **Distributed Task Queue:** Replace FastAPI's in-process `BackgroundTasks` with **Celery / ARQ / Celery with Redis or RabbitMQ**. Workers can be scaled horizontally across multiple machines.
2. **Cloud Object Storage:** Replace local disk storage (`storage/certificates`) with **Amazon S3, Cloudflare R2, or Google Cloud Storage**. Store signed pre-signed URLs in `file_path_pdf` and `file_path_png`.
3. **Database Migration:** Switch `DATABASE_URL` from SQLite to **PostgreSQL** using SQLAlchemy connection pooling (`QueuePool`).
4. **Batch Generation Optimization:** Implement parallel thread pooling (`concurrent.futures.ProcessPoolExecutor`) inside each worker to utilize all multi-core CPU threads when rendering certificates.
5. **Webhook Notifications:** Add an optional `webhook_url` parameter to `JobCreateRequest` to ping the client system once the bulk job finishes processing.

---

## 🧑‍💻 Author & Assessment Submission

- **Role:** Software Development Intern (Super Dream) — AEREO
- **Language:** Python 3.11
- **Framework:** FastAPI, SQLAlchemy 2.0, Pillow, Pydantic v2
