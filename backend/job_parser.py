"""
job_parser.py
-------------
Parse job descriptions from TXT and extract:
- Required skills
- Required education
- Required experience

Output is a structured model that downstream modules can use consistently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from backend.utils import DEFAULT_SKILL_VOCAB, normalize_skill, normalize_text, setup_logger, unique_preserve_order


logger = setup_logger()


@dataclass
class ParsedJobDescription:
    file_path: str
    title: Optional[str]
    required_skills: List[str]
    required_education: List[str]
    required_experience: List[str]
    raw_text_preview: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "title": self.title,
            "required_skills": self.required_skills,
            "required_education": self.required_education,
            "required_experience": self.required_experience,
            "raw_text_preview": self.raw_text_preview,
        }


DEFAULT_JD_SKILL_HINTS = DEFAULT_SKILL_VOCAB


def _read_txt(path: Union[str, Path]) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore").strip()


def _extract_title(text: str) -> Optional[str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return None
    # First line like "Job Title: X" or just "Data Scientist"
    m = re.match(r"^(job\s*title\s*:\s*)(.+)$", lines[0], re.I)
    if m:
        return m.group(2).strip()
    if len(lines[0]) <= 60:
        return lines[0]
    return None


def extract_required_skills(text: str, skill_hints: Optional[Sequence[str]] = None) -> List[str]:
    """
    Extract required skills from:
    - explicit "Requirements" / "Skills" section if present
    - otherwise scan whole JD for known skill hints
    """
    hints = [normalize_skill(s) for s in (skill_hints or DEFAULT_JD_SKILL_HINTS)]
    t_norm = normalize_text(text)

    # section-based parsing
    lines = [ln.strip() for ln in (text or "").splitlines()]
    req_idx = None
    for i, ln in enumerate(lines):
        ln_low = ln.lower().strip()
        if ln_low.startswith("requirements") or ln_low.startswith("required skills") or ln_low.startswith("skills"):
            req_idx = i
            break

    section_norm = ""
    if req_idx is not None:
        section = "\n".join(lines[req_idx : req_idx + 40])
        section_norm = normalize_text(section)

    found: List[str] = []

    def scan(hay: str) -> None:
        for h in hints:
            if h and re.search(rf"(^| )({re.escape(h)})( |$)", hay):
                found.append(h)

    if section_norm:
        scan(section_norm)
    else:
        scan(t_norm)

    # token extraction from bullet lists
    if req_idx is not None:
        blob = "\n".join(lines[req_idx : req_idx + 60])
        tokens = re.split(r"[,/|\n•\-\u2022]+", blob)
        for tok in tokens:
            s = normalize_skill(tok)
            if s in hints:
                found.append(s)

    return unique_preserve_order([f for f in found if f])


def extract_required_education(text: str) -> List[str]:
    t = text or ""
    out: List[str] = []
    for pat in [
        r"\b(b\.?tech|btech|be|b\.?e|bsc)\b",
        r"\b(m\.?tech|mtech|me|msc|mba)\b",
        r"\b(phd|doctorate)\b",
    ]:
        m = re.findall(pat, t, flags=re.I)
        out.extend([normalize_text(x) for x in m])
    return unique_preserve_order([o for o in out if o])


def extract_required_experience(text: str) -> List[str]:
    """
    Extract experience lines like:
    - "2+ years"
    - "3-5 years"
    """
    t = text or ""
    patterns = [
        r"\b\d+\s*\+\s*years?\b",
        r"\b\d+\s*-\s*\d+\s*years?\b",
        r"\b\d+\s*to\s*\d+\s*years?\b",
    ]
    out: List[str] = []
    for pat in patterns:
        out.extend([normalize_text(m) for m in re.findall(pat, t, flags=re.I)])
    return unique_preserve_order([o for o in out if o])


def parse_job_description(
    path: Union[str, Path],
    skill_hints: Optional[Sequence[str]] = None,
) -> ParsedJobDescription:
    p = Path(path)
    logger.info(f"Parsing JD: {p.name}")

    text = _read_txt(p)
    title = _extract_title(text)
    required_skills = extract_required_skills(text, skill_hints=skill_hints)
    required_education = extract_required_education(text)
    required_experience = extract_required_experience(text)

    preview = (text[:600] + " ...") if len(text) > 600 else text

    return ParsedJobDescription(
        file_path=str(p),
        title=title,
        required_skills=required_skills,
        required_education=required_education,
        required_experience=required_experience,
        raw_text_preview=preview,
    )

