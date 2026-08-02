# SmartKCET Prep — Implementation History

A consolidated record of what was built, when, and how the project evolved.

---

## Project Evolution

SmartKCET Prep started as a basic KCET exam preparation platform and grew into a full multi-role SaaS product with a subscription system, institution management, Razorpay payment integration, and a role-based access control layer.

### Timeline

| Phase | Description |
|-------|-------------|
| **Initial Build** | FastAPI backend, SQLite database, basic exam generation via FAISS + Groq |
| **Platform Upgrade** | Three-role system (platform_admin, institution_admin, student), subscription models, RBAC middleware |
| **Subscription Platform** | Full subscription lifecycle, usage tracking, institution invitation flow, background scheduler |
| **Frontend Implementation** | 10 JS modules, 8 HTML pages, subscription modal/banner, exam access gating |
| **Personal Student Flow** | Auto-open subscription modal for `direct_subscriber` students, Razorpay for paid plans |
| **Bug Fixes & Hardening** | UUID parsing fix, 429 rate-limit fix, post-payment modal re-open fix, missing backend model fields |

---

## Major Features Added

### Three-Role System
- `platform_admin` — unrestricted access, manages institutions and plans
- `institution_admin` — manages institution students, uploads content, views analytics
- `student` — two subtypes: `direct_subscriber` (personal) and `institution_linked`

### Subscription System
- Free Trial (7-day, 5-exam cap), Pro Monthly (₹349), Pro Yearly (₹2999), Free (₹0)
- Trial → Pro upgrade path
- Subscription lifecycle: active → grace_period → expired
- Background scheduler runs every 60 minutes to process renewals and expirations

### Payment Integration (Razorpay)
- Students pay directly via Razorpay checkout for Trial/Monthly/Yearly plans
- Free plan activates instantly via `/api/subscription/activate-free`
- HMAC webhook verification for production payment events
- Idempotent order processing with rate limiting (5 orders/min/IP)

### Institution Flow
- Institution registers → gets an `institution_admin` account
- Admin generates invitation codes (32+ chars, 7-day validity)
- Students accept invite → linked to institution → inherit institution subscription
- Student removal preserves all exam history

### Frontend SPA
- Vanilla JS, no frameworks
- Client-side routing with RBAC
- Subscription banner (sticky, collapsible, color-coded by status)
- Subscription modal (4-plan cards, Razorpay integration)
- Subscription management page with billing history
- WCAG 2.1 Level AA accessibility, responsive 320px–1920px

---

## Institution Platform Changes

**Backend files created/modified:**
- `backend/smartkcet/institution/service.py` — registration, invitation, student management, plan activation
- `backend/smartkcet/institution/routes.py` — 8 REST endpoints
- `backend/smartkcet/institution/models.py` — request/response schemas
- `backend/smartkcet/institution/content.py` — file upload, question generation (PDF/DOCX/TXT, 20MB max)

**API endpoints:**
- `POST /api/institution/register`
- `POST /api/institution/invite`
- `POST /api/institution/accept-invite`
- `DELETE /api/institution/students/{id}`
- `GET /api/institution/students`
- `GET /api/institution/analytics`
- `POST /api/institution/subscription/select`

---

## Student Platform Changes

**Dashboard auto-open flow:**
- `direct_subscriber` students with no active subscription see the modal automatically after 500ms
- Gate logic checks `is_active`, `status`, and `plan_type` before showing modal
- Institution students are redirected to `/student/institution/dashboard` — never see the modal

**Exam access control:**
- `ensureExamAccess()` in `frontend/js/exam.js` calls `POST /api/exam/check-access` before every exam start
- Error codes: `quota_exhausted`, `institution_quota_exhausted`, `subscription_expired`, `subscription_required`
- Remaining attempts displayed on exam entry form

---

## Subscription System

See `docs/SUBSCRIPTION_SYSTEM.md` for full architecture, modal logic, and payment flow details.

**Key backend files:**
- `backend/smartkcet/subscription/service.py`
- `backend/smartkcet/subscription/routes.py`
- `backend/smartkcet/subscription/usage.py`
- `backend/smartkcet/subscription/access_control.py`
- `backend/smartkcet/subscription/scheduler.py`

**Database models (7 tables):**
`SubscriptionPlan`, `Subscription`, `SubscriptionEvent`, `BillingRecord`, `PaymentLog`, `InstitutionSubscription`, `UsageRecord`

---

## Payment System

**Architecture:**
1. Frontend calls `POST /api/payments/create-order` with `plan_id`
2. Backend creates Razorpay order, returns `order_id`, `amount`, `key_id`
3. Razorpay checkout opens in browser
4. On success: frontend calls `POST /api/payments/verify`
5. Backend verifies HMAC signature → activates subscription
6. Production: Razorpay webhook hits `POST /api/payments/webhook`

**Critical bug fixed (UUID parsing):**
The JWT `sub` claim contains a KCET ID string (`KCET0006`), not a UUID. The original code called `uuid.UUID(payload.get("sub", ""))` which raised a `ValueError`. Fix: use `user.id` directly from `current_user()`.

**Razorpay test credentials** (stored in `backend/.env`):
- Key: `rzp_test_T0LO9N2ESKhzUA`
- Test card: `4111 1111 1111 1111`, test UPI: `success@razorpay`

---

## Current Working Status

As of the last implementation checkpoint:

| Component | Status |
|-----------|--------|
| Backend API | ✅ Running (FastAPI + uvicorn) |
| Database migrations | ✅ 10 migrations applied |
| Subscription endpoints | ✅ All 6 working |
| Payment endpoints | ✅ Working (test mode) |
| Institution endpoints | ✅ Working |
| Frontend SPA | ✅ Served by FastAPI at port 8000 |
| Subscription modal | ✅ Auto-opens for personal students |
| Subscription banner | ✅ Displays on all student pages |
| Exam access gating | ✅ Enforced before exam start |
| Background scheduler | ✅ Starts on app startup |
| 239 backend tests | ✅ Passing |

**Known limitations (non-blocking):**
- No subscription upgrade UI (trial → pro requires expiry)
- No payment history page in UI
- No email notifications on subscription events
- Some test infrastructure failures unrelated to business logic

---

## Final Architecture

```
SmartKCET Prep
├── backend/                    Python FastAPI application
│   ├── smartkcet/
│   │   ├── auth/              JWT, bcrypt, role management
│   │   ├── subscription/      Plans, lifecycle, usage, scheduler
│   │   ├── payments/          Razorpay gateway, order creation, verification
│   │   ├── institution/       Registration, invitations, student management
│   │   ├── student/           Exams, submissions, access control
│   │   ├── admin/             Platform admin, analytics
│   │   ├── rag/               FAISS + Groq for question generation
│   │   └── middleware/        RBAC
│   ├── migrations/            10 Alembic migration files
│   └── tests/                 239 passing tests
│
├── frontend/                   Vanilla JS SPA
│   ├── html/                  30+ HTML pages
│   ├── css/                   4 stylesheets
│   └── js/                    10+ modules (subscription, exam, auth, routing)
│
└── docs/                       Project documentation
    ├── SETUP.md
    ├── IMPLEMENTATION_HISTORY.md  (this file)
    ├── SUBSCRIPTION_SYSTEM.md
    └── DEBUGGING_HISTORY.md
```

**Running the project:**
```bash
cd backend
python app.py
# Frontend served at http://127.0.0.1:8000
```
