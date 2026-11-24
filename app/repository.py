from dataclasses import dataclass

from sqlalchemy import func, literal, select
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.orm import Session

from app.models import Candidate, Job, Match
from app.ranking import jaccard, match_score


@dataclass
class JobHit:
    job_id: int
    title: str
    category: str
    description: str
    skills: list[str]
    years_required: float | None
    score: float
    overlap: list[str]


def search_jobs(session: Session, query: str, limit: int = 10, category: str | None = None) -> list[JobHit]:
    query = query.strip()
    if not query:
        return []
    # literal("english") alone binds as VARCHAR, and Postgres has no
    # websearch_to_tsquery(varchar, varchar). The config must be regconfig.
    tsquery = func.websearch_to_tsquery(literal("english", type_=REGCONFIG), query)
    rank = func.ts_rank_cd(Job.search_document, tsquery)
    stmt = select(Job, rank).where(Job.search_document.bool_op("@@")(tsquery))
    if category:
        stmt = stmt.where(Job.category == category)
    rows = session.execute(stmt.order_by(rank.desc()).limit(limit)).all()
    return [_job_hit(job, float(score or 0.0), []) for job, score in rows]


def recommend_for_candidate(session: Session, candidate_id: str, limit: int = 10) -> list[JobHit]:
    candidate = session.get(Candidate, candidate_id)
    if candidate is None:
        return []
    return rank_jobs(
        session,
        skills=set(candidate.skills or []),
        target_position=candidate.target_position or "",
        category=candidate.category or "",
        years_experience=candidate.years_experience,
        limit=limit,
    )


def similar_jobs(session: Session, job_id: int, limit: int = 8) -> list[JobHit]:
    source = session.get(Job, job_id)
    if source is None:
        return []
    source_skills = set(source.skills or [])
    jobs = session.scalars(select(Job).where(Job.job_id != job_id)).all()
    scored: list[JobHit] = []
    for job in jobs:
        skills = set(job.skills or [])
        score = jaccard(source_skills, skills)
        if job.category and job.category == source.category:
            score += 0.05
        if score <= 0:
            continue
        scored.append(_job_hit(job, score, sorted(source_skills & skills)))
    scored.sort(key=lambda hit: hit.score, reverse=True)
    return scored[:limit]


def find_candidates(session: Session, query: str, limit: int = 20) -> list[Candidate]:
    pattern = f"%{query.strip()}%"
    stmt = (
        select(Candidate)
        .where(Candidate.target_position.ilike(pattern) | Candidate.candidate_id.ilike(pattern))
        .order_by(Candidate.candidate_id)
        .limit(limit)
    )
    return list(session.scalars(stmt))


def relevant_job_ids(session: Session, candidate_id: str) -> set[int]:
    stmt = select(Match.job_id).where(
        Match.candidate_id == candidate_id,
        Match.label_strength == "strong_positive",
    )
    return set(session.scalars(stmt))


def rank_jobs(
    session: Session,
    *,
    skills: set[str],
    target_position: str,
    category: str,
    years_experience: float | None,
    limit: int,
) -> list[JobHit]:
    jobs = session.scalars(select(Job)).all()
    scored: list[JobHit] = []
    for job in jobs:
        job_skills = set(job.skills or [])
        score = match_score(
            candidate_skills=skills,
            job_skills=job_skills,
            target_position=target_position,
            job_title=job.title or "",
            candidate_category=category,
            job_category=job.category,
            candidate_years=years_experience,
            years_required=job.years_required,
        )
        if score <= 0:
            continue
        scored.append(_job_hit(job, score, sorted(skills & job_skills)))
    scored.sort(key=lambda hit: hit.score, reverse=True)
    return scored[:limit]


def _job_hit(job: Job, score: float, overlap: list[str]) -> JobHit:
    description = job.description or ""
    if len(description) > 420:
        description = description[:417].rstrip() + "..."
    return JobHit(
        job_id=job.job_id,
        title=job.title or "Untitled role",
        category=job.category or "",
        description=description,
        skills=list(job.skills or []),
        years_required=job.years_required,
        score=round(score, 4),
        overlap=overlap,
    )
