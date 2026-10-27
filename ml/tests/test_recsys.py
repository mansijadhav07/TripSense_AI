"""
Tests of the data generator, the leakage guarantees and the model core.
Runs on a small freshly generated dataset (fast), plus sanity checks on the shipped evaluation report.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml" / "scripts"))

from generate_synthetic_dataset import generate  # noqa: E402
from ml.recsys.core import (  # noqa: E402
    CFModel, ContentModel, Recommender, SentimentModel, per_user_chronological_split, rating_to_label)


@pytest.fixture(scope="module")
def small():
    reviews, catalog = generate(n_hotels=60, n_users=300, min_reviews=10, max_reviews=20, seed=7)
    train, test = per_user_chronological_split(reviews)
    return reviews, catalog, train, test


def test_generation_is_reproducible():
    a, _ = generate(n_hotels=30, n_users=50, min_reviews=5, max_reviews=8, seed=3)
    b, _ = generate(n_hotels=30, n_users=50, min_reviews=5, max_reviews=8, seed=3)
    c, _ = generate(n_hotels=30, n_users=50, min_reviews=5, max_reviews=8, seed=4)
    assert a.equals(b) and not a.equals(c)


def test_dataset_has_repeated_ids_and_valid_ranges(small):
    reviews, catalog, *_ = small
    assert reviews.groupby("hotel_id").size().min() > 1            # multiple reviews per hotel
    assert reviews.groupby("user_id").size().min() >= 10          # multiple interactions per user
    assert set(reviews["hotel_id"]) <= set(catalog["hotel_id"])
    assert reviews["overall"].between(1, 5).all()
    assert reviews.duplicated(["user_id", "hotel_id"]).sum() == 0
    assert reviews["review_text"].str.len().min() > 20


def test_split_has_no_leakage(small):
    _, _, train, test = small
    assert not (set(zip(train.user_id, train.hotel_id)) & set(zip(test.user_id, test.hotel_id)))
    assert not (set(train.review_id) & set(test.review_id))
    last_train = train.groupby("user_id")["post_date"].max()
    first_test = test.groupby("user_id")["post_date"].min()
    assert (first_test >= last_train.reindex(first_test.index)).all()
    assert set(test.user_id) <= set(train.user_id)


def test_ratings_depend_on_text_and_structure(small):
    reviews, *_ = small
    pos = reviews[reviews.overall >= 4]["review_text"].str.contains("recommend|loved|wonderful|excellent|definitely", case=False).mean()
    neg = reviews[reviews.overall <= 2]["review_text"].str.contains("recommend|loved|wonderful|excellent|definitely", case=False).mean()
    assert pos > neg + 0.1


def test_cf_learns_beyond_the_mean_and_fold_in_matches_trained(small):
    _, catalog, train, test = small
    ids = catalog.hotel_id.tolist()
    cf = CFModel(n_factors=16).fit(train, ids)
    err, base = [], []
    for u, g in test.groupby("user_id"):
        pred = cf.predict(u)[0]
        for h, r in zip(g.hotel_id, g.overall):
            err.append((pred[cf.hotel_idx[h]] - r) ** 2)
            base.append((cf.mu - r) ** 2)
    assert np.mean(err) < np.mean(base)
    # a user the model has never seen, described only by history, gets sensible predictions
    u = train.user_id.iloc[0]
    hist = dict(zip(train[train.user_id == u].hotel_id, train[train.user_id == u].overall))
    trained, _, mode_t = cf.predict(u)
    folded, _, mode_f = cf.predict("brand_new_user", hist)
    assert (mode_t, mode_f) == ("trained", "fold_in")
    assert np.corrcoef(trained, folded)[0, 1] > 0.5
    assert cf.predict("brand_new_user")[2] == "item_bias"


def test_sentiment_beats_majority_baseline_on_heldout_text(small):
    *_, train, test = small
    m = SentimentModel().fit(train.review_text, train.overall)
    y = np.array([rating_to_label(r) for r in test.overall])
    acc = (m.predict_proba(test.review_text.tolist()).argmax(1) == y).mean()
    assert acc > np.bincount(y).max() / len(y) + 0.2
    assert m.analyze("Dirty room, rude staff, terrible. Would not recommend.")["label"] == "negative"
    assert m.analyze("Excellent, friendly staff and a spotless room. Highly recommended!")["label"] == "positive"


def test_content_model_uses_preferences_and_history(small):
    _, catalog, train, _ = small
    cm = ContentModel().fit(train, catalog)
    pref = cm.preference_vector(styles=["luxury"])
    scores, mode = cm.score(None, pref)
    top = np.argsort(-scores)[:5]
    assert mode == "preferences" and all("luxury" in catalog.iloc[i].styles for i in top)
    assert cm.score(None, None)[1] == "none"
    assert cm.aspect_fit({a: 1.0 for a in ["cleanliness", "service", "rooms", "location", "value"]}) is None


def test_hybrid_combines_three_models(small):
    _, catalog, train, _ = small
    rec = Recommender.fit(train, catalog)
    u = train.user_id.iloc[0]
    hist = dict(zip(train[train.user_id == u].hotel_id, train[train.user_id == u].overall))
    sc = rec.score_all(u, hist)
    assert set(sc["contributions"]) == {"cf", "content", "sentiment"}
    assert np.allclose(sum(sc["contributions"].values()), sc["hybrid"])
    assert abs(sum(sc["weights"].values()) - 1) < 1e-9


def test_shipped_evaluation_report_is_honest():
    rep = json.loads((ROOT / "ml/evaluation/results/synthetic_evaluation.json").read_text())
    assert all(v == 0 for v in rep["leakage_checks"].values())
    m = rep["models"]
    # every personalised model must beat the seeded random baseline on held-out data
    for k in ("collaborative_filtering_svd", "content_based", "hybrid_ensemble", "popularity"):
        assert m[k]["ndcg_at_k"] > m["random_baseline"]["ndcg_at_k"]
    assert m["hybrid_ensemble"]["ndcg_at_k"] > m["popularity"]["ndcg_at_k"]
    assert m["collaborative_filtering_svd"]["rmse"] < m["collaborative_filtering_svd"]["baseline_global_mean_rmse"]
    assert m["sentiment_analysis"]["accuracy"] > m["sentiment_analysis"]["majority_class_accuracy"]
    assert min(rep["tuning"]["hybrid_weights"].values()) >= 0.1
