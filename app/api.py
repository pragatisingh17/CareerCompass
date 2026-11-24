from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Candidate, Job
from app.repository import JobHit, find_candidates, recommend_for_candidate, search_jobs, similar_jobs, rank_jobs

app = FastAPI(title="CareerCompass", version="0.1.0")


class JobOut(BaseModel):
    job_id: int
    title: str
    category: str
    description: str
    skills: list[str]
    years_required: float | None
    score: float
    overlap: list[str]


class CandidateOut(BaseModel):
    candidate_id: str
    target_position: str
    category: str
    years_experience: float | None
    skills: list[str]


class ProfileIn(BaseModel):
    skills: list[str] = Field(default_factory=list)
    target_position: str = ""
    category: str = ""
    years_experience: float | None = None
    limit: int = 10


def session_dep():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@app.get("/health")
def health(session: Session = Depends(session_dep)) -> dict[str, int | str]:
    count = session.query(Job).count()
    return {"status": "ok", "jobs": count}


@app.get("/search", response_model=list[JobOut])
def search(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    category: str | None = None,
    session: Session = Depends(session_dep),
) -> list[JobHit]:
    return search_jobs(session, q, limit=limit, category=category)


@app.get("/recommend", response_model=list[JobOut])
def recommend(
    candidate_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(session_dep),
) -> list[JobHit]:
    if session.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return recommend_for_candidate(session, candidate_id, limit=limit)


@app.post("/recommend", response_model=list[JobOut])
def recommend_profile(profile: ProfileIn, session: Session = Depends(session_dep)) -> list[JobHit]:
    return rank_jobs(
        session,
        skills={skill.strip().lower() for skill in profile.skills if skill.strip()},
        target_position=profile.target_position,
        category=profile.category,
        years_experience=profile.years_experience,
        limit=profile.limit,
    )


@app.get("/similar", response_model=list[JobOut])
def similar(
    job_id: int,
    limit: int = Query(default=8, ge=1, le=50),
    session: Session = Depends(session_dep),
) -> list[JobHit]:
    hits = similar_jobs(session, job_id, limit=limit)
    if not hits:
        exists = session.get(Job, job_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="Job not found")
    return hits


@app.get("/candidates", response_model=list[CandidateOut])
def candidates(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(session_dep),
) -> list[CandidateOut]:
    rows = find_candidates(session, q, limit=limit)
    return [
        CandidateOut(
            candidate_id=row.candidate_id,
            target_position=row.target_position or "",
            category=row.category or "",
            years_experience=row.years_experience,
            skills=list(row.skills or [])[:12],
        )
        for row in rows
    ]
