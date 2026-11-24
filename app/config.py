import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data" / "raw"
_LOCAL_DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@localhost:5432/careercompass"


def _secret_database_url() -> str | None:
    try:
        import streamlit as st

        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"])
        neon = st.secrets.get("connections", {}).get("neon", {})
        if neon.get("url"):
            return str(neon["url"])
    except Exception:
        return None
    return None


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    scheme, separator, rest = url.partition("://")
    if separator and scheme == "postgresql":
        return f"postgresql+psycopg://{rest}"
    return url


def resolve_database_url() -> str:
    url = os.getenv("DATABASE_URL") or _secret_database_url() or _LOCAL_DATABASE_URL
    return normalize_database_url(url)


DATABASE_URL = resolve_database_url()
