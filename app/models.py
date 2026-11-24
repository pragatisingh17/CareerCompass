from sqlalchemy import BigInteger, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    target_position: Mapped[str] = mapped_column(Text, default="")
    resume_text: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    education_text: Mapped[str] = mapped_column(Text, default="")
    experience_text: Mapped[str] = mapped_column(Text, default="")
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str] = mapped_column(String(80), default="", index=True)
    search_document: Mapped[str] = mapped_column(TSVECTOR)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_search", "search_document", postgresql_using="gin"),
        Index("ix_jobs_skills", "skills", postgresql_using="gin"),
    )

    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), default="", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    education_text: Mapped[str] = mapped_column(Text, default="")
    years_required: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_document: Mapped[str] = mapped_column(TSVECTOR)


class Match(Base):
    __tablename__ = "matches"

    candidate_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    label_strength: Mapped[str] = mapped_column(String(32), default="", index=True)
    skill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    candidate_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
