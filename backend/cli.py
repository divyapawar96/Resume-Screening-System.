"""
cli.py
------
Batch processing entrypoint (backend-only).

Example:
  python -m backend.cli --resumes data/sample_resumes --jd data/sample_jds/jd_data_scientist.txt --top 3 --out outputs
"""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.job_parser import parse_job_description
from backend.matcher import matches_to_jsonable, rank_candidates
from backend.resume_parser import parse_resumes_in_dir, parsed_resumes_to_rows
from backend.utils import ensure_dir, setup_logger, write_csv_rows, write_json


logger = setup_logger()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Resume Screening & Skill Matching (Backend)")
    p.add_argument("--resumes", required=True, help="Directory containing resumes (pdf/docx/txt).")
    p.add_argument("--jd", required=True, help="Path to job description TXT file.")
    p.add_argument("--top", type=int, default=5, help="Top N candidates to output.")
    p.add_argument("--out", default="outputs", help="Output directory for JSON results.")
    p.add_argument(
        "--dump-parsed",
        action="store_true",
        help="If set, also write parsed resumes + parsed JD as JSON/CSV in the output directory.",
    )
    p.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformers model name.",
    )
    return p


def main() -> None:
    args = build_arg_parser().parse_args()

    resumes_dir = Path(args.resumes)
    jd_path = Path(args.jd)
    out_dir = ensure_dir(args.out)

    jd = parse_job_description(jd_path)
    logger.info(f"JD title: {jd.title or 'N/A'}")
    logger.info(f"JD required skills: {jd.required_skills}")

    parsed = parse_resumes_in_dir(resumes_dir)
    logger.info(f"Parsed {len(parsed)} resumes from {resumes_dir}")

    if args.dump_parsed:
        # Parsed outputs (useful for demo/evaluation)
        write_json(Path(out_dir) / "parsed_job.json", jd.to_dict())
        write_csv_rows(Path(out_dir) / "parsed_job.csv", [jd.to_dict()])

        write_json(Path(out_dir) / "parsed_resumes.json", [r.to_dict() for r in parsed])
        write_csv_rows(Path(out_dir) / "parsed_resumes.csv", parsed_resumes_to_rows(parsed))

    matches = rank_candidates(
        parsed_resumes=parsed,
        required_skills=jd.required_skills,
        required_education=jd.required_education,
        required_experience=jd.required_experience,
        top_n=args.top,
        model_name=args.model,
    )

    payload = {
        "job": {
            "title": jd.title,
            "file_path": jd.file_path,
            "required_skills": jd.required_skills,
            "required_education": jd.required_education,
            "required_experience": jd.required_experience,
        },
        "top_candidates": matches_to_jsonable(matches),
    }

    out_json = Path(out_dir) / "ranking_and_skill_gap.json"
    write_json(out_json, payload)

    # CSV exports (nice for evaluation / Excel)
    ranking_rows = []
    gap_rows = []
    for m in matches:
        ranking_rows.append(
            {
                "name": m.name,
                "resume_path": m.resume_path,
                "match_score": m.match_score,
                "semantic_similarity": m.semantic_similarity,
                "resume_quality_score": m.resume_quality_score,
                "education_boost": m.education_boost,
                "experience_boost": m.experience_boost,
                "skill_match_percentage": m.skill_gap.match_percentage,
            }
        )
        gap_rows.append(
            {
                "name": m.name,
                "matched_skills": ", ".join(m.skill_gap.matched_skills),
                "missing_skills": ", ".join(m.skill_gap.missing_skills),
                "skill_match_percentage": m.skill_gap.match_percentage,
            }
        )

    out_rank_csv = Path(out_dir) / "candidate_ranking.csv"
    out_gap_csv = Path(out_dir) / "skill_gap_report.csv"
    write_csv_rows(out_rank_csv, ranking_rows)
    write_csv_rows(out_gap_csv, gap_rows)

    logger.info(f"Wrote results: {out_json}")
    logger.info(f"Wrote CSV: {out_rank_csv}")
    logger.info(f"Wrote CSV: {out_gap_csv}")

    # Console summary (human-friendly)
    print("\n=== Top Candidates ===")
    for i, m in enumerate(matches, 1):
        print(
            f"{i}. {m.name} | score={m.match_score} | sim={m.semantic_similarity} | quality={m.resume_quality_score}"
        )
        print(f"   matched={m.skill_gap.matched_skills}")
        print(f"   missing={m.skill_gap.missing_skills}")
        print(f"   skill_match%={m.skill_gap.match_percentage}")


if __name__ == "__main__":
    main()

