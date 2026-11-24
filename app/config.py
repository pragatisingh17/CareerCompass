import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://careercompass:careercompass@localhost:5432/careercompass",
)
DATA_DIR = ROOT / "data" / "raw"
