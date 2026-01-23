"""
utils.py
--------
Shared utilities for file handling, normalization, logging, and safe parsing.

Design goals:
- Keep helpers small, deterministic, and unit-test friendly
- Centralize logging configuration
- Provide consistent text normalization across modules
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union


LOGGER_NAME = "resume_screening"

DEFAULT_SKILL_VOCAB: List[str] = [
    # Languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "sql",
    "nosql",
    # Web / Backend
    "fastapi",
    "flask",
    "django",
    "node.js",
    "rest api",
    "microservices",
    # Data / ML
    "pandas",
    "numpy",
    "scikit-learn",
    "machine learning",
    "deep learning",
    "data analysis",
    "data science",
    "nlp",
    "spacy",
    "nltk",
    "sentence-transformers",
    # DevOps / Cloud
    "git",
    "docker",
    "kubernetes",
    "linux",
    "aws",
    "azure",
    "gcp",
    # BI / Tools
    "excel",
    "power bi",
    "tableau",
    "streamlit",
]


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a module-wide logger.
    Safe to call multiple times (won't duplicate handlers).
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


def ensure_dir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_files(
    directory: Union[str, Path],
    extensions: Optional[Sequence[str]] = None,
) -> List[Path]:
    """
    List files under a directory. Optionally filter by extensions (case-insensitive),
    e.g. extensions=[".pdf", ".docx", ".txt"].
    """
    d = Path(directory)
    if not d.exists():
        return []

    files = [p for p in d.rglob("*") if p.is_file()]
    if not extensions:
        return files

    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    return [p for p in files if p.suffix.lower() in exts]


_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^a-z0-9\+\#\.\- ]+")


def normalize_text(text: str) -> str:
    """
    Normalize text for NLP-ish matching:
    - lower-case
    - strip noisy punctuation (keep + # . - for skills like c++, c#, node.js)
    - collapse whitespace
    """
    t = (text or "").lower()
    t = _NON_WORD_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def normalize_skill(skill: str) -> str:
    """
    Normalize a single skill token into a canonical form.
    """
    return normalize_text(skill)


def unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items:
        if it in seen:
            continue
        seen.add(it)
        out.append(it)
    return out


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """
    JSON serialize while supporting dataclasses.
    """
    def default(o: Any) -> Any:
        if is_dataclass(o):
            return asdict(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, indent=indent, ensure_ascii=False, default=default)


def write_json(path: Union[str, Path], obj: Any) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    p.write_text(safe_json_dumps(obj), encoding="utf-8")

def write_csv_rows(path: Union[str, Path], rows: List[Dict[str, Any]]) -> None:
    """
    Write a list of dict rows to CSV.
    - If `pandas` is available, it will be used for convenience.
    - Otherwise, falls back to Python's built-in csv module.
    """
    p = Path(path)
    ensure_dir(p.parent)
    if not rows:
        p.write_text("", encoding="utf-8")
        return

    try:
        import pandas as pd  # type: ignore

        pd.DataFrame(rows).to_csv(p, index=False)
        return
    except Exception:
        # pandas not available or failed; fallback to csv
        pass

    import csv

    # stable header union
    header: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in header:
                header.append(k)

    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_text(path: Union[str, Path], text: str) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    p.write_text(text, encoding="utf-8")


def read_text(path: Union[str, Path]) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def guess_name_from_email(email: str) -> Optional[str]:
    """
    Very lightweight heuristic to guess a name from an email.
    Example: divya.pawar96@gmail.com -> Divya Pawar
    """
    if not email or "@" not in email:
        return None
    local = email.split("@", 1)[0]
    local = re.sub(r"[^a-zA-Z\.]+", " ", local).strip()
    parts = [p for p in re.split(r"[ \.]+", local) if p]
    if not parts:
        return None
    return " ".join(p.capitalize() for p in parts[:2])


def extract_emails(text: str) -> List[str]:
    if not text:
        return []
    return unique_preserve_order(
        re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    )


def extract_phones(text: str) -> List[str]:
    """
    Extract phone-like patterns. Keeps it permissive for international formats.
    """
    if not text:
        return []
    candidates = re.findall(r"(\+?\d[\d\-\s\(\)]{8,}\d)", text)
    cleaned = [re.sub(r"\s+", " ", c).strip() for c in candidates]
    return unique_preserve_order(cleaned)


def score_completeness(fields_present: Dict[str, bool]) -> float:
    """
    A simple resume quality/completeness score in [0, 1].
    """
    if not fields_present:
        return 0.0
    total = len(fields_present)
    got = sum(1 for _, v in fields_present.items() if v)
    return got / max(total, 1)

