"""Pure ranking helpers. These do not touch the database."""

from app.parsing import tokenize


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union)


def years_fit(candidate_years: float | None, years_required: float | None) -> float:
    if candidate_years is None or years_required is None:
        return 0.5
    gap = abs(float(candidate_years) - float(years_required))
    return max(0.0, 1.0 - gap / 10.0)


def match_score(
    *,
    candidate_skills: set[str],
    job_skills: set[str],
    target_position: str,
    job_title: str,
    candidate_category: str | None,
    job_category: str | None,
    candidate_years: float | None,
    years_required: float | None,
) -> float:
    skill = jaccard(candidate_skills, job_skills)
    title = jaccard(tokenize(target_position), tokenize(job_title))
    category = 1.0 if candidate_category and job_category and candidate_category == job_category else 0.0
    experience = years_fit(candidate_years, years_required)
    return 0.6 * skill + 0.25 * title + 0.1 * category + 0.05 * experience


def precision_at_k(relevant: set[int], ranked: list[int], k: int) -> float:
    if k <= 0:
        return 0.0
    hits = sum(1 for job_id in ranked[:k] if job_id in relevant)
    return hits / k


def recall_at_k(relevant: set[int], ranked: list[int], k: int) -> float:
    if not relevant or k <= 0:
        return 0.0
    hits = sum(1 for job_id in ranked[:k] if job_id in relevant)
    return hits / len(relevant)


def reciprocal_rank(relevant: set[int], ranked: list[int]) -> float:
    for index, job_id in enumerate(ranked, start=1):
        if job_id in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at_k(relevant: set[int], ranked: list[int], k: int) -> float:
    if not relevant or k <= 0:
        return 0.0
    dcg = 0.0
    for index, job_id in enumerate(ranked[:k], start=1):
        if job_id in relevant:
            dcg += 1.0 / _log2(index + 1)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / _log2(index + 1) for index in range(1, ideal_hits + 1))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def _log2(value: int) -> float:
    import math

    return math.log2(value)
