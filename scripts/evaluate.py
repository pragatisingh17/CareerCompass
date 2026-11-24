"""Offline check of profile ranking against strong_positive labels."""

import random

from sqlalchemy import select

from app.db import get_session
from app.models import Match
from app.ranking import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from app.repository import recommend_for_candidate, relevant_job_ids

SAMPLE_SIZE = 200
K = 10
RANK_DEPTH = 50


def main() -> None:
    random.seed(7)
    session = get_session()
    try:
        candidate_ids = list(
            session.scalars(
                select(Match.candidate_id)
                .where(Match.label_strength == "strong_positive")
                .distinct()
            )
        )
        if not candidate_ids:
            raise SystemExit("No labeled matches found. Load the dataset first.")
        sample = random.sample(candidate_ids, k=min(SAMPLE_SIZE, len(candidate_ids)))
        totals = {"precision": 0.0, "recall": 0.0, "ndcg": 0.0, "mrr": 0.0}
        for candidate_id in sample:
            relevant = relevant_job_ids(session, candidate_id)
            ranked = [
                hit.job_id
                for hit in recommend_for_candidate(session, candidate_id, limit=RANK_DEPTH)
            ]
            totals["precision"] += precision_at_k(relevant, ranked, K)
            totals["recall"] += recall_at_k(relevant, ranked, K)
            totals["ndcg"] += ndcg_at_k(relevant, ranked, K)
            totals["mrr"] += reciprocal_rank(relevant, ranked)
    finally:
        session.close()

    count = len(sample)
    print(f"candidates={count} k={K}")
    print(f"precision@{K} {totals['precision'] / count:.4f}")
    print(f"recall@{K} {totals['recall'] / count:.4f}")
    print(f"ndcg@{K} {totals['ndcg'] / count:.4f}")
    print(f"mrr {totals['mrr'] / count:.4f}")
