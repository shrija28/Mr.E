# 🚀 SmartKCET Project - RUNNING

**Status:** ✅ **BACKEND RUNNING**

---

## ✅ Current Status

### Backend Server
- **Status:** Running ✓
- **URL:** http://127.0.0.1:8000
- **Health Check:** http://127.0.0.1:8000/health
- **Admin Dashboard:** http://127.0.0.1:8000/admin/dashboard

### Frontend
- **Status:** Ready to serve
- **Main Page:** Open `frontend/html/index.html` in browser

---

## 📋 Quick Access Links

| Feature | URL |
|---------|-----|
| **Health Check** | http://127.0.0.1:8000/health |
| **Admin Dashboard** | http://127.0.0.1:8000/admin/dashboard |
| **API Docs (Swagger)** | http://127.0.0.1:8000/docs |
| **ReDoc** | http://127.0.0.1:8000/redoc |

### Admin Login Credentials
- **Email:** `admin@smartkcet.com`
- **Password:** Check `backend/.env` file for hash

---

## 🎯 Test Data Available

The project has pre-seeded data in the database:

### Test Institutions (3)
1. **KCET Academy** - 5 students
2. **Engineering Coaching Centre** - 5 students  
3. **NEET Plus Institute** - 5 students

### Test Students (20)
- **Direct Students (5):** student1-5@smartkcet.test
- **Institution Students (15):** inst1/inst2/inst3_student1-5@smartkcet.test

### Test Subscriptions (8)
- **Individual Plans (5):** Trial status
- **Institutional Plans (3):** Active status

---

## 🌐 How to Access

### Option 1: Admin Dashboard (Full Featured)
1. Go to: **http://127.0.0.1:8000/admin/dashboard**
2. Login with admin credentials
3. Manage students, institutions, subscriptions

### Option 2: HTML Frontend
1. Open: **`frontend/html/index.html`** in your browser
2. Or run: `python -m http.server 3000 -d frontend`
3. Then navigate to: **http://127.0.0.1:3000**

### Option 3: API Direct Access
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## 📊 Key Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /api/health` - Detailed API health

### Authentication
- `POST /api/auth/register` - Register new account
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token

### Admin APIs
- `GET /api/admin/platform/students` - List all students
- `GET /api/admin/platform/institutions` - List institutions
- `GET /api/admin/platform/subscriptions` - List subscriptions
- `POST /api/admin/seed-test-data` - Create test data

### Subscription APIs
- `GET /api/subscription/plans` - Get available plans
- `POST /api/subscription/subscribe` - Subscribe to plan
- `GET /api/subscription/status` - Check subscription status

---

## 🔧 Backend Commands

### Start Backend (Already Running)
```bash
cd backend
python -m uvicorn smartkcet.main:app --host 127.0.0.1 --port 8000 --reload
```

### Stop Backend
- Press `CTRL+C` in the terminal running the backend

### Restart Backend
1. Stop it (Ctrl+C)
2. Run start command again

### View Backend Logs
```bash
# Follow the terminal output of the running backend process
```

---

## 📱 Frontend Setup

### Static Files (Recommended)
The frontend is already in `frontend/html/`. Open `index.html` in any browser.

### HTTP Server
```bash
cd frontend
python -m http.server 3000
```
Then open: http://127.0.0.1:3000

### With Node.js (if needed)
```bash
npm install
npm start
```

---

## 🧪 Testing the System

### 1. Health Check
```bash
curl http://127.0.0.1:8000/health
```

### 2. Login Test
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@smartkcet.com","password":"your_password"}'
```

### 3. Get Students List
```bash
curl http://127.0.0.1:8000/api/admin/platform/students \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⚙️ Configuration

### Backend Port
- Default: `8000`
- Override: Set `SMARTKCET_PORT` environment variable
- Example: `$env:SMARTKCET_PORT=8001`

### Host
- Default: `127.0.0.1`
- Override: Set `SMARTKCET_HOST` environment variable

### Database
- Location: `backend/smartkcet.db`
- Type: SQLite
- Auto-created on first run

---

## 📦 Database Info

### Current Data
- **21 Users** (1 admin + 20 students)
- **3 Institutions** (all active)
- **8 Subscriptions** (5 trial + 3 active)

### Data Report
See: `DB_STUDENT_INSTITUTION_REPORT.md` for complete database analysis

### Data Export
- JSON Export: `backend/database_export.json`
- Python Script: `backend/export_detailed_data.py`

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process on port 8000
taskkill /PID <PID> /F

# Try different port
$env:SMARTKCET_PORT=8001
python app.py
```

### 404 Errors on API
- Verify backend is running
- Check URL path is correct (use `/api/admin/...` not `/admin/...`)
- Restart backend after code changes

### Database Errors
- Check `backend/smartkcet.db` exists
- Try recreating: Delete `smartkcet.db` and restart backend
- Check file permissions in `backend/` directory

### CORS Issues
- All origins allowed by default (`*`)
- Credentials must be sent in requests
- Check browser console (F12) for detailed errors

---

## 📚 Documentation Files

- **QUICK_START.md** - Quick start guide
- **START_HERE.txt** - Project overview
- **ADMIN_DASHBOARD_QUICK_START.txt** - Admin dashboard guide
- **RUN_PROJECT_IN_VSCODE.md** - VS Code setup
- **TROUBLESHOOTING_GUIDE.md** - Detailed troubleshooting

---

## 🎓 Project Structure

```
SmartKCET Prep/
├── backend/
│   ├── app.py                 # Backend entry point
│   ├── smartkcet/
│   │   ├── main.py           # FastAPI app setup
│   │   ├── auth/             # Authentication
│   │   ├── admin/            # Admin features
│   │   ├── student/          # Student features
│   │   ├── subscription/     # Subscription management
│   │   └── ...
│   ├── smartkcet.db          # SQLite database
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── html/
│   │   ├── index.html        # Main page
│   │   ├── exam.html         # Exam page
│   │   └── ...
│   ├── css/
│   ├── js/
│   └── ...
├── docs/                      # Documentation
└── README.md                  # Project README
```

---

## ✨ Features Available

✅ User authentication (login/register)
✅ Admin dashboard with analytics
✅ Student management
✅ Institution management
✅ Subscription plans & billing
✅ Exam creation & submission
✅ Performance analytics
✅ Database seeding for testing
✅ RESTful API with Swagger docs
✅ Role-based access control

---

## 🚀 Next Steps

1. **Open Admin Dashboard:** http://127.0.0.1:8000/admin/dashboard
2. **Login** with admin credentials
3. **Explore** the available features
4. **Test** with pre-seeded data
5. **View** database contents (see reports)
6. **Develop** your features

---

## 📞 Support

- Check terminal output for errors
- Review `TROUBLESHOOTING_GUIDE.md` for solutions
- Check `backend/` logs directory for detailed logs
- Inspect browser console (F12) for frontend errors

---

**Project Status:** ✅ Ready for Development and Testing
**Last Updated:** June 19, 2026

