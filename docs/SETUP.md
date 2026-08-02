# Setup Instructions - ExamForge AI

## Prerequisites
- Python 3.8+
- GROQ API Key (get it from https://console.groq.com/keys)

## Step 1: Set GROQ API Key (Windows Environment Variable)

### Option A: Permanent System Environment (Recommended)
1. Press `Win + X` → Click **System**
2. Click **Advanced system settings** (right side)
3. Click **Environment Variables** button
4. Under "User variables" section → Click **New**
   - Variable name: `GROQ_API_KEY`
   - Variable value: `paste_your_api_key_here`
5. Click **OK** three times
6. **Restart your terminal/IDE** to apply changes

### Option B: Temporary (Per PowerShell Session)
```powershell
$env:GROQ_API_KEY = "your_api_key_here"
```

### Option C: Temporary (Per CMD Session)
```cmd
set GROQ_API_KEY=your_api_key_here
```

## Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 3: Run the Backend

```bash
cd backend
python app.py
```

You should see:
```
============================================================
🚀 ExamForge Backend Starting
============================================================
Server: http://localhost:8000
Health: http://localhost:8000/health
============================================================
```

The API will be available at `http://localhost:8000`

## Step 4: Serve Frontend

Open the frontend in your browser using one of these methods:

**Option 1: Python HTTP Server**
```bash
cd frontend
python -m http.server 3000
```
Then open: `http://localhost:3000/html/index.html`

**Option 2: VS Code Live Server**
- Install "Live Server" extension
- Right-click `frontend/html/index.html` → "Open with Live Server"

**Option 3: Direct File**
- Simply open `frontend/html/index.html` in your browser

## Usage Guide

### 1. Generate Question Papers
1. Open the frontend in your browser
2. Upload 2-10 PDF/DOCX/TXT files of previous year papers
3. Select difficulty level
4. Click "Generate Question Sets"
5. Download the generated question papers

### 2. Take an Exam
1. Select a question set from the generator
2. Answer all questions
3. Submit to see performance analysis

### 3. View Performance Dashboard
- Analyze your exam performance
- See topic-wise scores
- Get personalized recommendations

## Troubleshooting

### "GROQ_API_KEY environment variable is not set"
- Make sure you set the Windows environment variable (Step 1)
- Restart your terminal/IDE after setting it
- Verify with: `echo $env:GROQ_API_KEY` (PowerShell)

### "Module not found" Errors
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### CORS/Connection Issues
- Verify backend is running on `http://localhost:8000`
- Update API endpoint in frontend JS files if using different port:
  - `frontend/js/app.js`
  - `frontend/js/exam.js`
  - `frontend/js/dashboard.js`

### Port Already in Use
The backend automatically kills any existing process on port 8000 on startup.
