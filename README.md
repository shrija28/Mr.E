# 🚀 SmartKCET Prep / ExamForge AI

A specialized Karnataka Common Entrance Test (**KCET**) preparation platform powered by **Retrieval-Augmented Generation (RAG)**, **Groq LLMs**, **FAISS Vector Search**, **Flask**, and **React 18+**. SmartKCET filters question banks according to standard KCET patterns and extracts official **60-question paper sets** with instant evaluation, institutional management, and student subscription controls.

---

## 🌟 Key Features

* 🎯 **KCET 60-Question Paper Extraction**: Filters question banks to extract standard KCET-compliant MCQs, assembling official **60-question / 60-mark / 80-minute paper sets** (Sets A, B, C, D).
* 📄 **Vision OCR & Multimodal Parsing**: Handles complex diagrams, printed textbook pages, and past KCET papers using **PyMuPDF** & **Groq Vision OCR (`llama-3.2-90b-vision-preview`)**.

* 🛡️ **Role-Based Access Control (RBAC)**: Role-specific portals (Admin, Student, Institution Manager) secured with **Flask-JWT-Extended** and **Bcrypt hashing**.
* 💳 **Subscription & Access Control**: Tiered plans (Free Trial, Individual, Institutional) with access control gates and **Razorpay** payment gateway integration.
* 🏫 **Institution & Student Management**: Supports bulk student creation, institution codes, trial tracking, and student association.
* 📊 **Performance Analytics & Leaderboards**: Real-time evaluation, subject-wise accuracy tracking, attempt history, and percentile rank leaderboards.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Backend Core** | Python 3.10+, Flask 3.x, Flask Blueprints, Flask-CORS, Gunicorn/Waitress |
| **Database & ORM** | SQLite (`smartkcet.db`), PostgreSQL support, Flask-SQLAlchemy, Flask-Migrate (Alembic) |

| **AI / RAG / ML** | Groq API (`groq`), FAISS (`faiss-cpu`), Sentence-Transformers, PyTorch, PyMuPDF |
| **Vision & Image** | OpenCV (`cv2`), Pillow (`PIL`), PyMuPDF (`fitz`) |
| **Security** | PyJWT (JWT Tokens), Bcrypt (Password Hashing) |
| **Payments** | Razorpay SDK |
| **Frontend** | React 18+, Vite, TypeScript/JavaScript, React Router v6, Tailwind CSS, Recharts |

---

## 📁 Directory Structure

```text
SmartKCET-Prep/
├── backend/
│   ├── app.py                      # Application execution entry point
│   ├── requirements.txt            # Python dependencies
│   ├── smartkcet/
│   │   ├── main.py                 # FastAPI application factory & router mounts
│   │   ├── config.py               # Startup environment & config validator
│   │   ├── admin/                  # Admin portal APIs (dashboard, students, institutions, exams)
│   │   ├── auth/                   # Authentication (login, register, JWT, password hashing)
│   │   ├── student/                # Student portal APIs (dashboard, exams, attempts, leaderboard)
│   │   ├── subscription/           # Subscriptions, access control, plans & Razorpay wiring
│   │   ├── institution/            # Institution student management & content APIs
│   │   ├── rag/                    # RAG pipeline (parsing.py, groq_client.py, store.py, mcq_extractor.py)
│   │   └── db/                     # SQLAlchemy models, database session, seed scripts
│   └── tests/                      # Automated test suite (pytest)
├── frontend/
│   ├── html/                       # HTML pages (index, exam, dashboard, admin, institution)
│   ├── js/                         # Frontend JS logic & REST API clients
│   └── css/                        # CSS stylesheets
├── docs/                           # Setup & architectural documentation
├── QUICK_START.md                  # Quick testing guide
├── PROJECT_RUNNING.md              # Live status and verification guide
└── README.md                       # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** installed.
- **Groq API Key** (for AI question generation features).

### 2. Environment Setup
Set your `GROQ_API_KEY` in your environment or inside `backend/.env`:
```bash
# Windows PowerShell
$env:GROQ_API_KEY="your_groq_api_key_here"

# Linux / macOS
export GROQ_API_KEY="your_groq_api_key_here"
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the Backend Server
```bash
python app.py
```
*The server automatically initializes database schema self-healing, seeds admin credentials, subscription plans, and test institutions on first start.*

---

## 🌐 Quick Access URLs

| Feature | URL |
| :--- | :--- |
| **Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
| **Admin Dashboard** | [http://127.0.0.1:8000/admin/dashboard](http://127.0.0.1:8000/admin/dashboard) |
| **Interactive API Docs (Swagger)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| **ReDoc Specification** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |

### Default Admin Credentials
- **Email:** `admin@smartkcet.com`
- **Password:** Defined in `backend/.env` or generated during initial seeding

---

## 🔑 Key API Endpoints

### 🔐 Auth Routes (`/api/auth`)
* `POST /api/auth/login` — User authentication & JWT issuance
* `POST /api/auth/register` — Student account registration
* `POST /api/auth/refresh` — Refresh access token

### ⚙️ Admin Routes (`/api/admin`)
* `GET /api/admin/platform/students` — Manage registered students
* `GET /api/admin/platform/institutions` — List & manage institutions
* `POST /api/admin/exams/generate-textbook` — Trigger RAG-powered MCQ generation from textbook PDFs

### 🎓 Student Routes (`/api/student`)
* `GET /api/student/dashboard` — Fetch student analytics & recent exam attempts
* `POST /api/student/exams/{id}/submit` — Submit exam responses for automatic scoring
* `GET /api/student/leaderboard` — View platform rank leaderboard

### 💳 Subscription Routes (`/api/subscription`)
* `GET /api/subscription/plans` — View active subscription plans
* `POST /api/subscription/subscribe` — Initiate subscription plan purchase
* `GET /api/subscription/status` — Check active subscription & trial period status

---

## 🧪 Testing

To run the backend test suite:
```bash
cd backend
pytest
```



