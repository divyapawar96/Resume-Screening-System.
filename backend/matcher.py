"""
matcher.py
----------
Compute semantic similarity between candidate skills and job required skills
using SentenceTransformers, then rank candidates and produce top-N outputs.

We deliberately treat "skills" as short phrases. Using embeddings on a joined
string (e.g. "python sql fastapi") works well in practice and is fast.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from backend.skill_gap import SkillGapReport, generate_skill_gap
from backend.utils import normalize_text, setup_logger


logger = setup_logger()


@dataclass
class CandidateMatch:
    name: str
    resume_path: str
    match_score: float  # 0..100
    semantic_similarity: float  # 0..1
    resume_quality_score: float  # 0..1
    education_boost: float  # 0..1 (added as part of final score)
    experience_boost: float  # 0..1 (added as part of final score)
    skill_gap: SkillGapReport


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)


def _join_skills(skills: Sequence[str]) -> str:
    return " ".join([s for s in skills if s])


def _jaccard_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    """
    Lightweight fallback similarity when embeddings aren't available.
    Returns a score in [0, 1].
    """
    sa = {x.strip().lower() for x in a if x and x.strip()}
    sb = {x.strip().lower() for x in b if x and x.strip()}
    if not sa or not sb:
        return 0.0
    return len(sa.intersection(sb)) / max(len(sa.union(sb)), 1)

def _parse_required_years(required_experience: Sequence[str]) -> int:
    """
    Convert JD experience strings like:
    - "2+ years"
    - "3-5 years"
    into a conservative minimum years integer.
    """
    mins: List[int] = []
    import re

    for s in required_experience or []:
        t = normalize_text(s)
        m = None
        # 3-5 years
        m = re.search(r"\b(\d+)\s*-\s*(\d+)\s*years?\b", t)
        if m:
            mins.append(int(m.group(1)))
            continue
        # 2+ years
        m = re.search(r"\b(\d+)\s*\+\s*years?\b", t)
        if m:
            mins.append(int(m.group(1)))
            continue
        # 2 years
        m = re.search(r"\b(\d+)\s*years?\b", t)
        if m:
            mins.append(int(m.group(1)))
            continue
    return max(mins) if mins else 0


def _estimate_candidate_years(experience_items: Sequence[Any]) -> float:
    """
    Best-effort estimate of total years of experience from parsed durations.
    Handles patterns like:
    - "Jun 2022 - Present"
    - "2021 - 2023"
    Falls back to 0.0 if not available.
    """
    import datetime as _dt
    import re as _re

    if not experience_items:
        return 0.0

    now_year = _dt.datetime.now().year
    total_years = 0.0

    for ex in experience_items:
        dur = getattr(ex, "duration", None) or ""
        t = normalize_text(dur)
        if not t:
            continue

        # year span: 2021 - 2023 / 2021 - present
        m = _re.search(r"\b(19\d{2}|20\d{2})\s*[-–]\s*(19\d{2}|20\d{2}|present|current)\b", t)
        if m:
            start = int(m.group(1))
            end_raw = m.group(2)
            end = now_year if end_raw in {"present", "current"} else int(end_raw)
            if end >= start:
                total_years += float(end - start)
            continue

        # month year - month year (approx): "jun 2022 - aug 2023"
        # We'll approximate by using the year difference when present.
        years = [int(y) for y in _re.findall(r"\b(19\d{2}|20\d{2})\b", t)]
        if len(years) >= 2 and years[-1] >= years[0]:
            total_years += float(years[-1] - years[0])
            continue

    return round(min(total_years, 50.0), 2)


def _education_match_boost(candidate_education: Sequence[Any], required_education: Sequence[str]) -> float:
    """
    Simple boost:
    - If JD mentions any degree level and candidate education has any degree -> boost 1.0
    - Otherwise 0.0
    """
    if not required_education:
        return 0.0
    cand_deg = []
    for e in candidate_education or []:
        d = getattr(e, "degree", None) or ""
        cand_deg.append(normalize_text(d))
    has_cand = any(cand_deg)
    has_req = any(normalize_text(x) for x in required_education)
    return 1.0 if (has_req and has_cand) else 0.0


def compute_match_score(
    candidate_skills: Sequence[str],
    required_skills: Sequence[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Tuple[float, float]:
    """
    Returns:
    - semantic_similarity in [0,1]
    - match_score in [0,100]
    """
    cand_text = _join_skills(candidate_skills) or ""
    req_text = _join_skills(required_skills) or ""

    if not cand_text or not req_text:
        return 0.0, 0.0

    # Lazy import to keep modules lightweight unless needed.
    # If SentenceTransformers isn't installed yet, gracefully fall back to Jaccard.
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        sim = _jaccard_similarity(candidate_skills, required_skills)
        return round(sim, 4), round(sim * 100.0, 2)

    model = SentenceTransformer(model_name)

    emb = model.encode([cand_text, req_text], normalize_embeddings=False)
    sim = _cosine_sim(np.array(emb[0]), np.array(emb[1]))
    sim = max(0.0, min(1.0, sim))
    score = round(sim * 100.0, 2)
    return sim, score


def rank_candidates(
    parsed_resumes: Sequence[Any],
    required_skills: Sequence[str],
    required_education: Sequence[str] = (),
    required_experience: Sequence[str] = (),
    top_n: int = 5,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> List[CandidateMatch]:
    """
    parsed_resumes: expects objects with fields:
      - name, file_path, skills, resume_quality_score
    """
    results: List[CandidateMatch] = []
    req_years = _parse_required_years(required_experience)

    for r in parsed_resumes:
        name = (getattr(r, "name", None) or "Unknown").strip()
        resume_path = getattr(r, "file_path", "")
        skills = getattr(r, "skills", []) or []
        q = float(getattr(r, "resume_quality_score", 0.0) or 0.0)
        cand_edu = getattr(r, "education", []) or []
        cand_exp = getattr(r, "experience", []) or []

        try:
            sim, match_score = compute_match_score(
                candidate_skills=skills,
                required_skills=required_skills,
                model_name=model_name,
            )
        except Exception as e:
            logger.exception(f"Embedding match failed for {resume_path}: {e}")
            sim, match_score = 0.0, 0.0

        # Experience boost: if candidate meets/exceeds required min years.
        cand_years = _estimate_candidate_years(cand_exp)
        exp_boost = 0.0
        if req_years > 0:
            exp_boost = 1.0 if cand_years >= req_years else (cand_years / max(req_years, 1))

        # Education boost: coarse check.
        edu_boost = _education_match_boost(cand_edu, required_education)

        # Final score combines:
        # - semantic match (dominant)
        # - resume quality (completeness)
        # - edu/exp boosts (small nudges)
        final = (
            0.80 * match_score
            + 0.12 * (q * 100.0)
            + 0.05 * (edu_boost * 100.0)
            + 0.03 * (exp_boost * 100.0)
        )
        final = round(max(0.0, min(100.0, final)), 2)

        gap = generate_skill_gap(
            candidate_name=name,
            candidate_skills=skills,
            required_skills=required_skills,
        )

        results.append(
            CandidateMatch(
                name=name,
                resume_path=resume_path,
                match_score=final,
                semantic_similarity=round(sim, 4),
                resume_quality_score=round(q, 4),
                education_boost=round(float(edu_boost), 4),
                experience_boost=round(float(exp_boost), 4),
                skill_gap=gap,
            )
        )

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results[: max(1, top_n)]


def matches_to_jsonable(matches: Sequence[CandidateMatch]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in matches:
        out.append(
            {
                "name": m.name,
                "resume_path": m.resume_path,
                "match_score": m.match_score,
                "semantic_similarity": m.semantic_similarity,
                "resume_quality_score": m.resume_quality_score,
                "education_boost": m.education_boost,
                "experience_boost": m.experience_boost,
                "skill_gap": {
                    "matched_skills": m.skill_gap.matched_skills,
                    "missing_skills": m.skill_gap.missing_skills,
                    "match_percentage": m.skill_gap.match_percentage,
                },
            }
        )
    return out

