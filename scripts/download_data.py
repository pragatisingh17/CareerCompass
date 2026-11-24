"""Download the public job-resume CSVs used by CareerCompass.

Embeddings are kept in the download but dropped at load time.
Source: https://huggingface.co/datasets/Saharsha11/job-resume-matching
"""

from app.datasets import FILES, download


def main() -> None:
    download()
    from app.config import DATA_DIR

    for name in FILES:
        target = DATA_DIR / name
        print(f"saved {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
