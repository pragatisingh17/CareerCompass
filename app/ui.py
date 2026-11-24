import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_session
from app.repository import find_candidates, recommend_for_candidate, search_jobs, similar_jobs

st.set_page_config(page_title="CareerCompass", layout="wide")
st.title("CareerCompass")
st.caption("Search jobs by keywords, or rank them against a candidate profile.")


def render_job(session, hit, key_prefix: str) -> None:
    with st.container(border=True):
        st.subheader(hit.title)
        meta = " · ".join(part for part in [hit.category, f"score {hit.score}"] if part)
        st.caption(meta)
        st.write(hit.description)
        if hit.overlap:
            st.write("Shared skills: " + ", ".join(hit.overlap[:12]))
        if st.button("Similar jobs", key=f"{key_prefix}-{hit.job_id}"):
            related = similar_jobs(session, hit.job_id, limit=5)
            for item in related:
                st.write(f"{item.title} ({item.category}) — {item.score}")


mode = st.sidebar.radio("Mode", ["Search", "Recommend"])
limit = st.sidebar.slider("Results", min_value=5, max_value=20, value=10)

try:
    session = get_session()
    session.execute(text("SELECT 1"))
except SQLAlchemyError as exc:
    st.error(f"Could not connect to Postgres. Start the database, then reload. {exc}")
    st.stop()

try:
    if mode == "Search":
        query = st.text_input("Job search", placeholder="python backend postgres")
        if query.strip():
            hits = search_jobs(session, query, limit=limit)
            if not hits:
                st.info("No jobs matched that query.")
            for hit in hits:
                render_job(session, hit, "search")
    else:
        query = st.text_input("Find a profile", placeholder="data scientist or cand_00001")
        if query.strip():
            people = find_candidates(session, query, limit=15)
            if not people:
                st.info("No profiles matched.")
            else:
                labels = {
                    f"{person.candidate_id} — {person.target_position}": person.candidate_id
                    for person in people
                }
                choice = st.selectbox("Profile", list(labels))
                person = next(person for person in people if person.candidate_id == labels[choice])
                st.write(person.target_position)
                st.write(", ".join((person.skills or [])[:16]))
                hits = recommend_for_candidate(session, person.candidate_id, limit=limit)
                for hit in hits:
                    render_job(session, hit, "recommend")
finally:
    session.close()
