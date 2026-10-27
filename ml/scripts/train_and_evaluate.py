"""
TripSense AI - Train and evaluate all four models
=================================================
Models: SVD collaborative filtering, content-based, sentiment analysis, hybrid
(plus a popularity baseline and a seeded random baseline for context).

Protocol (identical for every ranking model, no leakage):
  1. data/processed/train.parquet / test.parquet: per-user chronological split
     (each user's latest 20% of reviews are held out).
  2. Hybrid weights are tuned on a *validation* split carved out of TRAIN
     (models fit on train-minus-validation). The test set is not touched.
  3. Models are re-fit on the full training set and evaluated on test:
     for every user with >=1 relevant (rating >= 4) test review, rank ALL
     catalogue hotels the user has not reviewed in train; compute
     Precision/Recall/NDCG/HitRate@10 against the user's relevant test hotels.
  4. Sentiment is evaluated on held-out test review text (3 classes).
  5. Serving artifacts are fit on train+test afterwards and written to
     artifacts/models/. Reported metrics always come from step 3/4.

Usage: python ml/scripts/train_and_evaluate.py
"""
import datetime
import itertools
import json
import logging
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from ml.recsys.core import (  # noqa: E402
    ASPECTS, LABELS, RELEVANCE_THRESHOLD, HybridModel, Recommender, SentimentModel,
    hotel_sentiment_table, per_user_chronological_split, rating_to_label)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("train")

DATA = REPO_ROOT / "data" / "processed"
ARTS = REPO_ROOT / "artifacts" / "models"
EVAL_DIR = REPO_ROOT / "ml" / "evaluation" / "results"
K = 10
SEED = 42
MIN_W = 0.1          # minimum hybrid weight per component


# ---------------------------------------------------------------------------
# Ranking evaluation
# ---------------------------------------------------------------------------
def _history(df: pd.DataFrame):
    return {u: dict(zip(g["hotel_id"], g["overall"])) for u, g in df.groupby("user_id")}


def _relevant(df: pd.DataFrame):
    rel = df[df["overall"] >= RELEVANCE_THRESHOLD]
    return {u: set(g["hotel_id"]) for u, g in rel.groupby("user_id")}


def rank_metrics(top_ids, relevant, k=K):
    hits = [1 if h in relevant else 0 for h in top_ids[:k]]
    dcg = sum(x / math.log2(i + 2) for i, x in enumerate(hits))
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return sum(hits) / k, sum(hits) / len(relevant), dcg / idcg, float(sum(hits) > 0)


def evaluate_ranking(rec: Recommender, history_df, target_df, models, fold_in=False, seed=SEED):
    """Full-catalogue ranking evaluation. `models` is a list of score keys (or 'random')."""
    hist, rel = _history(history_df), _relevant(target_df)
    rng = np.random.default_rng(seed)
    ids = np.array(rec.hotel_ids)
    acc = {m: [] for m in models}
    covered = {m: set() for m in models}
    for u, relevant in rel.items():
        h = hist.get(u, {})
        sc = rec.score_all(None if fold_in else u, h)
        seen = np.array([i in h for i in ids])
        for m in models:
            s = rng.random(len(ids)) if m == "random" else np.asarray(sc[m], dtype=float)
            s = np.where(seen, -np.inf, s)
            top = ids[np.argsort(-s, kind="stable")[:K]]
            acc[m].append(rank_metrics(list(top), relevant))
            covered[m].update(top)
    out = {}
    for m in models:
        a = np.array(acc[m])
        out[m] = {"precision_at_k": round(float(a[:, 0].mean()), 4), "recall_at_k": round(float(a[:, 1].mean()), 4),
                  "ndcg_at_k": round(float(a[:, 2].mean()), 4), "hit_rate_at_k": round(float(a[:, 3].mean()), 4),
                  "catalog_coverage": round(len(covered[m]) / len(ids), 4),
                  "k": K, "evaluated_users": len(a)}
    return out


def cf_rating_metrics(rec: Recommender, test_df):
    idx = rec.cf.hotel_idx
    preds, truth, cold = [], [], 0
    cache = {}
    for u, h, r in zip(test_df["user_id"], test_df["hotel_id"], test_df["overall"]):
        if not rec.cf.knows_user(u):
            cold += 1
            continue
        if u not in cache:
            cache[u] = rec.cf.predict(u)[0]
        preds.append(cache[u][idx[h]])
        truth.append(r)
    mean_pred = np.full(len(truth), rec.cf.mu)
    return {"rmse": round(math.sqrt(mean_squared_error(truth, preds)), 4), "mae": round(mean_absolute_error(truth, preds), 4),
            "baseline_global_mean_rmse": round(math.sqrt(mean_squared_error(truth, mean_pred)), 4),
            "baseline_global_mean_mae": round(mean_absolute_error(truth, mean_pred), 4),
            "cold_start_test_reviews_skipped": cold, "n_test_reviews": len(truth)}


def sentiment_metrics(model: SentimentModel, test_df):
    y = np.array([rating_to_label(r) for r in test_df["overall"]])
    proba = model.predict_proba(test_df["review_text"].tolist())
    pred = proba.argmax(axis=1)
    majority = np.bincount(y).argmax()
    return {
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
        "majority_class_accuracy": round(float((y == majority).mean()), 4),
        "majority_class_macro_f1": round(float(f1_score(y, np.full_like(y, majority), average="macro")), 4),
        "auc_positive_vs_rest": round(float(roc_auc_score(y == 2, proba[:, 2])), 4),
        "labels": LABELS, "n_test_reviews": int(len(y)),
        "test_label_distribution": {l: round(float((y == i).mean()), 4) for i, l in enumerate(LABELS)},
    }


# ---------------------------------------------------------------------------
# Hybrid weight tuning (validation only)
# ---------------------------------------------------------------------------
def tune_hybrid(train_df, catalog, cf_params):
    sub_train, val = per_user_chronological_split(train_df, 0.2)
    logger.info("Tuning hybrid on validation split: fit=%d reviews, validation=%d reviews", len(sub_train), len(val))
    rec = Recommender.fit(sub_train, catalog, cf_params=cf_params)
    hist, rel = _history(sub_train), _relevant(val)
    users = list(rel)
    comps = {}
    for u in users:
        sc = rec.score_all(u, hist.get(u, {}))
        comps[u] = sc
    ids = np.array(rec.hotel_ids)
    from ml.recsys.core import minmax
    grid, best = [], None
    steps = [i / 10 for i in range(0, 11)]
    for wc, wt in itertools.product(steps, steps):
        ws = round(1 - wc - wt, 2)
        # design constraint: every model must contribute at least MIN_W to the hybrid
        if min(wc, wt, ws) < MIN_W - 1e-9:
            continue
        w = {"cf": wc, "content": wt, "sentiment": ws}
        nd = []
        for u in users:
            sc = comps[u]
            s = sum(w[k] * minmax(v) for k, v in zip(("cf", "content", "sentiment"),
                                                     (sc["collaborative"], sc["content"], sc["sentiment"]))) / sum(w.values())
            seen = np.array([i in hist.get(u, {}) for i in ids])
            s = np.where(seen, -np.inf, s)
            nd.append(rank_metrics(list(ids[np.argsort(-s, kind="stable")[:K]]), rel[u])[2])
        val_ndcg = float(np.mean(nd))
        grid.append((val_ndcg, w))
        if best is None or val_ndcg > best[0]:
            best = (val_ndcg, w)
    tot = sum(best[1].values())
    weights = {k: round(v / tot, 3) for k, v in best[1].items()}
    logger.info("Best hybrid weights %s (validation NDCG@%d=%.4f)", weights, K, best[0])
    return weights, round(best[0], 4), len(grid)


def tune_cf(train_df, catalog):
    """Pick SVD hyper-parameters on a validation split carved from train (test untouched).

    Stage 1: rating-SVD (n_factors, reg) by validation RMSE.
    Stage 2: interaction-SVD rank and rating mix by validation NDCG@10.
    """
    from ml.recsys.core import CFModel
    sub_train, val = per_user_chronological_split(train_df, 0.2)
    ids = catalog["hotel_id"].tolist()
    best = None
    for nf, reg in itertools.product([16, 32, 64], [0.03, 0.06, 0.1]):
        m = CFModel(n_factors=nf, reg_all=reg).fit(sub_train, ids)
        errs = []
        for u, g in val.groupby("user_id"):
            if m.knows_user(u):
                p = m.predict(u)[0]
                errs += [(p[m.hotel_idx[h]] - r) ** 2 for h, r in zip(g["hotel_id"], g["overall"])]
        rmse = math.sqrt(np.mean(errs))
        logger.info("  rating-SVD n_factors=%d reg=%.2f validation RMSE=%.4f", nf, reg, rmse)
        if best is None or rmse < best[0]:
            best = (rmse, {"n_factors": nf, "reg_all": reg})
    params, val_rmse = dict(best[1]), round(best[0], 4)

    hist, rel = _history(sub_train), _relevant(val)
    arr = np.array(ids)
    best2 = None
    for k in (8, 16, 24, 32):
        m = CFModel(**params, implicit_k=k).fit(sub_train, ids)
        for mix in (0.0, 0.25, 0.5, 1.0):
            m.rating_mix = mix
            nd = []
            for u, r in rel.items():
                s_ = m.rank_score(u, hist.get(u, {}))[0]
                s_ = np.where([h in hist.get(u, {}) for h in ids], -np.inf, s_)
                nd.append(rank_metrics(list(arr[np.argsort(-s_, kind="stable")[:K]]), r)[2])
            v = float(np.mean(nd))
            logger.info("  interaction-SVD k=%d rating_mix=%.2f validation NDCG@%d=%.4f", k, mix, K, v)
            if best2 is None or v > best2[0]:
                best2 = (v, k, mix)
    params.update(implicit_k=best2[1], rating_mix=best2[2])
    logger.info("Best CF params %s (validation RMSE=%.4f, ranking NDCG@%d=%.4f)", params, val_rmse, K, best2[0])
    return params, val_rmse, round(best2[0], 4)


# ---------------------------------------------------------------------------
def leakage_checks(train, test):
    train_pairs = set(zip(train["user_id"], train["hotel_id"]))
    overlap = sum((u, h) in train_pairs for u, h in zip(test["user_id"], test["hotel_id"]))
    last_train = train.groupby("user_id")["post_date"].max()
    t_first = test.groupby("user_id")["post_date"].min()
    common = t_first.index.intersection(last_train.index)
    out_of_order = int((t_first[common] < last_train[common]).sum())
    return {"user_hotel_pairs_in_both_splits": int(overlap), "users_with_test_before_train": out_of_order,
            "test_users_without_train_history": int(len(set(test["user_id"]) - set(train["user_id"]))),
            "review_ids_in_both_splits": int(len(set(train["review_id"]) & set(test["review_id"])))}


def main():
    train = pd.read_parquet(DATA / "train.parquet")
    test = pd.read_parquet(DATA / "test.parquet")
    catalog = pd.read_parquet(DATA / "hotel_catalog.parquet")
    full = pd.concat([train, test], ignore_index=True)
    logger.info("train=%d test=%d hotels=%d users=%d", len(train), len(test), len(catalog), full["user_id"].nunique())

    checks = leakage_checks(train, test)
    logger.info("Leakage checks: %s", checks)
    assert checks["user_hotel_pairs_in_both_splits"] == 0 and checks["review_ids_in_both_splits"] == 0
    assert checks["users_with_test_before_train"] == 0 and checks["test_users_without_train_history"] == 0

    cf_params, cf_val_rmse, cf_val_ndcg = tune_cf(train, catalog)
    weights, val_ndcg, n_grid = tune_hybrid(train, catalog, cf_params)
    hybrid = HybridModel(weights=weights)

    logger.info("Fitting on train and evaluating on held-out test ...")
    rec = Recommender.fit(train, catalog, hybrid=hybrid, cf_params=cf_params)
    ranking = evaluate_ranking(rec, train, test, ["random", "popularity", "collaborative", "content", "sentiment", "hybrid"])
    fold = evaluate_ranking(rec, train, test, ["collaborative", "hybrid"], fold_in=True)
    cf_rating = cf_rating_metrics(rec, test)
    sent = sentiment_metrics(rec.sentiment, test)
    for m, v in ranking.items():
        logger.info("  %-14s P@10=%.4f R@10=%.4f NDCG@10=%.4f Hit@10=%.4f", m, v["precision_at_k"], v["recall_at_k"], v["ndcg_at_k"], v["hit_rate_at_k"])
    logger.info("  CF fold-in (new-user path) NDCG@10=%.4f | trained NDCG@10=%.4f", fold["collaborative"]["ndcg_at_k"], ranking["collaborative"]["ndcg_at_k"])
    logger.info("  CF rating RMSE=%.4f (global-mean baseline %.4f)", cf_rating["rmse"], cf_rating["baseline_global_mean_rmse"])
    logger.info("  Sentiment accuracy=%.4f macroF1=%.4f (majority %.4f)", sent["accuracy"], sent["macro_f1"], sent["majority_class_accuracy"])

    report = {
        "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dataset_info": {
            "source": "synthetic (seed=42, reproducible)", "total_reviews": int(len(full)),
            "train_reviews": int(len(train)), "test_reviews": int(len(test)),
            "distinct_users": int(full["user_id"].nunique()), "distinct_hotels": int(full["hotel_id"].nunique()),
            "split": "per-user chronological: each user's latest 20% of reviews held out",
            "relevance_threshold": RELEVANCE_THRESHOLD, "k": K,
            "evaluation_protocol": "Full-catalogue ranking: all hotels the user has not reviewed in train are ranked; "
                                   "relevant = test reviews rated >= 4. Same protocol for every model.",
        },
        "leakage_checks": checks,
        "tuning": {"data": "validation split carved from train only; test untouched",
                   "svd_params": cf_params, "svd_validation_rmse": cf_val_rmse, "cf_validation_ndcg_at_k": cf_val_ndcg,
                   "hybrid_weights": weights, "hybrid_validation_ndcg_at_k": val_ndcg, "hybrid_grid_size": n_grid, "hybrid_min_component_weight": MIN_W},
        "models": {
            "random_baseline": ranking["random"],
            "popularity": ranking["popularity"],
            "collaborative_filtering_svd": {**ranking["collaborative"], **cf_rating,
                                            "params": cf_params, "fold_in_new_user": fold["collaborative"]},
            "content_based": ranking["content"],
            "sentiment_analysis": {**sent, "ranking_by_hotel_sentiment": ranking["sentiment"]},
            "hybrid_ensemble": {**ranking["hybrid"], "weights": weights, "fold_in_new_user": fold["hybrid"]},
        },
    }
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    (EVAL_DIR / "synthetic_evaluation.json").write_text(json.dumps(report, indent=2))

    # ---- serving artifacts: refit on ALL data (metrics above are the held-out ones) ----
    logger.info("Refitting on all data for serving ...")
    final = Recommender.fit(full, catalog, hybrid=hybrid, cf_params=cf_params)
    for d in ("collaborative_filtering", "content_based", "nlp_sentiment", "hybrid_ensemble"):
        (ARTS / d).mkdir(parents=True, exist_ok=True)
    with open(ARTS / "recommender.pkl", "wb") as f:
        pickle.dump(final, f)
    (ARTS / "hybrid_ensemble" / "hybrid_config.json").write_text(json.dumps(
        {"weights": hybrid.weights, "cold_start_weights": hybrid.cold_weights, "tuned_on": "validation split of train"}, indent=2))

    # refresh the hotel feature table served by the API with model-derived sentiment
    feats = pd.read_parquet(DATA / "features" / "hotel_features_complete.parquet")
    sent_by_hotel = dict(zip(final.hotel_ids, final.hotel_sentiment))
    feats["sentiment_score"] = feats["hotel_id"].map(sent_by_hotel).round(4)
    feats.to_parquet(DATA / "features" / "hotel_features_complete.parquet", index=False)
    logger.info("Saved %s and updated hotel sentiment_score", ARTS / "recommender.pkl")


if __name__ == "__main__":
    main()
