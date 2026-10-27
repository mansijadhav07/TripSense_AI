"""Tests for the leakage-free evaluation protocol (run from repo root: pytest ml/tests)."""
import numpy as np
import pandas as pd
import pytest

from ml.evaluation import run_verified_evaluation as ev


def test_ndcg_known_values():
    assert ev.ndcg_at_k(["a", "b"], {"a"}, 10) == pytest.approx(1.0)
    assert ev.ndcg_at_k(["x", "a"], {"a"}, 10) == pytest.approx(1 / np.log2(3))
    assert ev.ndcg_at_k(["x", "y"], {"a"}, 10) == 0.0


def _frame(n_users=60, n_items=30, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(n_users * 8):
        u, i = rng.integers(n_users), rng.integers(n_items)
        rows.append(dict(user_id=f"u{u}", hotel_id=f"h{i}", overall=float(rng.integers(3, 6)),
                         post_date=f"2012-{1 + d * 12 // (n_users * 8):02d}-{1 + d % 28:02d}",
                         text="great stay" if i % 2 else "bad room",
                         cleanliness=4.0, value=4.0, location=4.0, rooms=4.0, sleep_quality=4.0))
    return pd.DataFrame(rows).drop_duplicates(["user_id", "hotel_id"])


def test_split_is_chronological_and_disjoint():
    train, test = ev.split(_frame())
    assert train["post_date"].max() <= test["post_date"].min()
    key = lambda d: set(zip(d.user_id, d.hotel_id))
    assert not key(train) & key(test)


def test_rankers_evaluable_with_recurring_items_and_exclude_seen():
    train, test = ev.split(_frame())
    diag, models = ev.evaluate_rankers(train, test)
    assert diag["evaluable_users"] > 0
    for name, m in models.items():
        assert m["status"] == "evaluated"
        assert 0.0 <= m["ndcg_at_10"] <= 1.0 and m["ndcg_at_10"] is not None


def test_not_evaluable_returns_null_not_zero():
    df = _frame()
    df["hotel_id"] = [f"unique{i}" for i in range(len(df))]  # review-id style: never recurs
    train, test = ev.split(df)
    diag, models = ev.evaluate_rankers(train, test)
    assert diag["evaluable_users"] == 0 and diag["test_reviews_with_item_in_train"] == 0.0
    for m in models.values():
        assert m["status"] == "not_evaluable" and m["ndcg_at_10"] is None


def test_text_model_beats_mean_baseline_on_signal():
    df = _frame(n_users=200, n_items=40)
    df["overall"] = np.where(df["hotel_id"].str[1:].astype(int) % 2 == 1, 5.0, 3.0)
    train, test = ev.split(df)
    r = ev.evaluate_text_model(train, test)
    assert r["rmse"] < r["baseline_global_mean_rmse"]
