import re

from sqlalchemy.dialects import postgresql

from app.repository import search_jobs


class _Result:
    def all(self):
        return []


class _Session:
    def __init__(self):
        self.statement = None

    def execute(self, statement):
        self.statement = statement
        return _Result()


def test_search_jobs_binds_text_search_config_as_regconfig():
    session = _Session()
    assert search_jobs(session, " python backend ", limit=10) == []

    compiled = session.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "ts_rank_cd(jobs.search_document, websearch_to_tsquery(" in sql
    assert "jobs.search_document @@ websearch_to_tsquery(" in sql
    assert re.search(
        r"websearch_to_tsquery\(%\([^)]+\)s::REGCONFIG, %\([^)]+\)s",
        sql,
    )
    assert not re.search(r"websearch_to_tsquery\(\s*%\([^)]+\)s::VARCHAR", sql)
    assert "english" in compiled.params.values()
    assert "python OR backend" in compiled.params.values()


def test_search_jobs_ors_each_word():
    session = _Session()
    search_jobs(session, "python backend")
    compiled = session.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    values = list(compiled.params.values())
    assert "python OR backend" in values
    assert "python backend" not in values
    assert "ts_rank_cd(jobs.search_document, websearch_to_tsquery(" in sql
    assert re.search(
        r"websearch_to_tsquery\(%\([^)]+\)s::REGCONFIG, %\([^)]+\)s",
        sql,
    )

    session = _Session()
    search_jobs(session, "  python,   backend sql ")
    compiled = session.statement.compile(dialect=postgresql.dialect())
    assert "python OR backend OR sql" in list(compiled.params.values())


def test_search_jobs_skips_blank_query():
    session = _Session()
    assert search_jobs(session, "   ") == []
    assert session.statement is None
