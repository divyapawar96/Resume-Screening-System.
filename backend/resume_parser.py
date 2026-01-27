"""
resume_parser.py
---------------
Parse resumes from PDF, DOCX, and TXT and extract structured information:
- Name, contact info, email
- Skills (keywords)
- Education (degree, institution, year)
- Work experience (role, company, duration)

This module focuses on pragmatic parsing with robust fallbacks:
- PDF: best-effort text extraction (PyPDF2)
- DOCX: paragraph extraction (python-docx)
- TXT: read directly

Note: Real-world resume parsing is messy. This implementation is modular so you
can plug in more advanced NLP models later (spaCy NER, LLM extraction, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from backend.utils import (
    DEFAULT_SKILL_VOCAB,
    extract_emails,
    extract_phones,
    guess_name_from_email,
    normalize_skill,
    normalize_text,
    score_completeness,
    setup_logger,
    unique_preserve_order,
)


logger = setup_logger()


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

@dataclass
class Education:
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


@dataclass
class Experience:
    role: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None


@dataclass
class ParsedResume:
    file_path: str
    name: Optional[str]
    emails: List[str]
    phones: List[str]
    skills: List[str]
    education: List[Education]
    experience: List[Experience]
    raw_text_preview: str
    resume_quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "name": self.name,
            "emails": self.emails,
            "phones": self.phones,
            "skills": self.skills,
            "education": [
                {"degree": e.degree, "institution": e.institution, "year": e.year} for e in (self.education or [])
            ],
            "experience": [
                {"role": x.role, "company": x.company, "duration": x.duration} for x in (self.experience or [])
            ],
            "raw_text_preview": self.raw_text_preview,
            "resume_quality_score": self.resume_quality_score,
        }


def _read_pdf(path: Path) -> str:
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError("PyPDF2 is required for PDF parsing.") from e

    reader = PdfReader(str(path))
    parts: List[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            # Some PDFs fail on certain pages; keep going.
            continue
    return "\n".join(parts).strip()


def _read_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except Exception as e:
        raise RuntimeError("python-docx is required for DOCX parsing.") from e

    doc = docx.Document(str(path))
    lines = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(lines).strip()


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def read_resume_text(path: Union[str, Path]) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported resume format: {ext}. Supported: {sorted(SUPPORTED_EXTENSIONS)}")

    if ext == ".pdf":
        return _read_pdf(p)
    if ext == ".docx":
        return _read_docx(p)
    return _read_txt(p)


def _extract_name(text: str, emails: List[str]) -> Optional[str]:
    """
    Heuristic:
    - First non-empty line with mostly letters and <= 4 words
    - Otherwise fall back to email-based guess
    """
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    for ln in lines[:8]:
        if len(ln) > 60:
            continue
        if re.search(r"\d", ln):
            continue
        words = re.findall(r"[A-Za-z]+", ln)
        if 2 <= len(words) <= 4 and sum(len(w) for w in words) >= 6:
            return " ".join(w.capitalize() for w in words)

    if emails:
        return guess_name_from_email(emails[0])
    return None


def _extract_section(text: str, header_keywords: Sequence[str]) -> str:
    """
    Extract a rough section by headers. Best-effort and format-agnostic.
    """
    t = text or ""
    lines = [ln.rstrip() for ln in t.splitlines()]
    headers = [hk.lower() for hk in header_keywords]

    idxs: List[int] = []
    for i, ln in enumerate(lines):
        ln_low = ln.strip().lower()
        if any(ln_low.startswith(h) for h in headers):
            idxs.append(i)

    if not idxs:
        return ""

    start = idxs[0] + 1
    end = len(lines)
    # stop at next likely header
    for j in range(start, len(lines)):
        ln_low = lines[j].strip().lower()
        if re.fullmatch(r"[a-z &/]{3,40}", ln_low) and any(
            kw in ln_low for kw in ["experience", "education", "skills", "projects", "summary", "certifications"]
        ):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def extract_skills(text: str, skill_vocab: Optional[Sequence[str]] = None) -> List[str]:
    """
    Extract skills using a hybrid approach:
    - If a SKILLS section exists, parse it aggressively
    - Else: scan whole resume for known vocab terms

    Returns normalized unique skills.
    """
    vocab = [normalize_skill(s) for s in (skill_vocab or DEFAULT_SKILL_VOCAB)]
    t_norm = normalize_text(text)

    skills_section = _extract_section(text, ["skills", "technical skills", "skills & tools"])
    section_norm = normalize_text(skills_section)

    found: List[str] = []

    def scan(hay: str) -> None:
        for v in vocab:
            if not v:
                continue
            # word-ish boundary match, but allow dots and plus signs
            if re.search(rf"(^| )({re.escape(v)})( |$)", hay):
                found.append(v)

    if section_norm:
        scan(section_norm)
    else:
        scan(t_norm)

    # also parse comma/bullet tokens from skills section if present
    if skills_section:
        tokens = re.split(r"[,/|\n•\-\u2022]+", skills_section)
        for tok in tokens:
            s = normalize_skill(tok)
            if len(s) >= 2 and s in vocab:
                found.append(s)

    return unique_preserve_order([f for f in found if f])


def extract_education(text: str) -> List[Education]:
    section = _extract_section(text, ["education", "academics"])
    blob = section if section else text
    blob = blob.replace("\t", " ")

    edu_list: List[Education] = []
    # common degrees
    deg_re = re.compile(r"\b(b\.?tech|btech|be|b\.?e|bsc|m\.?tech|mtech|me|msc|mba|phd)\b", re.I)
    year_re = re.compile(r"\b(19\d{2}|20\d{2})\b")

    lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]
    for ln in lines:
        if not deg_re.search(ln) and "university" not in ln.lower() and "college" not in ln.lower():
            continue
        degree = deg_re.search(ln).group(0) if deg_re.search(ln) else None
        year = year_re.search(ln).group(0) if year_re.search(ln) else None
        institution = None
        # naive: institution is text after '-' or ',' if present
        if "-" in ln:
            parts = [p.strip() for p in ln.split("-", 1)]
            if len(parts) == 2:
                institution = parts[1]
        elif "," in ln:
            parts = [p.strip() for p in ln.split(",", 1)]
            if len(parts) == 2:
                institution = parts[1]

        edu_list.append(Education(degree=degree, institution=institution, year=year))

    return edu_list


def extract_experience(text: str) -> List[Experience]:
    section = _extract_section(text, ["experience", "work experience", "professional experience"])
    blob = section if section else text
    lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]

    exp_list: List[Experience] = []
    # role @ company | role - company
    pat = re.compile(r"^(?P<role>.+?)\s*(?:@|-)\s*(?P<company>.+?)(?:\s*\|\s*(?P<duration>.+))?$")
    dur_re = re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b", re.I)
    year_span_re = re.compile(r"\b(20\d{2}|19\d{2})\s*[-–]\s*(20\d{2}|present|current)\b", re.I)

    for ln in lines:
        m = pat.match(ln)
        if m:
            exp_list.append(
                Experience(
                    role=m.group("role").strip(),
                    company=m.group("company").strip(),
                    duration=(m.group("duration") or "").strip() or None,
                )
            )
            continue

        # duration-only lines (e.g. "Jun 2022 - Present")
        if dur_re.search(ln) or year_span_re.search(ln):
            if exp_list and not exp_list[-1].duration:
                exp_list[-1].duration = ln

    return exp_list


def parse_resume(
    path: Union[str, Path],
    skill_vocab: Optional[Sequence[str]] = None,
) -> ParsedResume:
    p = Path(path)
    logger.info(f"Parsing resume: {p.name}")

    text = read_resume_text(p)
    emails = extract_emails(text)
    phones = extract_phones(text)
    name = _extract_name(text, emails)
    skills = extract_skills(text, skill_vocab=skill_vocab)
    education = extract_education(text)
    experience = extract_experience(text)

    fields_present = {
        "name": bool(name),
        "email": bool(emails),
        "phone": bool(phones),
        "skills": bool(skills),
        "education": bool(education),
        "experience": bool(experience),
    }

    # Resume Quality Score: completeness + relevance proxy (skills count)
    completeness = score_completeness(fields_present)
    relevance = min(len(skills) / 20.0, 1.0)  # cap at 20 skills
    quality = round(0.65 * completeness + 0.35 * relevance, 4)

    preview = (text[:600] + " ...") if len(text) > 600 else text

    return ParsedResume(
        file_path=str(p),
        name=name,
        emails=emails,
        phones=phones,
        skills=skills,
        education=education,
        experience=experience,
        raw_text_preview=preview,
        resume_quality_score=quality,
    )


def parse_resumes_in_dir(
    resumes_dir: Union[str, Path],
    skill_vocab: Optional[Sequence[str]] = None,
    extensions: Optional[Sequence[str]] = (".pdf", ".docx", ".txt"),
    max_workers: int = 4,
) -> List[ParsedResume]:
    from backend.utils import list_files
    from concurrent.futures import ThreadPoolExecutor

    files = list_files(resumes_dir, extensions=extensions)
    if not files:
        return []

    logger.info(f"Parsing {len(files)} resumes in parallel (workers={max_workers})...")
    
    parsed: List[ParsedResume] = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map each file parsing to a thread
        future_to_file = {executor.submit(parse_resume, fp, skill_vocab): fp for fp in files}
        
        from concurrent.futures import as_completed
        for future in as_completed(future_to_file):
            fp = future_to_file[future]
            try:
                data = future.result()
                parsed.append(data)
            except Exception as e:
                logger.exception(f"Failed to parse resume {fp.name}: {e}")
                
    return parsed


def parsed_resumes_to_rows(parsed_resumes: Sequence[ParsedResume]) -> List[Dict[str, Any]]:
    """
    Flatten parsed resumes into CSV-friendly rows.
    """
    rows: List[Dict[str, Any]] = []
    for r in parsed_resumes:
        rows.append(
            {
                "file_path": r.file_path,
                "name": r.name,
                "emails": ", ".join(r.emails),
                "phones": ", ".join(r.phones),
                "skills": ", ".join(r.skills),
                "education": "; ".join(
                    [
                        " | ".join([x for x in [e.degree, e.institution, e.year] if x])
                        for e in (r.education or [])
                    ]
                ),
                "experience": "; ".join(
                    [
                        " | ".join([x for x in [ex.role, ex.company, ex.duration] if x])
                        for ex in (r.experience or [])
                    ]
                ),
                "resume_quality_score": r.resume_quality_score,
            }
        )
    return rows

