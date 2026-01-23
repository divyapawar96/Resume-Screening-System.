# Resume Screening & Skill Matching System (Backend Only)

This is a **backend-only** project that parses resumes and job descriptions, performs **semantic skill matching** using **SentenceTransformers**, ranks candidates, and generates **skill gap reports**.

## Tech Stack
- Python 3.10+
- NLP/Similarity: `sentence-transformers`
- Parsing: `PyPDF2`, `python-docx`
- Data: `numpy`, `pandas`
- Optional API: `fastapi`, `uvicorn`

## Project Structure
```
backend/
  resume_parser.py   # Parse PDF/DOCX/TXT resumes -> structured fields
  job_parser.py      # Parse job descriptions -> required fields
  matcher.py         # SentenceTransformers similarity + candidate ranking
  skill_gap.py       # Skill gap report (missing skills + match %)
  utils.py           # Logging, normalization, IO helpers
  cli.py             # Batch processing entrypoint (recommended)
  api.py             # Optional FastAPI wrapper

data/
  sample_resumes/    # 3 sample resumes (TXT) for testing
  sample_jds/        # 2 sample job descriptions (TXT) for testing
```

## Installation
Create a virtual environment, then:
```bash
pip install -r requirements.txt
```

## Run (Batch Processing)
Example: rank candidates for the NLP Data Scientist JD:
```bash
python -m backend.cli --resumes data/sample_resumes --jd data/sample_jds/jd_data_scientist.txt --top 3 --out outputs
```

The output JSON will be created at:
`outputs/ranking_and_skill_gap.json`

Additional CSV outputs:
- `outputs/candidate_ranking.csv`
- `outputs/skill_gap_report.csv`

## Sample Output (Console)
Example of what you’ll see after running the CLI:
```
=== Top Candidates ===
1. Divya Pawar | score=66.32 | sim=0.6 | quality=0.86
   matched=['docker', 'git', 'nlp', 'nltk', 'numpy', 'pandas', 'python', 'spacy', 'sql']
   missing=['data analysis', 'data science', 'machine learning']
   skill_match%=75.0
2. Aisha Khan | score=52.76 | sim=0.5 | quality=0.6467
   matched=['data analysis', 'git', 'machine learning', 'numpy', 'pandas', 'python']
   missing=['data science', 'docker', 'nlp', 'nltk', 'spacy', 'sql']
   skill_match%=50.0
3. Rahul Sharma | score=36.51 | sim=0.2353 | quality=0.8075
   matched=['docker', 'git', 'python', 'sql']
   missing=['data analysis', 'data science', 'machine learning', 'nlp', 'nltk', 'numpy', 'pandas', 'spacy']
   skill_match%=33.33
```

*(Scores will vary slightly depending on model version and environment.)*

## Optional: Run as an API (FastAPI)
```bash
uvicorn backend.api:app --reload
```
Then open:
- `GET /health`
- `POST /rank`

## Documentation (MVBS Architecture)
### MVBS Diagram (Text)
```
Model:
  SentenceTransformers embeddings + cosine similarity
View (optional):
  FastAPI endpoints (or later: Streamlit/UI)
Business Logic:
  resume_parser -> job_parser -> matcher -> skill_gap
Storage:
  local filesystem (resumes/JDs), JSON outputs in outputs/
```

### 3–5 Slides (Text)
1) **Resume Parsing**
   - Reads PDF/DOCX/TXT and extracts contact, skills, education, experience
   - Outputs structured objects for matching

2) **Job Parsing**
   - Reads JD text and extracts required skills/education/experience
   - Normalizes skills for stable matching

3) **Matching & Ranking**
   - Embeds candidate skills vs JD skills with SentenceTransformers
   - Produces a match score and ranks candidates

4) **Skill Gap Reporting**
   - Compares candidate skills to required skills
   - Returns missing skills and match percentage

5) **Batch + Extensibility**
   - CLI supports processing many resumes per JD
   - FastAPI wrapper is ready for future UI integration

## Notes on Sample Data
This repo includes sample resumes/JDs as **TXT** so they’re easy to diff and commit.
The parser also supports **PDF** and **DOCX** for real usage.

