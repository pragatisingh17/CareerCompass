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
