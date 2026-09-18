# 🚀 VyasaPrep — KCET Preparation & Question Paper Platform

A comprehensive competitive exam preparation platform for the Karnataka Common Entrance Test (**KCET**) powered by **Flask / React**, **Retrieval-Augmented Generation (RAG)**, **Groq LLMs**, **FAISS Vector Search**, and **SQLite**. VyasaPrep enables automated entrance-level MCQ paper generation from textbook PDFs, instant exam evaluation, institutional management, performance analytics, and tiered student subscriptions.

---

## 🌟 Features & Architecture

* 🎯 **AI & RAG Question Generation**: Generates competitive entrance exam MCQs directly from textbook PDFs using **Groq LLM (`llama-3.3-70b-versatile`)** combined with **FAISS vector search** for context retrieval.
* 📄 **Vision OCR & Multimodal Parsing**: Parses textbook PDFs and complex diagrams using **PyMuPDF (`fitz`)** & **Groq Vision OCR (`llama-3.2-90b-vision-preview`)**.
* 🛡️ **Role-Based Access Control (RBAC)**: Role-scoped endpoints (Admin, Student, Institution Manager) secured with **PyJWT** tokens and **Bcrypt** password hashing.
* 💳 **Subscription & Access Control**: Tiered subscription plans (Free Trial, Individual, Institutional) with access control gates and lifecycle expiration scheduling.
* 🏫 **Institution & Cohort Management**: Supports bulk student enrollment, institution codes (e.g. `KCET_AC_001`), and institutional dashboard analytics.
* 📊 **Performance Analytics & Leaderboards**: Real-time evaluation, subject-wise accuracy tracking, attempt history, and percentile rank leaderboards.

---

## 🛠️ Technology Stack (Actual Codebase)

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.10+ / FastAPI** | High-performance ASGI framework with Pydantic v2 validation |
| **Server** | **Uvicorn** | ASGI server running the FastAPI app on port `8000` |
| **Database & ORM** | **SQLite (`smartkcet.db`)** | SQLAlchemy 2.0 ORM with self-healing schema migrations & Alembic |
| **AI / RAG Pipeline** | **Groq API / FAISS / PyMuPDF** | Vector similarity search (`faiss-cpu`), sentence embeddings, and Groq LLMs |
| **Security** | **PyJWT & Bcrypt** | Bearer JWT authentication & salted password hashing |
| **Payments** | **Razorpay SDK** | Payment gateway integration for subscription plans |
| **Frontend** | **HTML5, CSS3, JavaScript (ES6)** | Served directly by FastAPI at `/html/*`, `/js/*`, `/css/*` |

---

## 📁 Repository Structure

```text
SmartKCET-Prep/
├── backend/
│   ├── app.py                      # Server entry point (starts Uvicorn on 127.0.0.1:8000)
│   ├── requirements.txt            # Python dependencies
│   ├── smartkcet.db                # SQLite database
│   ├── smartkcet/                  # Main Python package
│   │   ├── main.py                 # FastAPI application factory & router mounts
│   │   ├── config.py               # Startup environment & config validation
│   │   ├── admin/                  # Admin endpoints (dashboard, students, institutions, exams)
│   │   ├── auth/                   # Authentication (login, register, JWT, passwords)
│   │   ├── student/                # Student endpoints (dashboard, exams, attempts, leaderboard)
│   │   ├── subscription/           # Subscriptions, access control gates, scheduler
│   │   ├── institution/            # Institution cohort management & content APIs
│   │   ├── rag/                    # RAG pipeline (parsing.py, groq_client.py, store.py, mcq_extractor.py)
│   │   └── db/                     # SQLAlchemy models, sessions, seed scripts
│   └── tests/                      # Automated test suite (pytest)
├── frontend/
│   ├── html/                       # HTML view templates (index, exam, dashboards)
│   ├── js/                         # Client-side JavaScript & API integration
│   └── css/                        # Stylesheets
├── docs/                           # Documentation
├── QUICK_START.md                  # Quick testing reference guide
└── README.md                       # Project overview and setup instructions
```

---

## 🚀 Quick Start & How to Run

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- **Groq API Key** (Set as environment variable `GROQ_API_KEY`).

### 2. Set Up Environment Variables
Set your `GROQ_API_KEY` in your environment or inside `backend/.env`:
```bash
# Windows PowerShell
$env:GROQ_API_KEY="your_groq_api_key_here"

# Linux / macOS
export GROQ_API_KEY="your_groq_api_key_here"
```

### 3. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Start the Server
Run the backend entry point:
```bash
python app.py
```
*Or run via Uvicorn directly:*
```bash
python -m uvicorn smartkcet.main:app --reload --host 127.0.0.1 --port 8000
```
On startup, the server automatically runs database self-healing, seeds admin credentials, subscription plans, and test institutions.

---

## 🌐 Application URLs

| Feature / Page | URL |
| :--- | :--- |
| **Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
| **Admin Dashboard** | [http://127.0.0.1:8000/admin/dashboard](http://127.0.0.1:8000/admin/dashboard) |
| **API Documentation (Swagger UI)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| **ReDoc Specification** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |

### Default Admin Credentials
- **Email:** `admin@smartkcet.com`
- **Password:** Defined in `backend/.env` or generated during initial startup seeding.

---

## 🔑 Primary REST API Routes

### 🔐 Authentication (`/api/auth`)
- `POST /api/auth/login` — Authenticate user & issue JWT bearer token
- `POST /api/auth/register` — Student account registration
- `POST /api/auth/refresh` — Refresh expired JWT access token

### ⚙️ Admin Platform (`/api/admin`)
- `GET /api/admin/platform/students` — List & manage registered students
- `GET /api/admin/platform/institutions` — Manage institutions & cohorts
- `POST /api/admin/exams/generate-textbook` — Trigger RAG-based MCQ paper generation

### 🎓 Student Portal (`/api/student`)
- `GET /api/student/dashboard` — Fetch student test history & analytics
- `POST /api/student/exams/{id}/submit` — Submit exam answers for instant scoring
- `GET /api/student/leaderboard` — View rank leaderboard

### 💳 Subscription (`/api/subscription`)
- `GET /api/subscription/plans` — Fetch active pricing plans
- `POST /api/subscription/subscribe` — Initiate subscription purchase
- `GET /api/subscription/status` — Check active subscription & trial status

---

## 🧪 Running Tests

To run the backend automated test suite:
```bash
cd backend
pytest
```
