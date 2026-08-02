# SmartKCET Prep — Subscription System

Complete reference for the subscription architecture, personal student flow, institution flow, modal logic, and Razorpay integration.

---

## Subscription Architecture

### Plans

| Plan | Price | Type | Access |
|------|-------|------|--------|
| Free | ₹0 | individual | 3–5 mock tests, basic analytics |
| 7-Day Premium Trial | ₹99 | individual | Unlimited tests for 7 days |
| Pro Monthly | ₹349 | individual | Unlimited, monthly billing |
| Pro Yearly | ₹2999 | individual | Unlimited, yearly billing |
| Institution plans | Varies | institution | Configured per institution |

Plans are stored in `subscription_plans` table. Individual plans require `plan_type = 'individual'` and `is_active = true`.

### Database Tables

- `subscription_plans` — plan definitions
- `subscriptions` — user subscription records
- `subscription_events` — audit trail for all state transitions
- `billing_records` — Razorpay order records
- `payment_logs` — payment verification logs
- `institution_subscriptions` — institution-level subscriptions
- `usage_records` — exam attempt tracking

### Status Values

`trial` → `active` → `grace_period` → `expired`

Cancellation sets `pending_cancellation = true`; scheduler processes at period end.

### Background Scheduler

`backend/smartkcet/subscription/scheduler.py`

- Runs every 60 minutes (configurable via `SUBSCRIPTION_SCHEDULER_INTERVAL_MINUTES`)
- Processes renewals, grace period entries, expirations, pending cancellations
- Cleans up events older than 90 days
- Starts automatically on FastAPI app startup

---

## Personal Student Flow

Personal students are identified by `student_subtype = 'direct_subscriber'`.

### Registration → Dashboard Flow

```
Student registers / logs in
    ↓
Dashboard loads (dashboard.js → initDashboard())
    ↓
Auth.currentRole() → check student_subtype
    ↓
direct_subscriber detected
    ↓
_checkAndPromptSubscription() called
    ↓
GET /api/subscription/status
    ↓
Gate 1: is_active === true? → BLOCK (has subscription)
Gate 2: status in ['trial','active','grace_period']? → BLOCK
Gate 3: plan_type = 'individual' + name contains 'free'? → BLOCK
    ↓
All gates pass → wait 500ms → SubscriptionModal.show()
```

### Gate Logic (dashboard.js)

```javascript
// Force fresh data after payment
const sub = await Subscription.getStatus(true);

const hasValidSubscription = (
  (sub && sub.has_subscription === true) ||
  (sub && sub.is_active === true) ||
  (sub && ['trial', 'active', 'trialing', 'grace_period'].includes(sub.status))
);

if (hasValidSubscription) return; // Modal blocked
```

### After Payment

After a successful Razorpay payment:
1. Frontend calls `Subscription.getStatus(true)` to force-bypass the 60-second cache
2. Gate logic re-evaluates with fresh data
3. Modal is blocked; green subscription banner appears
4. Dashboard refreshes automatically

---

## Institution Student Flow

Institution students have `student_subtype = 'institution_linked'`.

- **Never see** the personal subscription modal
- On login, dashboard.js detects `institution_linked` and redirects to `/student/institution/dashboard`
- Access is controlled by the institution's subscription, not individual payments
- Students inherit institution subscription quota (weekly/monthly exam limits)

---

## Modal Logic

### Files

- `frontend/html/subscription_modal.html` — 4-card HTML structure
- `frontend/js/subscription-modal.js` — all modal logic
- `frontend/css/subscription-modal-premium.css` — styling

### Plan Cards

1. **Free (₹0)** — "Start Free" → `POST /api/subscription/activate-free`
2. **7-Day Premium Trial (₹99)** — "Start 7-Day Trial" → Razorpay flow
3. **Pro Monthly (₹349)** — "Subscribe Monthly" → Razorpay flow
4. **Pro Yearly (₹2999)** — "Subscribe Yearly" → Razorpay flow

### Duplicate Request Prevention

The `_isBusy` flag prevents multiple API calls per button click:

```javascript
// Reset on ALL exit paths
_isBusy = false;  // on error, on dismissal, on network failure

// Button guards
if (_isBusy) { evt.preventDefault(); return; }

// Visual feedback
btn.disabled = !!isLoading;
btn.style.opacity = isLoading ? '0.5' : '1';
```

Event listeners are bound only once (`_initialized` flag) to prevent duplicate listener accumulation when modal reopens.

### Layout

- Desktop: 4 plans in a single horizontal row, modal up to 1500px wide
- Tablet: 2×2 grid
- Mobile: single column stack
- Keyboard: Escape closes, Tab cycles through, focus trap active
- ARIA: `aria-labelledby`, `aria-describedby`, `role="dialog"`

---

## Payment Flow (Razorpay Integration)

### Full Flow

```
User clicks paid plan
    ↓
Frontend: POST /api/payments/create-order  { plan_id: "uuid" }
    ↓
Backend: creates Razorpay order → returns { order_id, amount, key_id }
    ↓
Frontend: opens Razorpay checkout popup
    ↓
User completes payment
    ↓
Frontend: POST /api/payments/verify  { razorpay_order_id, razorpay_payment_id, razorpay_signature }
    ↓
Backend: verifies HMAC signature → activates subscription
    ↓
Production: Razorpay webhook → POST /api/payments/webhook → backup activation
    ↓
Modal closes → page refreshes → subscription active
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/subscription/activate-free` | POST | Activate free plan (no payment) |
| `/api/payments/create-order` | POST | Create Razorpay order for paid plans |
| `/api/payments/verify` | POST | Verify payment signature after checkout |
| `/api/payments/webhook` | POST | Production Razorpay webhook handler |
| `/api/payments/plans/student` | GET | Fetch available student plans with key_id |
| `/api/subscription/status` | GET | Get effective subscription status |
| `/api/subscription/select` | POST | Activate trial or pro plan |
| `/api/subscription/upgrade` | POST | Upgrade from trial to pro |
| `/api/subscription/cancel` | POST | Cancel subscription |

### Security

- HMAC signature verification on all webhook events (`razorpay_signature` validated)
- Idempotent webhook processing (duplicate events skipped via `order_id` uniqueness)
- Rate limiting: 5 orders per minute per IP
- Replay attack protection via `BillingRecord` uniqueness constraint
- HTTPS-only payment gateway, httpOnly JWT cookies for auth

### Test Configuration

```env
RAZORPAY_KEY_ID=rzp_test_T0LO9N2ESKhzUA
RAZORPAY_KEY_SECRET=tDMTgi49Uu7uuo7lY7lE0unX
RAZORPAY_WEBHOOK_SECRET=smartkcet_test_secret
```

**Test cards:**
- Success: `4111 1111 1111 1111` (any CVV, any future expiry)
- Failure: `4000 0000 0000 0002`
- Test UPI: `success@razorpay` / `failure@razorpay`

**Switching to production:** Update `.env` with `rzp_live_...` keys. No code changes needed.

---

## Access Protection

### Exam Access Gate

`frontend/js/exam.js` → `ensureExamAccess(subject, set)`

Before every exam start:
1. Calls `POST /api/exam/check-access`
2. On HTTP 200 → proceed to exam
3. On HTTP 403 → show appropriate error modal based on `error_code`:
   - `quota_exhausted` → "Upgrade to Pro" prompt
   - `institution_quota_exhausted` → institution quota modal with reset date
   - `subscription_expired` → "Renew Subscription" prompt
   - `subscription_required` → opens `SubscriptionModal.show()`

### Feature Access by Plan

| Feature | No Subscription | Free | Trial | Pro |
|---------|----------------|------|-------|-----|
| Exam access | ❌ Blocked | ✅ 3–5 total | ✅ Unlimited (7 days) | ✅ Unlimited |
| Basic analytics (score, pass/fail) | ❌ | ✅ | ✅ | ✅ |
| Full analytics (topic breakdown, trends) | ❌ | ❌ | ✅ | ✅ |
| AI recommendations | ❌ | ❌ | ✅ | ✅ |
| Leaderboard | ❌ | ❌ Hidden | ✅ Full | ✅ Full (Gold/Silver/Bronze) |

### Subscription Banner

`frontend/js/subscription-banner.js`

- Renders immediately after `<nav>` on all authenticated student pages
- Color-coded: green (active), yellow/orange (expiring/overdue), red (expired)
- Status-specific text:
  - Free Trial: "X of 5 attempts remaining · Y days left"
  - Pro: billing period + next renewal date
  - Institution: institution name + weekly/monthly remaining
  - Expired: "Upgrade Now" CTA
- Collapsible with sessionStorage persistence
- Updates within 5 seconds of status change via `subscriptionStatusChanged` CustomEvent

---

## Final Working State

As of last verification:

- ✅ Personal student logs in → modal auto-opens for users with no active subscription
- ✅ Free plan activates instantly (₹0, no Razorpay)
- ✅ Paid plans open Razorpay checkout
- ✅ After payment: modal closes, banner shows, modal never reopens
- ✅ Institution students never see the personal subscription modal
- ✅ Exam access blocked until plan chosen
- ✅ Subscription management page shows plan name, start date, renewal date
- ✅ `plan_name`, `start_date`, `current_period_start` fields returned by backend status API
- ✅ 429 duplicate request error eliminated via `_isBusy` flag on all paths
