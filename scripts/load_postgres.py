"""Load CareerCompass CSVs into Postgres.

Replaces existing rows. Run scripts/download_data.py first.
"""

import math

import pandas as pd
from sqlalchemy import text

from app.config import DATA_DIR
from app.datasets import download
from app.db import engine
from app.models import Base
from app.parsing import parse_skills

JOB_COLUMNS = [
    "job_id",
    "job_title",
    "category",
    "job_description",
    "clean_skills_json",
    "education_text",
    "years_required",
]
CANDIDATE_COLUMNS = [
    "candidate_id",
    "target_position",
    "resume_text",
    "clean_skills_json",
    "education_text",
    "experience_text",
    "years_experience",
    "inferred_category",
]
MATCH_COLUMNS = [
    "candidate_id",
    "job_id",
    "final_score",
    "label_strength",
    "skill_score",
    "semantic_score",
    "candidate_rank",
]


def load_if_empty() -> bool:
    """Create tables and load jobs plus profiles when the database has no jobs.

    Returns True when this call inserted the dataset. Match labels stay out of
    this path; scripts/load_postgres.py still loads them for local evaluation.
    """
    Base.metadata.create_all(engine)
    with engine.connect() as connection:
        job_count = connection.execute(text("SELECT COUNT(*) FROM jobs")).scalar_one()
    if job_count:
        return False

    # Recreate empty tables so a failed first load cannot leave job_id as a 32-bit integer.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    download(("job.csv", "cv.csv"))
    jobs = pd.read_csv(DATA_DIR / "job.csv", usecols=JOB_COLUMNS)
    candidates = pd.read_csv(DATA_DIR / "cv.csv", usecols=CANDIDATE_COLUMNS)
    with engine.begin() as connection:
        _insert_jobs(connection, jobs)
        _insert_candidates(connection, candidates)
    return True


def main() -> None:
    for name in ("job.csv", "cv.csv", "matches.csv"):
        if not (DATA_DIR / name).exists():
            raise SystemExit(f"Missing {DATA_DIR / name}. Run scripts/download_data.py first.")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    jobs = pd.read_csv(DATA_DIR / "job.csv", usecols=JOB_COLUMNS)
    candidates = pd.read_csv(DATA_DIR / "cv.csv", usecols=CANDIDATE_COLUMNS)
    matches = pd.read_csv(DATA_DIR / "matches.csv", usecols=MATCH_COLUMNS)

    with engine.begin() as connection:
        _insert_jobs(connection, jobs)
        _insert_candidates(connection, candidates)
        _insert_matches(connection, matches)
        job_count = connection.execute(text("SELECT COUNT(*) FROM jobs")).scalar_one()
        candidate_count = connection.execute(text("SELECT COUNT(*) FROM candidates")).scalar_one()
        match_count = connection.execute(text("SELECT COUNT(*) FROM matches")).scalar_one()
    print(f"loaded jobs={job_count} candidates={candidate_count} matches={match_count}")


def _insert_jobs(connection, frame: pd.DataFrame) -> None:
    statement = text(
        """
        INSERT INTO jobs (
            job_id, title, category, description, skills, education_text, years_required, search_document
        ) VALUES (
            :job_id, :title, :category, :description, :skills, :education_text, :years_required,
            to_tsvector('english', :document)
        )
        """
    )
    rows = []
    for record in frame.to_dict(orient="records"):
        skills = parse_skills(record.get("clean_skills_json"))
        title = _text(record.get("job_title"))
        description = _text(record.get("job_description"))
        rows.append(
            {
                "job_id": int(record["job_id"]),
                "title": title,
                "category": _text(record.get("category")),
                "description": description,
                "skills": skills,
                "education_text": _text(record.get("education_text")),
                "years_required": _number(record.get("years_required")),
                "document": " ".join([title, description, " ".join(skills)]),
            }
        )
    connection.execute(statement, rows)


def _insert_candidates(connection, frame: pd.DataFrame) -> None:
    statement = text(
        """
        INSERT INTO candidates (
            candidate_id, target_position, resume_text, skills, education_text,
            experience_text, years_experience, category, search_document
        ) VALUES (
            :candidate_id, :target_position, :resume_text, :skills, :education_text,
            :experience_text, :years_experience, :category, to_tsvector('english', :document)
        )
        """
    )
    rows = []
    for record in frame.to_dict(orient="records"):
        skills = parse_skills(record.get("clean_skills_json"))
        position = _text(record.get("target_position"))
        resume = _text(record.get("resume_text"))
        rows.append(
            {
                "candidate_id": str(record["candidate_id"]),
                "target_position": position,
                "resume_text": resume,
                "skills": skills,
                "education_text": _text(record.get("education_text")),
                "experience_text": _text(record.get("experience_text")),
                "years_experience": _number(record.get("years_experience")),
                "category": _text(record.get("inferred_category")),
                "document": " ".join([position, " ".join(skills), resume[:4000]]),
            }
        )
    connection.execute(statement, rows)


def _insert_matches(connection, frame: pd.DataFrame) -> None:
    statement = text(
        """
        INSERT INTO matches (
            candidate_id, job_id, final_score, label_strength, skill_score, semantic_score, candidate_rank
        )
        SELECT :candidate_id, :job_id, :final_score, :label_strength, :skill_score, :semantic_score, :candidate_rank
        WHERE EXISTS (SELECT 1 FROM candidates WHERE candidate_id = :candidate_id)
          AND EXISTS (SELECT 1 FROM jobs WHERE job_id = :job_id)
        """
    )
    rows = [
        {
            "candidate_id": str(record["candidate_id"]),
            "job_id": int(record["job_id"]),
            "final_score": _number(record.get("final_score")),
            "label_strength": _text(record.get("label_strength")),
            "skill_score": _number(record.get("skill_score")),
            "semantic_score": _number(record.get("semantic_score")),
            "candidate_rank": _int(record.get("candidate_rank")),
        }
        for record in frame.to_dict(orient="records")
    ]
    connection.execute(statement, rows)


def _text(value: object) -> str:
    if _missing(value):
        return ""
    return str(value)


def _number(value: object) -> float | None:
    if _missing(value):
        return None
    return float(value)


def _int(value: object) -> int | None:
    number = _number(value)
    if number is None:
        return None
    return int(number)


def _missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


if __name__ == "__main__":
    main()
