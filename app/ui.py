import html
from pathlib import Path

import streamlit as st
from sqlalchemy import text

from app.db import get_session
from app.repository import find_candidates, recommend_for_candidate, search_jobs, similar_jobs
from scripts.load_postgres import load_if_empty

_THEME = Path(__file__).resolve().parent / "theme.css"


def render() -> None:
    st.set_page_config(page_title="CareerCompass", layout="wide")
    st.html(_THEME)
    _header()
    mode, limit = _sidebar()

    try:
        with st.spinner("Opening the catalog. The first visit takes a little longer."):
            load_if_empty()
        session = get_session()
        session.execute(text("SELECT 1"))
    except Exception as exc:
        _notice(_public_error(exc))
        st.stop()
        return

    try:
        if mode == "Search":
            _render_search(session, limit)
        else:
            _render_recommend(session, limit)
    except Exception as exc:
        if exc.__class__.__name__ in {"StopException", "RerunException"}:
            raise
        _notice("That lookup did not complete. Try again in a moment.")
    finally:
        session.close()


def render_job(session, hit, key_prefix: str) -> None:
    category = (hit.category or "").strip()
    meta = []
    if category:
        meta.append(f'<span class="cc-cat">{_esc(category)}</span>')
    meta.append(f'<span class="cc-score" title="Score">{hit.score:.3f}</span>')
    description = ""
    if hit.description:
        description = f'<p class="cc-job-desc">{_esc(hit.description)}</p>'
    skills = _chips(list(hit.overlap or [])[:12])
    skill_block = f'<p class="cc-label">Shared skills</p>{skills}' if skills else ""
    with st.container(border=True, key=f"job-{key_prefix}-{hit.job_id}"):
        st.html(
            f'<div class="cc-job-top">'
            f'<h2 class="cc-job-title">{_esc(hit.title)}</h2>'
            f'<div class="cc-job-meta">{"".join(meta)}</div>'
            f"</div>"
            f"{description}"
            f"{skill_block}"
        )
        if st.button("Similar jobs", key=f"{key_prefix}-{hit.job_id}"):
            related = similar_jobs(session, hit.job_id, limit=5)
            if not related:
                st.html('<p class="cc-empty">No similar roles turned up.</p>')
            else:
                rows = []
                for item in related:
                    cat = (item.category or "").strip()
                    cat_html = f'<span class="cc-sim-meta">{_esc(cat)}</span>' if cat else ""
                    rows.append(
                        "<li>"
                        f'<span class="cc-sim-main"><span class="cc-sim-title">{_esc(item.title)}</span>{cat_html}</span>'
                        f'<span class="cc-score" title="Score">{item.score:.3f}</span>'
                        "</li>"
                    )
                st.html(
                    '<p class="cc-label">Similar roles</p>'
                    f'<ul class="cc-similar">{"".join(rows)}</ul>'
                )


def _render_search(session, limit: int) -> None:
    with st.container(border=True, key="composer"):
        query = st.text_input("Job search", placeholder="python backend postgres")
    if not query.strip():
        _empty("Enter keywords to search the catalog.")
        return
    hits = search_jobs(session, query, limit=limit)
    _render_hits(session, hits, "search", "No jobs matched that query.")


def _render_recommend(session, limit: int) -> None:
    with st.container(border=True, key="composer"):
        query = st.text_input("Find a profile", placeholder="data scientist or cand_00001")
        people = find_candidates(session, query, limit=15) if query.strip() else []
        person = None
        if people:
            labels = {
                f"{item.candidate_id} — {item.target_position}": item.candidate_id
                for item in people
            }
            choice = st.selectbox("Profile", list(labels))
            person = next(item for item in people if item.candidate_id == labels[choice])
    if not query.strip():
        _empty("Enter a role or a profile id.")
        return
    if person is None:
        _empty("No profiles matched.")
        return
    _profile(person)
    hits = recommend_for_candidate(session, person.candidate_id, limit=limit)
    _render_hits(session, hits, "recommend", "No roles ranked for this profile.")


def _render_hits(session, hits, key_prefix: str, empty: str) -> None:
    if not hits:
        _empty(empty)
        return
    noun = "role" if len(hits) == 1 else "roles"
    st.html(f'<p class="cc-count">{len(hits)} {noun}</p>')
    for hit in hits:
        render_job(session, hit, key_prefix)


def _profile(person) -> None:
    title = person.target_position or person.candidate_id
    skills = _chips(list(person.skills or [])[:16])
    skill_block = f'<p class="cc-label">Skills</p>{skills}' if skills else ""
    st.html(
        '<section class="cc-profile">'
        f'<p class="cc-label">{_esc(person.candidate_id)}</p>'
        f'<h2 class="cc-job-title">{_esc(title)}</h2>'
        f"{skill_block}"
        "</section>"
    )


def _header() -> None:
    st.html(
        """
        <header class="cc-header">
          <h1>CareerCompass</h1>
          <div class="cc-rule"></div>
          <p class="cc-lede">Search jobs by keyword, or match them to a candidate profile.</p>
        </header>
        """
    )


def _sidebar() -> tuple[str, int]:
    with st.sidebar:
        st.html(
            """
            <div class="cc-brand">
              <span class="cc-mark">CC</span>
              <span>
                <span class="cc-brand-name">CareerCompass</span>
                <span class="cc-brand-note">Search and match</span>
              </span>
            </div>
            """
        )
        mode = st.radio("Mode", ["Search", "Recommend"])
        limit = st.slider("Results", min_value=5, max_value=20, value=10)
        st.html(
            '<p class="cc-side-help">Search looks up roles by keyword. '
            "Recommend ranks roles for one profile.</p>"
        )
    return mode, limit


def _chips(items: list[str]) -> str:
    chips = []
    for item in items:
        text_value = str(item).strip()
        if text_value:
            chips.append(f'<span class="cc-chip">{_esc(text_value)}</span>')
    if not chips:
        return ""
    return f'<div class="cc-chips">{"".join(chips)}</div>'


def _empty(message: str) -> None:
    st.html(f'<p class="cc-empty">{_esc(message)}</p>')


def _notice(message: str) -> None:
    st.html(f'<p class="cc-warn">{_esc(message)}</p>')


def _public_error(exc: Exception) -> str:
    raw = str(exc).strip()
    line = raw.splitlines()[0].strip() if raw else ""
    lowered = line.lower()
    leaked = (
        "select ",
        "insert ",
        "update ",
        "delete ",
        "traceback",
        "psycopg",
        "sqlalchemy",
        "programmingerror",
        "[sql",
        "syntax error",
    )
    if not line or len(line) > 160 or any(token in lowered for token in leaked):
        return "The catalog is unavailable right now. Try again in a moment."
    return f"The catalog is unavailable right now. {line}"


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)
