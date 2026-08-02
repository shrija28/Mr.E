# Quick Start - Admin Dashboard Testing

## 1️⃣ Start Backend

```bash
cd backend
python -m uvicorn smartkcet.main:app --reload --host 127.0.0.1 --port 8000
```

Wait for output:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 2️⃣ Open Admin Dashboard

Go to: `http://127.0.0.1:8000/admin/dashboard`

Login with:
- Email: `admin@smartkcet.com`
- Password: (from the hash in `backend/.env`)

## 3️⃣ Create Test Data

### Option A: Via UI (Easiest)
1. Click on "Total Students" KPI card → goes to `/admin/students` ✅
2. Click "Seed Test Data" button
3. Confirm dialog
4. Wait for success message

### Option B: Via Python Script
```bash
cd backend
python -m smartkcet.db.seed_students
```

## 4️⃣ Verify Data Created

After seeding, you should see:
- **Students**: 20 total (5 direct + 15 institution-linked)
- **Institutions**: 3 institutions
- **Subscriptions**: Plans displayed on `/admin/subscriptions`

## 5️⃣ Test All Features

| Feature | URL | Expected |
|---------|-----|----------|
| Dashboard | `/admin/dashboard` | Total Students = 20 |
| Students | `/admin/students` | List of 20 students |
| Institutions | `/admin/institutions` | List of 3 institutions |
| Subscriptions | `/admin/subscriptions` | Show all plans |

## 🆘 Troubleshooting

### Getting 404 on `/api/admin/platform/students`?
✅ **Fixed!** Route prefix has been corrected. Restart backend.

```bash
# Restart backend
cd backend
python -m uvicorn smartkcet.main:app --reload
```

### Seed Data Fails?
1. Check backend is running: `curl http://127.0.0.1:8000/api/health`
2. Check you're logged in as admin
3. Check browser console (F12 → Console tab) for errors
4. See `backend/TROUBLESHOOTING_GUIDE.md` for detailed help

### No Data Showing?
Run seed script directly:
```bash
cd backend
python -m smartkcet.db.seed_students
```

---

## Test Data Created

### Test Institutions
- **KCET Academy** (Code: KCET_AC_001)
- **Engineering Coaching Centre** (Code: ENG_CC_001)
- **NEET Plus Institute** (Code: NEET_INST_001)

### Test Students (Direct)
- `student1@smartkcet.test` - `student5@smartkcet.test`
- Password: `TestPass{1-5}@123`
- IDs: `KCET001` - `KCET005`

### Test Students (Institution-Linked)
- `inst1_student1@smartkcet.test` - `inst3_student5@smartkcet.test`
- Password: `TestPass{1-5}@123`
- IDs: `KCET_AC_001` - `NEET_INST_005`

---

## What's Fixed ✅

1. **Total Students Link** → Now goes to `/admin/students`
2. **Students Page** → Can create test data, shows all students
3. **Institutions Page** → Can create test institutions
4. **Subscriptions Page** → Shows all subscription plans
5. **Route Prefix** → Fixed to `/api/admin/platform/*`

---

See `backend/TROUBLESHOOTING_GUIDE.md` for detailed troubleshooting.
