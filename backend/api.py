"""
api.py (optional)
-----------------
FastAPI-ready backend wrapper. This keeps UI separate while making it easy to
deploy as an API later.

Run:
  uvicorn backend.api:app --reload
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from backend.job_parser import parse_job_description
from backend.matcher import matches_to_jsonable, rank_candidates
from backend.resume_parser import parse_resumes_in_dir, parse_resume
from backend.utils import ensure_dir, setup_logger, write_text


logger = setup_logger()
app = FastAPI(title="Resume Screening & Skill Matching API", version="1.0.0")


class RankRequest(BaseModel):
    jd_path: str
    resumes_dir: str
    top_n: int = 5
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/rank")
def rank(req: RankRequest) -> dict:
    jd = parse_job_description(req.jd_path)
    resumes = parse_resumes_in_dir(req.resumes_dir)
    matches = rank_candidates(
        parsed_resumes=resumes,
        required_skills=jd.required_skills,
        top_n=req.top_n,
        model_name=req.model_name,
    )
    return {
        "job": {
            "title": jd.title,
            "file_path": jd.file_path,
            "required_skills": jd.required_skills,
        },
        "top_candidates": matches_to_jsonable(matches),
    }


@app.post("/upload/jd")
async def upload_jd(file: UploadFile = File(...)) -> dict:
    """
    Upload a JD text file and save it locally under outputs/uploads/.
    """
    uploads = ensure_dir("outputs/uploads")
    dest = Path(uploads) / file.filename
    content = (await file.read()).decode("utf-8", errors="ignore")
    write_text(dest, content)
    logger.info(f"Uploaded JD: {dest}")
    return {"saved_to": str(dest)}


@app.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    """
    Upload a resume (pdf/docx/txt) and return parsed fields immediately.
    """
    uploads = ensure_dir("outputs/uploads")
    dest = Path(uploads) / file.filename
    data = await file.read()
    dest.write_bytes(data)
    parsed = parse_resume(dest)
    return {
        "file_path": parsed.file_path,
        "name": parsed.name,
        "emails": parsed.emails,
        "phones": parsed.phones,
        "skills": parsed.skills,
        "resume_quality_score": parsed.resume_quality_score,
    }

