# 📄 Product Requirements Document (PRD)
## SmartKCET Prep / ExamForge AI — RAG-Powered Entrance Exam Platform

**Document Status:** Approved & Active  
**Version:** 1.2.0  
**Target Audience:** Engineering & Development Team, Product Management, System Architects  
**Product Name:** SmartKCET Prep / ExamForge AI  
**Frontend Framework:** React 18+ Single Page Application (SPA)  
**Backend Framework:** Flask (Python 3.10+) with Flask Blueprints  
**Last Updated:** August 2026  

---

## 1. 🎯 Executive Summary & Problem Statement

### 1.1 Executive Summary
SmartKCET Prep / ExamForge AI is an advanced, AI-driven competitive entrance exam preparation and learning platform. Built specifically for students preparing for the Karnataka Common Entrance Test (KCET) and similar competitive entrance exams (NEET, JEE), the system combines a modern **React 18+ Single Page Application (SPA)** frontend (built with **Vite**, **TypeScript/JavaScript**, **React Router v6**, and **Tailwind CSS**) with a robust **Flask (Python 3.10+)** REST API backend utilizing **Flask Blueprints**, **Flask-SQLAlchemy**, **Retrieval-Augmented Generation (RAG)**, **Groq LLMs**, and **FAISS Vector Search**.

### 1.2 Problem Statement
* **Static & Repeated Question Banks:** Traditional coaching platforms reuse static PDF question papers, leading to rote memorization rather than conceptual problem-solving.
* **Lack of Syllabus Alignment:** Generic AI question generators produce out-of-syllabus questions or trivial definitions rather than multi-step numerical calculation problems required by entrance exams.
* **Vision & Diagram Extraction Gap:** Standard text-only parsers fail to extract questions containing chemical structures, circuit diagrams, and mathematical formulas from printed textbook scans.
* **Monolithic/Laggy UIs:** Legacy server-rendered HTML pages lack fluid state management, instant client-side transitions, and real-time interactive timer/question grids required during online entrance exam practice.

---

## 2. 🚀 Product Vision & Objectives

### 2.1 Product Vision
To empower students and educational institutions with an intelligent entrance exam platform featuring a high-performance **React SPA** frontend and a modular, reliable **Flask + RAG** backend that converts prescribed NCERT/KCET textbooks into dynamic, competitive-level test papers with instant analytics and subscription controls.

### 2.2 Core Business & Technical Objectives
* **Fluid React User Experience:** Deliver an ultra-responsive React SPA (< 100ms client-side page transitions, zero full-page reloads).
* **Modular Flask Backend:** Architecture structured into isolated **Flask Blueprints** (`auth_bp`, `admin_bp`, `student_bp`, `subscription_bp`, `institution_bp`).
* **Automated Paper Generation:** Generate 80-question competitive exam papers across 4 paper sets (Sets A, B, C, D) in under 15 seconds.
* **Strict Difficulty Enforcement:** Ensure at least 60% of Physics/Chemistry MCQs are numerical/calculation-based problems with high-quality distractors.
* **Seamless Access Control:** Enforce JWT role-based access control (RBAC) and subscription gates across direct students and institutionally linked cohorts using **Flask-JWT-Extended** decorators (`@jwt_required()`, `@admin_required`) on backend endpoints and React `ProtectedRoute` components on the client.

---

## 3. 👥 User Personas & Roles

| Persona / Role | Description & Needs | Primary Workflows |
| :--- | :--- | :--- |
| **Student Aspirant** | High school student preparing for KCET/NEET. Needs real-time exam practice, instant scoring, subject breakdown, and leaderboard ranking. | Register account, take timed exams in React Exam Interface, review detailed explanations, view interactive Recharts performance analytics. |
| **Institution Manager** | Director or instructor at a coaching center. Needs to enroll student cohorts, assign institutional licenses, and track student activity. | Access React Institution Portal, link students using custom institution codes (e.g. `KCET_AC_001`). |
| **Platform Admin** | Platform administrator monitoring system health, managing subscription pricing plans, and triggering AI question generation from textbooks. | Access React Admin Portal, monitor student metrics, trigger textbook exam generation, manage plans. |

---

## 4. ⚙️ Functional Requirements (FRs)

### FR-1: React SPA Frontend Architecture
* **FR-1.1 Framework & Build Tool:** Built using **React 18+** bundled with **Vite** for fast HMR development and optimized production builds.
* **FR-1.2 Routing:** Client-side routing implemented using **React Router v6** with nested layouts, lazy-loaded page components, and role-based `ProtectedRoute` wrappers.
* **FR-1.3 Styling & UI:** Styled using **Tailwind CSS** for responsive design, dark/light mode UI components, glassmorphism card layouts, and **Lucide React** icons.
* **FR-1.4 State Management & API Integration:** 
  - Centralized authentication state managed via `AuthContext` and custom `useAuth` hook.
  - HTTP requests handled via **Axios** with global request/response interceptors to automatically attach `Authorization: Bearer <token>` headers and catch `401 Unauthorized` / `403 Forbidden` errors.
  - Interactive charts rendered using **Recharts** / **Chart.js** (React-chartjs-2).

### FR-2: Flask Backend & Blueprint Architecture
* **FR-2.1 Framework Core:** Built with **Flask 3.x** / Python 3.10+ application factory pattern (`create_app()`).
* **FR-2.2 Blueprint Segmentation:**
  - `auth_bp` (`/api/auth`): Registration, login, JWT token refresh.
  - `admin_bp` (`/api/admin`): Platform metrics, student management, institution setup, textbook exam generation.
  - `student_bp` (`/api/student`): Dashboard analytics, exam taking, submission scoring, leaderboard ranks.
  - `subscription_bp` (`/api/subscription`): Plans listing, checkout, subscription status checks.
  - `institution_bp` (`/api/institution`): Bulk student enrollment and license allocation.
* **FR-2.3 Database Layer:** **Flask-SQLAlchemy** (SQLAlchemy 2.0 ORM) with **Flask-Migrate** (Alembic) for schema migrations.
* **FR-2.4 CORS Configuration:** **Flask-CORS** middleware enabling cross-origin requests from the React SPA.

### FR-3: AI & RAG Question Generation Engine
* **FR-3.1 Context Retrieval:** System shall query FAISS vector indices of uploaded textbook PDFs to retrieve relevant topic chunks for Physics, Chemistry, Mathematics, and Biology.
* **FR-3.2 LLM Invocation:** System shall call Groq API (`llama-3.3-70b-versatile`) with explicit exam-setter prompts.
* **FR-3.3 Exam Difficulty Rules:**
  - **No Trivial Definitions:** Questions must be application-based, numerical, or rigorous conceptual deductions.
  - **Numerical Ratio:** At least 60% of Physics questions must require multi-step numerical calculations.
  - **Distractor Quality:** Incorrect options must represent common student calculation/sign errors.
  - **Meta-Text Ban:** Output must be self-contained; no phrases like "In this passage" or "According to chapter".
* **FR-3.4 Output Format:** System must output a clean, validated JSON array of MCQ objects with fields `q`, `opts` (4 options), `ans` (0-based index), `marks`, and `exp` (step-by-step solution).

### FR-4: Multimodal PDF Parsing & Vision OCR
* **FR-4.1 Text Extraction:** System shall use **PyMuPDF (`fitz`)** for native text extraction from textbook PDFs.
* **FR-4.2 Vision OCR Fallback:** For scanned or image-heavy pages, system shall preprocess images with OpenCV/Pillow and invoke **Groq Vision OCR (`llama-3.2-90b-vision-preview`)** via a multi-threaded execution pool.

### FR-5: User Authentication & Role-Based Access Control (RBAC)
* **FR-5.1 JWT Token Management:** Issued using **Flask-JWT-Extended** upon successful authentication (`POST /api/auth/login`).
* **FR-5.2 Password Hashing:** Passwords hashed using **Werkzeug / Bcrypt**.
* **FR-5.3 Route & Endpoint Protection:** Endpoint routes decorated with `@jwt_required()`, `@admin_required`, `@student_required`. React client enforces `<ProtectedRoute />` redirects.

### FR-6: Subscription & Access Control Engine
* **FR-6.1 Plan Types:** Free Trial (14 days), Individual Monthly/Annual, and Institutional Bundle plans.
* **FR-6.2 Pre-Exam Gate:** Before starting an exam (`POST /api/exam/check-access`), Flask decorator verifies subscription status.
* **FR-6.3 Upgrade UI Prompts:** React client shows modal upgrade prompts for restricted actions.

### FR-7: React Exam Engine & Automated Evaluation
* **FR-7.1 Exam Interface Component (`<ExamEngine />`):** Real-time timer hook (`useTimer`), question navigation drawer (`<QuestionGrid />`), option selectors (`<OptionCard />`).
* **FR-7.2 Instant Scoring:** Submission (`POST /api/student/exams/{id}/submit`) calculates score, subject breakdown, and updates database records instantly.

---

## 5. 🛡️ Non-Functional Requirements (NFRs)

* **SPA & API Performance:** React client initial load time `< 1.2s`. Flask REST API endpoints respond in `< 200ms`. RAG MCQ paper generation completes in `< 15s`.
* **Security:** HTTPS/TLS, Flask-JWT-Extended verification, CORS policy restricted to React SPA domain, XSS defense via React JSX auto-escaping, SQL injection prevention via SQLAlchemy ORM.
* **Reliability & WSGI Deployment:** Production deployment via **Gunicorn** / **Waitress** WSGI server with multiple worker processes.
* **Responsiveness:** Fluid layout using Tailwind CSS across Mobile, Tablet, and Desktop screens.

---

## 6. 🏗️ Architecture & Technology Stack

```text
+-----------------------------------------------------------------------+
|                       REACT 18+ SPA FRONTEND                          |
|   React 18 + Vite + TypeScript + React Router v6 + Axios + Tailwind CSS|
|   [Components: AuthContext, ExamEngine, StudentDashboard, AdminPortal]|
+-----------------------------------------------------------------------+
                                   |
                          REST API (JSON / JWT)
                                   v
+-----------------------------------------------------------------------+
|                            FLASK BACKEND                              |
|  +------------------+  +------------------+  +--------------------+   |
|  | Auth Blueprint   |  | Admin/Student Bp |  | Subscription Gate  |   |
|  | /api/auth        |  | /api/admin       |  | /api/subscription  |   |
|  +------------------+  +------------------+  +--------------------+   |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |                         RAG ENGINE                              |  |
|  |  PyMuPDF + Groq Vision OCR + FAISS Vector Index + Groq LLM API  |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
                                   |
                          Flask-SQLAlchemy ORM
                                   v
+-----------------------------------------------------------------------+
|                      SQLite / PostgreSQL Database                      |
+-----------------------------------------------------------------------+
```

---

## 7. 🔌 API Specifications Summary

| Method | Endpoint | Blueprint | Access Level | React Component / Consumer |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | `auth_bp` | Public | `<LoginModal />` / `useAuth` hook |
| `POST` | `/api/auth/register` | `auth_bp` | Public | `<RegisterForm />` |
| `GET` | `/api/admin/platform/students` | `admin_bp` | Admin | `<AdminStudentTable />` |
| `GET` | `/api/admin/platform/institutions`| `admin_bp` | Admin | `<AdminInstitutionList />` |
| `POST` | `/api/admin/exams/generate-textbook` | `admin_bp` | Admin | `<TextbookExamGenerator />` |
| `GET` | `/api/student/dashboard` | `student_bp` | Student | `<StudentDashboard />` / Recharts |
| `POST` | `/api/student/exams/{id}/submit` | `student_bp` | Student | `<ExamEngine />` |
| `GET` | `/api/subscription/plans` | `subscription_bp` | Public | `<PricingCards />` |

---

## 8. 🗺️ Future Roadmap & Phase 2

* **PWA & Offline React Support:** Service Workers & IndexedDB for offline exam taking and background sync.
* **Webhook Callbacks:** Real-time Razorpay payment webhook processing in Flask (`payment_bp`).
* **Adaptive AI Tutor:** Personal AI learning recommendations rendered as interactive React flashcards.
