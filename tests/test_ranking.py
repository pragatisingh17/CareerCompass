from app.parsing import parse_skills
from app.ranking import jaccard, match_score, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def test_parse_skills_from_json_list():
    raw = '["Python", "PostgreSQL", "python", "FastAPI"]'
    assert parse_skills(raw) == ["python", "postgresql", "fastapi"]


def test_parse_skills_ignores_empty_cells():
    assert parse_skills(None) == []
    assert parse_skills("nan") == []


def test_jaccard_overlap():
    assert jaccard({"python", "sql"}, {"sql", "java"}) == 1 / 3
    assert jaccard(set(), {"sql"}) == 0.0


def test_match_score_prefers_shared_skills():
    close = match_score(
        candidate_skills={"python", "postgres"},
        job_skills={"python", "postgres"},
        target_position="backend engineer",
        job_title="Backend Engineer",
        candidate_category="INFORMATION-TECHNOLOGY",
        job_category="INFORMATION-TECHNOLOGY",
        candidate_years=4,
        years_required=4,
    )
    far = match_score(
        candidate_skills={"accounting"},
        job_skills={"python", "postgres"},
        target_position="accountant",
        job_title="Backend Engineer",
        candidate_category="FINANCE",
        job_category="INFORMATION-TECHNOLOGY",
        candidate_years=1,
        years_required=8,
    )
    assert close > far
    assert close > 0.9


def test_ranking_metrics():
    relevant = {2, 5}
    ranked = [2, 9, 5, 1]
    assert precision_at_k(relevant, ranked, 2) == 0.5
    assert recall_at_k(relevant, ranked, 3) == 1.0
    assert reciprocal_rank(relevant, ranked) == 1.0
    assert ndcg_at_k(relevant, ranked, 3) > 0.9
    assert precision_at_k(set(), ranked, 3) == 0.0
