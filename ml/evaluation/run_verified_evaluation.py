"""
TripSense AI - Verified (leakage-free) evaluation.

Protocol
- Source: raw TripAdvisor CSV (no downstream artifacts are trusted).
- Chronological 80/20 split on ``post_date`` (ties broken deterministically).
- Every model is fit on TRAIN only; seen items are excluded from rankings;
  relevant items are TEST reviews rated >= 4.0.
- A ranking model can only be evaluated on users who have at least one relevant
  test item that exists in the train catalogue. If there are none, ranking
  metrics are reported as null with the reason, never as 0.0 or a made-up value.
- The text/sentiment model is evaluated as a rating predictor (RMSE/MAE/AUC),
  which does not require item identity.

Usage: python -m ml.evaluation.run_verified_evaluation
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "tripadvisor_reviews.csv"
OUT = Path(__file__).resolve().parent / "results" / "verified_evaluation.json"
K = 10
THRESH = 4.0
SEED = 42


def ndcg_at_k(rec, rel, k=K):
    dcg = sum(1.0 / np.log2(i + 2) for i, r in enumerate(rec[:k]) if r in rel)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(k, len(rel))))
    return dcg / idcg if idcg else 0.0


def rank_metrics(rec_by_user, rel_by_user):
    p, r, n, hit = [], [], [], []
    for u, rel in rel_by_user.items():
        rec = rec_by_user[u][:K]
        hits = sum(1 for x in rec if x in rel)
        p.append(hits / K)
        r.append(hits / len(rel))
        n.append(ndcg_at_k(rec, rel))
        hit.append(1.0 if hits else 0.0)
    return {
        "precision_at_10": float(np.mean(p)), "recall_at_10": float(np.mean(r)),
        "ndcg_at_10": float(np.mean(n)), "hit_rate": float(np.mean(hit)),
    }


def split(df):
    df = df.sort_values(["post_date", "hotel_id"], kind="mergesort").reset_index(drop=True)
    cut = int(len(df) * 0.8)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def evaluate_rankers(train, test):
    from scipy.sparse import csr_matrix
    from sklearn.decomposition import TruncatedSVD

    catalogue = train["hotel_id"].unique()
    item_idx = {h: i for i, h in enumerate(catalogue)}
    seen = train.groupby("user_id")["hotel_id"].apply(set).to_dict()
    rel_all = test[test["overall"] >= THRESH].groupby("user_id")["hotel_id"].apply(set).to_dict()
    # only items present in the train catalogue can ever be recommended
    rel = {u: {h for h in hs if h in item_idx} for u, hs in rel_all.items()}
    rel = {u: hs for u, hs in rel.items() if hs and u in seen}

    diag = {
        "train_catalogue_items": int(len(catalogue)),
        "test_reviews": int(len(test)),
        "test_reviews_with_item_in_train": float(test["hotel_id"].isin(item_idx).mean()),
        "test_reviews_with_user_in_train": float(test["user_id"].isin(seen).mean()),
        "users_with_relevant_test_items": int(len(rel_all)),
        "evaluable_users": int(len(rel)),
    }
    if not rel:
        reason = ("No test user has a relevant item that also exists in the training catalogue "
                  "(and a training history), so item-ranking models cannot be evaluated.")
        null = {m: None for m in ("precision_at_10", "recall_at_10", "ndcg_at_10", "hit_rate")}
        return diag, {name: {**null, "status": "not_evaluable", "reason": reason}
                      for name in ("popularity", "collaborative_filtering", "content_based", "hybrid")}

    users = sorted(seen)
    uidx = {u: i for i, u in enumerate(users)}
    rows = train["user_id"].map(uidx).to_numpy()
    cols = train["hotel_id"].map(item_idx).to_numpy()
    mat = csr_matrix((np.ones(len(train), dtype=np.float32), (rows, cols)), shape=(len(users), len(catalogue)))
    pop = np.asarray(mat.sum(axis=0)).ravel()
    svd = TruncatedSVD(n_components=min(50, min(mat.shape) - 1), random_state=SEED).fit(mat)
    U = svd.transform(mat)

    feats = train.groupby("hotel_id")[["overall", "cleanliness", "value", "location", "rooms", "sleep_quality"]].mean()
    feats = feats.reindex(catalogue).fillna(feats.mean())
    F = (feats - feats.mean()) / (feats.std().replace(0, 1))
    F = F.to_numpy(dtype=np.float32)
    F /= np.linalg.norm(F, axis=1, keepdims=True) + 1e-9

    def top(scores, u):
        s = scores.copy()
        for h in seen[u]:
            s[item_idx[h]] = -np.inf
        return [catalogue[i] for i in np.argsort(-s)[:K]]

    rec = {"popularity": {}, "collaborative_filtering": {}, "content_based": {}, "hybrid": {}}
    z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
    for u in rel:
        i = uidx[u]
        cf = U[i] @ svd.components_
        liked = [item_idx[h] for h in seen[u]]
        prof = F[liked].mean(axis=0)
        cb = F @ prof
        rec["popularity"][u] = top(pop.astype(float), u)
        rec["collaborative_filtering"][u] = top(cf, u)
        rec["content_based"][u] = top(cb, u)
        rec["hybrid"][u] = top(0.6 * z(cf) + 0.2 * z(cb) + 0.2 * z(np.log1p(pop)), u)
    return diag, {n: {**rank_metrics(r, rel), "status": "evaluated"} for n, r in rec.items()}


def evaluate_text_model(train, test):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_auc_score

    vec = TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=3, sublinear_tf=True)
    Xtr = vec.fit_transform(train["text"].fillna(""))
    Xte = vec.transform(test["text"].fillna(""))
    model = Ridge(alpha=1.0, random_state=SEED).fit(Xtr, train["overall"])
    pred = np.clip(model.predict(Xte), 1, 5)
    y = test["overall"].to_numpy()
    base = np.full_like(y, train["overall"].mean())
    rmse = lambda a, b: float(np.sqrt(mean_squared_error(a, b)))
    return {
        "task": "predict overall rating from review text (TF-IDF + Ridge, fit on train only)",
        "test_reviews": int(len(test)),
        "rmse": rmse(y, pred), "mae": float(mean_absolute_error(y, pred)),
        "auc_rating_ge_4": float(roc_auc_score(y >= THRESH, pred)),
        "baseline_global_mean_rmse": rmse(y, base),
        "baseline_global_mean_mae": float(mean_absolute_error(y, base)),
    }


def main():
    df = pd.read_csv(RAW)
    train, test = split(df)
    integrity = {
        "rows": int(len(df)), "distinct_hotel_id": int(df["hotel_id"].nunique()),
        "distinct_user_id": int(df["user_id"].nunique()),
        "reviews_per_hotel_id_mean": float(len(df) / df["hotel_id"].nunique()),
        "hotel_id_is_unique_per_row": bool(df["hotel_id"].nunique() == len(df)),
    }
    counts = df["overall"].round().value_counts(normalize=True)
    summary = {
        "total_reviews": int(len(df)), "total_users": integrity["distinct_user_id"],
        "distinct_hotel_ids": integrity["distinct_hotel_id"],
        "avg_rating": round(float(df["overall"].mean()), 3), "rating_std": round(float(df["overall"].std()), 3),
        "sparsity_percent": round(100 * (1 - len(df) / (integrity["distinct_user_id"] * integrity["distinct_hotel_id"])), 4),
        "date_range": {"start": str(df["post_date"].min()), "end": str(df["post_date"].max())},
        "rating_distribution": [{"rating": str(r), "count": int((df["overall"].round() == r).sum()),
                                 "percentage": round(100 * float(counts.get(float(r), 0)), 1)} for r in range(1, 6)],
        "train_reviews": int(len(train)), "test_reviews": int(len(test)),
    }
    diag, ranking = evaluate_rankers(train, test)
    result = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocol": {"split": "chronological 80/20 by post_date", "k": K,
                     "relevance_threshold": THRESH, "fit_on": "train only",
                     "seen_items_excluded": True, "seed": SEED,
                     "train_rows": int(len(train)), "test_rows": int(len(test))},
        "data_integrity": integrity,
        "dataset_summary": summary,
        "ranking_feasibility": diag,
        "ranking_models": ranking,
        "sentiment_text_model": evaluate_text_model(train, test),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
