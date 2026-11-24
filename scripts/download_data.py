"""Download the public job-resume CSVs used by CareerCompass.

Embeddings are kept in the download but dropped at load time.
Source: https://huggingface.co/datasets/Saharsha11/job-resume-matching
"""

from urllib.request import urlretrieve

from app.config import DATA_DIR

FILES = {
    "cv.csv": "https://huggingface.co/datasets/Saharsha11/job-resume-matching/resolve/main/cv.csv",
    "job.csv": "https://huggingface.co/datasets/Saharsha11/job-resume-matching/resolve/main/job.csv",
    "matches.csv": "https://huggingface.co/datasets/Saharsha11/job-resume-matching/resolve/main/matches.csv",
}


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        target = DATA_DIR / name
        if target.exists() and target.stat().st_size > 0:
            print(f"skip {target}")
            continue
        print(f"download {name}")
        urlretrieve(url, target)
        print(f"saved {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
