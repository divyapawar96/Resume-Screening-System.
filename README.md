# Resume Screening & Skill Matching System
## 🖳 Project Description

This project is an AI-based Resume Screening and Skill Matching System that automatically analyzes resumes and matches candidates with job descriptions using Natural Language Processing (NLP) and semantic similarity techniques.

The system helps recruiters reduce manual effort by ranking candidates based on skill relevance, experience, and job requirements.
## ⚠️ Problem Statement

Recruiters often receive hundreds of resumes for a single job role. Manual resume screening is time-consuming, biased, and inefficient.

This project aims to automate resume screening by intelligently matching resumes with job descriptions and providing a clear match score and skill gap analysis.
## 💡 Solution Overview

The system extracts important information from resumes and job descriptions such as skills, experience, and education. It then uses semantic embeddings to calculate similarity scores and ranks candidates based on their suitability for the job role.
## 📐 System Architecture (MVBS)

- **Model:** NLP models and Sentence Transformers for skill matching
- **View:** Web-based user interface using Streamlit
- **Business Logic:** Resume parsing, matching, scoring, and ranking logic
- **Storage:** Structured data storage for resumes and job descriptions
## ⚜️ Features

- Resume parsing (PDF & DOCX)
- Job description parsing
- Semantic skill matching using embeddings
- Candidate ranking based on match score
- Skill gap analysis
- AI-powered resume summarization
- Interactive web dashboard
- Visual skill comparison charts
## 🛠 Technologies Used

- Python
- NLP (SpaCy)
- Sentence Transformers
- Streamlit
- Pandas & NumPy
- Matplotlib & Plotly
- Google Colab
- GitHub
## ⚙ Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/divyapawar96/ResumeScreeningSystem.git
pip install -r requirements.txt
streamlit run web_app/app.py
## 🏅 Unique Enhancements

- Skill gap identification with recommendations
- Resume summarization for quick HR review
- Visual skill comparison using radar charts
- Multi-resume comparison dashboard
## 🔮 Future Scope

- Resume recommendation system
- Automated interview scheduling
- ATS system integration
- Real-time recruiter dashboard
