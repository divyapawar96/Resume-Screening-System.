# AI-Based Resume Screening & Skill Matching System

A sophisticated end-to-end platform designed to automate the recruitment process using AI. This system leverages **SentenceTransformers** for semantic analysis to match candidate resumes against job descriptions with human-like understanding.

## 🌟 Key Features

- **Multi-Format Parsing**: Automatically extracts data from **PDF, DOCX, and TXT** files.
- **AI Matching Engine**: Uses semantic similarity to understand skills beyond simple keyword matching (e.g., recognizes that "React" and "Frontend" are related).
- **Ranking System**: A multi-factor scoring algorithm that considers skill match (80%), resume quality (12%), education (5%), and experience (3%).
- **Interactive Dashboard**: A modern, animated React frontend built with Vite and Framer Motion.
- **Skill Gap Analysis**: Identifies exactly which required skills are missing from each candidate's profile.

## 🏗️ Project Structure

```text
├── backend/            
│   ├── api.py         
│   ├── matcher.py      
│   ├── resume_parser.py 
│   └── ...            
├── frontend/           
│   ├── src/            
│   └── ...            
├── data/               
│   ├── sample_resumes/ 
│   └── sample_jds/    
├── outputs/            # System-generated artifacts
│   └── uploads/        # Temporary storage for uploaded files
└── requirements.txt    # Python dependencies
```

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js & npm

### 2. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn backend.api:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --port 5175
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, SentenceTransformers, NumPy, Pandas, PyPDF2
- **Frontend**: React 19, Vite, Framer Motion, Lucide Icons, Axios, jsPDF

## 📊 Evaluation
You can verify the system's accuracy by running the provided script:
```bash
python verify_system.py
```

---
*Created with ❤️ for efficient recruitment.*

