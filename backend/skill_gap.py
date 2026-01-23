"""
skill_gap.py
------------
Compute skill gap reports between:
- candidate skills (from ParsedResume)
- job required skills (from ParsedJobDescription)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Set

from backend.utils import unique_preserve_order


@dataclass
class SkillGapReport:
    candidate_name: str
    matched_skills: List[str]
    missing_skills: List[str]
    match_percentage: float  # 0..100


def _to_set(skills: Sequence[str]) -> Set[str]:
    return {s.strip().lower() for s in skills if s and s.strip()}


def generate_skill_gap(
    candidate_name: str,
    candidate_skills: Sequence[str],
    required_skills: Sequence[str],
) -> SkillGapReport:
    cand = _to_set(candidate_skills)
    req = _to_set(required_skills)

    if not req:
        return SkillGapReport(
            candidate_name=candidate_name,
            matched_skills=[],
            missing_skills=[],
            match_percentage=0.0,
        )

    matched = sorted(cand.intersection(req))
    missing = sorted(req.difference(cand))
    pct = round((len(matched) / max(len(req), 1)) * 100.0, 2)

    return SkillGapReport(
        candidate_name=candidate_name,
        matched_skills=unique_preserve_order(matched),
        missing_skills=unique_preserve_order(missing),
        match_percentage=pct,
    )

