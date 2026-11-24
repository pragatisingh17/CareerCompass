"""Public job and resume files used to fill an empty database."""

from urllib.request import urlretrieve

from app.config import DATA_DIR

FILES = {
    "cv.csv": "https://huggingface.co/datasets/Saharsha11/job-resume-matching/resolve/main/cv.csv",
    "job.csv": "https://huggingface.co/datasets/Saharsha11/job-resume-matching/resolve/main/job.csv",
    "matches.csv": "https://huggingface.co/datasets/Saharsha11/job-resume-matching/resolve/main/matches.csv",
}


def download(names: tuple[str, ...] | None = None) -> None:
    selected = names or tuple(FILES)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in selected:
        target = DATA_DIR / name
        if target.exists() and target.stat().st_size > 0:
            continue
        urlretrieve(FILES[name], target)
