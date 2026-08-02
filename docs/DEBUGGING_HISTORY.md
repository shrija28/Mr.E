# SmartKCET Prep — Debugging History

A consolidated record of bugs encountered, root causes identified, and fixes applied during development.

---

## Major Bugs Encountered

| Bug | Symptom | Root Cause | Status |
|-----|---------|------------|--------|
| UUID parsing error | `400 "badly formed hexadecimal UUID string"` on payment | JWT `sub` claim is a KCET ID string, not UUID | ✅ Fixed |
| Subscription modal reopens after payment | Modal opens again after successful payment | Stale cache + incomplete gate logic + leftover force-test code | ✅ Fixed |
| 429 Too Many Requests | 10+ API calls per button click | Missing `_isBusy` flag resets, no button click guards, duplicate event listeners | ✅ Fixed |
| Modal not auto-opening | Personal student lands on dashboard, no modal | Test user had active subscription in DB (correct behavior, bad test data) | ✅ Identified |
| Missing plan name / start date | Subscription management page shows `—` for plan name and started date | Backend `EffectiveSubscriptionStatus` model missing `plan_name`, `start_date`, `current_period_start` fields | ✅ Fixed |
| Wrong API endpoint in comments | References to non-existent `/api/subscription/me` | Old documentation, code always used correct `/api/subscription/status` | ✅ Clarified |

---

## Root Causes

### UUID Parsing Bug

**File:** `backend/smartkcet/payments/routes.py`

**Buggy code:**
```python
elif role == "student":
    user_id = uuid.UUID(payload.get("sub", ""))  # ❌ BUG
```

The JWT `sub` claim for students contains a KCET ID string like `KCET0006`, not a UUID. `uuid.UUID("KCET0006")` raises `ValueError: badly formed hexadecimal UUID string`, which was caught by the generic `ValueError` handler and returned to the client as `400 {"error": "invalid_plan", "message": "badly formed hexadecimal UUID string"}`.

The code then called `current_user()` anyway and used `user.id` for the actual DB query — so the UUID parse was completely redundant.

**Fix:**
```python
elif role == "student":
    from ..middleware.rbac import current_user
    user = current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "auth_required"})
    result = create_student_order(db, user.id, plan_id)  # ✅ use user.id directly
```

---

### Subscription Modal Reopening After Payment

**Files:** `frontend/js/dashboard.js`, `backend/smartkcet/subscription/models.py`, `backend/smartkcet/subscription/service.py`

**Root causes (three combined):**

1. **Leftover force-test code** in `dashboard.js` was unconditionally opening the modal 2 seconds after dashboard load (added during debugging, never removed)
2. **Gate logic only checked `is_active`** — after payment, the cache still had stale `is_active: false` data
3. **Cache not bypassed** after payment — needed `Subscription.getStatus(true)` to force a fresh API call

**Fixes:**
- Removed the `setTimeout` force-test block
- Added `Subscription.getStatus(true)` (force refresh) in the check function
- Extended gate logic to check `has_subscription`, `is_active`, AND status string values
- Added banner visibility as an additional safety gate

---

### 429 Too Many Requests (Duplicate Payment Requests)

**File:** `frontend/js/subscription-modal.js`

**Root causes:**
1. `_isBusy` flag was only reset on success, not on error paths (Razorpay dismissal, network error, bad response)
2. Multiple rapid button clicks bypassed the flag before it was set
3. Modal reopening re-bound event listeners without checking for duplicates, accumulating multiple listeners

**Fixes:**
```javascript
// Reset on ALL exit paths
if (!createRes.ok) {
    _setLoading(false);
    _isBusy = false;  // ← Added on error
    return;
}
modal: { ondismiss: function() {
    _setLoading(false);
    _isBusy = false;  // ← Added on dismissal
}}
catch (err) {
    _setLoading(false);
    _isBusy = false;  // ← Added on network error
}

// Button click guards
_handlers.trial = function(evt) {
    evt.preventDefault();
    if (_isBusy) return;  // ← Early return
    selectTrial();
};

// One-time listener binding
function _bindListeners() {
    if (!_modalEl || _initialized) return;
    // ... bind handlers ...
    _initialized = true;  // ← Only bind once
}
```

---

### Missing Subscription Fields on Management Page

**File:** `backend/smartkcet/subscription/models.py`, `backend/smartkcet/subscription/service.py`

The `EffectiveSubscriptionStatus` Pydantic model was missing three fields that the frontend's subscription management page needed: `plan_name`, `start_date`, `current_period_start`.

**Fix — model:**
```python
class EffectiveSubscriptionStatus(BaseModel):
    plan_name: Optional[str] = Field(None, description="Plan display name")
    start_date: Optional[datetime] = Field(None, description="Subscription start date")
    current_period_start: Optional[datetime] = Field(None)
```

**Fix — service:** All three code paths (institution, no-subscription, active subscription) now return these fields.

**Fix — frontend fallback:**
```javascript
var startDate = sub.start_date || sub.started_at || sub.current_period_start || sub.created_at;
```

---

## Fixes Applied

### Payment Endpoint (routes.py)

- Removed invalid `uuid.UUID(payload.get("sub", ""))` call for student role
- Used `user.id` from `current_user()` directly
- Added structured logging: `[create-order] RAW REQUEST body`, `Student user.id`, etc.
- Improved `ValueError` handler with full traceback in logs

### Dashboard Gate Logic (dashboard.js)

- Replaced single `is_active` check with comprehensive validation covering `has_subscription`, `is_active`, and status string set
- Added `Subscription.getStatus(true)` to force cache bypass after payment
- Removed temporary `setTimeout` force-test block
- Added banner visibility as Gate 0 (extra safety)

### Modal Event Handling (subscription-modal.js)

- `_isBusy = false` added on all non-success exit paths
- `_handlers` object stores named function references for clean removal
- `_initialized` flag prevents duplicate listener binding
- Visual button disable: `disabled`, `opacity: 0.5`, `cursor: not-allowed` during loading

### Backend Model (models.py + service.py)

- `plan_name`, `start_date`, `current_period_start` added to `EffectiveSubscriptionStatus`
- All service code paths updated to populate these fields

---

## Razorpay Issues

### Razorpay Popup Not Opening

**Cause:** Script not loaded, or `createData` missing `order_id`/`key_id`  
**Check:** `window.Razorpay` should exist; `createData.key_id` should start with `rzp_`

### Test Mode Behavior

In test mode, Razorpay checkout simulates payment without a real payment popup. This is expected Razorpay sandbox behavior — not a bug.

### Webhook Not Firing in Test Mode

Razorpay webhooks only fire for real payments. In test/development, use `POST /api/payments/verify` directly.

### Payment Verification Failed

Check HMAC signature match. In production, verify webhook URL is configured in Razorpay dashboard at `https://your-domain.com/api/payments/webhook`.

---

## Subscription Issues

### Modal Not Showing for Personal Student

**Debug checklist:**
1. Confirm `student_subtype` is `direct_subscriber` (check via `GET /api/auth/me`)
2. Confirm user has **no** active subscription (check via `GET /api/subscription/status`)
3. Open DevTools Console and look for `[subscription-onboarding]` logs
4. Verify `SubscriptionModal` is defined: `typeof SubscriptionModal !== 'undefined'`
5. Verify modal element exists: `document.getElementById('subscriptionModal')`
6. Hard-refresh (Ctrl+Shift+R) to clear any cached JS files

**Test manually:**
```javascript
SubscriptionModal.show();
```

### Modal Shows But Plans Not Visible

**Cause:** `GET /api/payments/plans/student` failed or returned empty  
**Check:** Network tab for that request; verify backend is running and `plan_type = 'individual'` plans exist with `is_active = true`

### Student Plans Missing from Database

**Symptom:** `400 {"error": "invalid_plan", "message": "Plan ... not found or inactive"}`  
**Fix:** Run `python backend/seed_student_plans.py`

**Verify:**
```sql
SELECT id, name, plan_type, price, is_active
FROM subscription_plans
WHERE plan_type = 'individual' AND is_active = true;
```

Expected: Free (₹0), 7-Day Premium Trial (₹99), Pro Monthly (₹349), Pro Yearly (₹2999)

---

## Dashboard Issues

### Institution Student Sees Personal Dashboard

**Cause:** Student subtype detection failure  
**Check:** `Auth.currentRole()` should return `student_subtype: 'institution_linked'`  
**Expected behavior:** Redirect to `/student/institution/dashboard` immediately

### Dashboard Loads But Subscription Check Doesn't Run

**Check:** Look for `[dashboard] ✅ Personal student (direct_subscriber) detected` in console. If missing, `initDashboard()` didn't reach the subtype check — look for earlier errors.

---

## Final Resolutions

All production-blocking bugs are resolved:

- ✅ UUID parsing bug fixed → paid plan orders work for students
- ✅ 429 error fixed → single API call per button click
- ✅ Modal reopen after payment fixed → gate logic reliable
- ✅ Missing subscription data fixed → management page shows complete info
- ✅ Modal auto-open confirmed working → personal students see plans on login
- ✅ Endpoint confusion resolved → code always used `/api/subscription/status` (the correct endpoint)

**Remaining non-blocking items:**
- Some backend test infrastructure failures (TestClient async loop issues) — do not affect runtime
- No email notifications on subscription events (by design, MVP scope)
