# ExamForge AI - RAG Question Paper Generator

A smart exam paper generation system using Retrieval-Augmented Generation (RAG) to create unique question papers from previous year papers.

## Project Structure

```
project/
├── backend/                 # FastAPI backend with Python
│   ├── app.py             # Main Flask/FastAPI application
│   ├── examforge_backend.ipynb # Jupyter notebook for development
│   └── utils/             # Utility modules
├── frontend/              # Web interface
│   ├── html/             # HTML pages
│   │   ├── index.html    # Main generator page
│   │   ├── exam.html     # Exam interface
│   │   └── dashboard.html # Dashboard view
│   ├── js/               # JavaScript files
│   │   ├── app.js        # Main application logic
│   │   ├── exam.js       # Exam page functionality
│   │   └── dashboard.js  # Dashboard functionality
│   └── css/              # Stylesheets
│       └── style.css     # Main styles
├── docs/                 # Documentation
└── README.md             # This file
```

## Features

- **RAG-Powered Generation**: Upload 10 previous year papers, AI extracts patterns
- **Multiple Question Sets**: Generates 4 unique question sets
- **Student Performance Analysis**: Analyzes performance metrics
- **Web-Based Interface**: Modern, responsive UI

## Getting Started

See [docs/SETUP.md](docs/SETUP.md) for complete setup instructions.

### Quick Start (Windows)

1. **Set GROQ API Key** (Windows Environment Variable):
   - Press `Win + X` → **System** → **Advanced system settings** → **Environment Variables**
   - Add: `GROQ_API_KEY` = your_api_key
   - Restart terminal

2. **Run Backend**:
   ```bash
   cd backend
   python app.py
   ```

3. **Open Frontend**:
   - Open `frontend/html/index.html` in your browser
   - Or use: `python -m http.server 3000 -d frontend`

### Frontend

The frontend is a static web application. Open `frontend/html/index.html` in a browser or serve it via a web server.

## API Endpoints

- `POST /upload` - Upload papers for processing
- `POST /generate` - Generate question papers
- `GET /dashboard` - Get performance metrics


