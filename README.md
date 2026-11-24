# CareerCompass

Job search and profile matching. Keyword search runs in Postgres. Recommendations rank jobs by skill overlap, title similarity, category, and years of experience.

The first dataset is the public [job-resume-matching](https://huggingface.co/datasets/Saharsha11/job-resume-matching) release: about 1,167 jobs, 9,544 profiles, and labeled candidate-job matches. Precomputed embeddings are left out of v1.

## Run Postgres

Docker:

```powershell
docker compose up -d
copy .env.example .env
```

The default URL is `postgresql+psycopg://careercompass:careercompass@localhost:5432/careercompass`.

## Load data and start the app

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -3 scripts/download_data.py
py -3 scripts/load_postgres.py
py -3 scripts/evaluate.py
uvicorn app.api:app --reload
streamlit run app/ui.py
```

API routes:

- `GET /search?q=python backend`
- `GET /recommend?candidate_id=cand_00001`
- `POST /recommend` with a skill list
- `GET /similar?job_id=1`
- `GET /candidates?q=data scientist`

`load_postgres.py` drops and recreates the tables before each load.

## Live demo

The public app runs on [Streamlit Community Cloud](https://share.streamlit.io) and reads a hosted Postgres database. Search uses Postgres full-text search, so the demo cannot run from a file database.

1. Create a free project at [Neon](https://neon.tech). Copy the connection string. It looks like `postgresql://USER:PASSWORD@HOST/neondb?sslmode=require`.
2. Open https://share.streamlit.io and sign in with GitHub as `pragatisingh17`.
3. Create an app from https://github.com/pragatisingh17/CareerCompass/blob/main/streamlit_app.py on branch `main`.
4. In Advanced settings, set Python to 3.12 and paste this secret, using the Neon string:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/neondb?sslmode=require"
```

5. Deploy. The app URL is on `streamlit.app`. The first open downloads the public job and profile files into Neon. Later visits only query that database.

Do not commit the Neon password. Streamlit stores that secret in the app settings, not in git.
