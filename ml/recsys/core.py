"""
TripSense AI - recommender core
===============================
One implementation of every model, used by ml/scripts/train_and_evaluate.py
(training + held-out evaluation) and by the API (inference), so what is
evaluated is exactly what is served.

  CFModel         SVD matrix factorisation (fit with scikit-surprise; factors are
                  extracted to numpy so inference needs no surprise install).
                  Unknown users are handled by ridge "fold-in" on their history.
  ContentModel    hotel vectors = review-text TF-IDF + destination + style +
                  amenities + aspect quality; user profile from rated history
                  and/or explicit preferences; cosine scoring.
  SentimentModel  TF-IDF + logistic regression (negative / neutral / positive).
  HybridModel     weighted blend of per-user min-max normalised CF, content
                  and sentiment scores.
"""
import math
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import normalize

ASPECTS = ["cleanliness", "service", "rooms", "location", "value"]
STYLES = ["family", "business", "romantic", "budget", "luxury", "adventure"]
LABELS = ["negative", "neutral", "positive"]
RELEVANCE_THRESHOLD = 4.0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def per_user_chronological_split(reviews: pd.DataFrame, test_frac: float = 0.2):
    """Latest `test_frac` of each user's reviews (by date) -> test; the rest -> train."""
    df = reviews.sort_values(["user_id", "post_date", "review_id"]).reset_index(drop=True)
    rank = df.groupby("user_id").cumcount()
    size = df.groupby("user_id")["review_id"].transform("count")
    n_test = np.maximum(1, np.floor(size * test_frac)).astype(int)
    is_test = rank >= (size - n_test)
    return df[~is_test].reset_index(drop=True), df[is_test].reset_index(drop=True)


def rating_to_label(r: float) -> int:
    """1-2 -> negative(0), 3 -> neutral(1), 4-5 -> positive(2)."""
    return 0 if r <= 2 else (1 if r <= 3 else 2)


def minmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lo, hi = np.nanmin(x), np.nanmax(x)
    return np.zeros_like(x) if hi - lo < 1e-12 else (x - lo) / (hi - lo)


def _split_tags(s) -> List[str]:
    return [t for t in str(s or "").split(",") if t]


# ---------------------------------------------------------------------------
# Collaborative filtering (SVD)
# ---------------------------------------------------------------------------
class CFModel:
    """Matrix-factorisation CF with two SVD components.

    * rating SVD (scikit-surprise): predicts the star rating a user would give.
    * interaction SVD (truncated SVD of the binary user x hotel matrix): scores how
      likely a user is to engage with a hotel. Rating prediction alone cannot rank
      well because *which* hotels a user reviews is itself the dominant signal.
    Ranking score = minmax(interaction affinity) + rating_mix * minmax(predicted rating).
    """

    def __init__(self, n_factors=32, n_epochs=40, lr_all=0.005, reg_all=0.1,
                 fold_in_reg=1.0, implicit_k=16, rating_mix=0.5, random_state=42):
        self.params = dict(n_factors=n_factors, n_epochs=n_epochs, lr_all=lr_all,
                           reg_all=reg_all, random_state=random_state)
        self.fold_in_reg = fold_in_reg
        self.implicit_k = implicit_k
        self.rating_mix = rating_mix

    def fit(self, train: pd.DataFrame, hotel_ids: Sequence[str]) -> "CFModel":
        import scipy.sparse as sp
        from scipy.sparse.linalg import svds
        from surprise import SVD, Dataset, Reader
        data = Dataset.load_from_df(train[["user_id", "hotel_id", "overall"]], Reader(rating_scale=(1, 5)))
        ts = data.build_full_trainset()
        svd = SVD(**self.params)
        svd.fit(ts)
        self.hotel_ids = list(hotel_ids)
        self.hotel_idx = {h: i for i, h in enumerate(self.hotel_ids)}
        k = self.params["n_factors"]
        self.mu = float(ts.global_mean)
        self.bi = np.zeros(len(self.hotel_ids))
        self.qi = np.zeros((len(self.hotel_ids), k))
        for inner in ts.all_items():
            j = self.hotel_idx.get(ts.to_raw_iid(inner))
            if j is not None:
                self.bi[j] = svd.bi[inner]
                self.qi[j] = svd.qi[inner]
        self.user_idx = {ts.to_raw_uid(u): u for u in ts.all_users()}
        self.bu, self.pu = svd.bu.copy(), svd.pu.copy()

        # interaction SVD over the same users (row order = rating-SVD inner ids)
        rows = [self.user_idx[u] for u in train["user_id"]]
        cols = [self.hotel_idx[h] for h in train["hotel_id"]]
        M = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(self.user_idx), len(self.hotel_ids)))
        M.data[:] = 1.0
        self.interactions = M
        _, _, vt = svds(M, k=self.implicit_k, random_state=self.params["random_state"])
        self.V = vt.T
        return self

    def knows_user(self, user_id: Optional[str]) -> bool:
        return user_id is not None and user_id in self.user_idx

    def _fold_in(self, history: Dict[str, float]):
        rows = [(self.hotel_idx[h], r) for h, r in history.items() if h in self.hotel_idx]
        if not rows:
            return None
        idx = np.array([i for i, _ in rows])
        y = np.array([r for _, r in rows]) - self.mu - self.bi[idx]
        X = np.hstack([np.ones((len(idx), 1)), self.qi[idx]])
        sol = np.linalg.solve(X.T @ X + self.fold_in_reg * np.eye(X.shape[1]), X.T @ y)
        return float(sol[0]), sol[1:]

    def _affinity(self, x: np.ndarray) -> np.ndarray:
        return (x @ self.V) @ self.V.T

    def predict(self, user_id: Optional[str] = None, history: Optional[Dict[str, float]] = None):
        """Returns (predicted ratings 1-5, interaction affinity, mode).

        mode: 'trained' (user in the training set), 'fold_in' (new user built from
        `history`), or 'item_bias' (no user information: not personalised).
        """
        n = len(self.hotel_ids)
        if self.knows_user(user_id):
            u = self.user_idx[user_id]
            rating = self.mu + self.bi + self.bu[u] + self.qi @ self.pu[u]
            return np.clip(rating, 1, 5), self._affinity(self.interactions[u].toarray().ravel()), "trained"
        folded = self._fold_in(history) if history else None
        if folded is not None:
            bu, pu = folded
            x = np.zeros(n)
            for h in history:
                if h in self.hotel_idx:
                    x[self.hotel_idx[h]] = 1.0
            return np.clip(self.mu + self.bi + bu + self.qi @ pu, 1, 5), self._affinity(x), "fold_in"
        return np.clip(self.mu + self.bi, 1, 5), np.zeros(n), "item_bias"

    def rank_score(self, user_id=None, history=None):
        rating, aff, mode = self.predict(user_id, history)
        if mode == "item_bias":
            # no user information: item bias + how often guests engage with the hotel (not personalised)
            engage = np.log1p(np.asarray(self.interactions.sum(axis=0)).ravel())
            score = minmax(rating) + minmax(engage)
        else:
            score = minmax(aff) + self.rating_mix * minmax(rating)
        return score, rating, mode


# ---------------------------------------------------------------------------
# Sentiment analysis
# ---------------------------------------------------------------------------
class SentimentModel:
    def __init__(self, C=4.0):
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, max_features=20000)
        self.clf = LogisticRegression(C=C, max_iter=1000)

    def fit(self, texts: Iterable[str], ratings: Iterable[float]) -> "SentimentModel":
        X = self.tfidf.fit_transform(list(texts))
        self.clf.fit(X, [rating_to_label(r) for r in ratings])
        return self

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        return self.clf.predict_proba(self.tfidf.transform(list(texts)))

    def score(self, texts: Sequence[str]) -> np.ndarray:
        """Sentiment in [-1, 1] = P(positive) - P(negative)."""
        p = self.predict_proba(texts)
        return p[:, 2] - p[:, 0]

    def analyze(self, text: str) -> dict:
        p = self.predict_proba([text])[0]
        return {"label": LABELS[int(np.argmax(p))],
                "probabilities": {l: round(float(v), 4) for l, v in zip(LABELS, p)},
                "score": round(float(p[2] - p[0]), 4),
                "confidence": round(float(p.max()), 4)}

    @staticmethod
    def out_of_fold_scores(texts: Sequence[str], ratings: Sequence[float], folds=5, C=4.0) -> np.ndarray:
        """Scores for each review from a model that never saw that review (no in-sample optimism)."""
        from sklearn.pipeline import make_pipeline
        pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, max_features=20000),
                             LogisticRegression(C=C, max_iter=1000))
        p = cross_val_predict(pipe, list(texts), [rating_to_label(r) for r in ratings],
                              cv=folds, method="predict_proba")
        return p[:, 2] - p[:, 0]


def hotel_sentiment_table(hotel_ids: Sequence[str], review_hotels: Sequence[str],
                          review_scores: np.ndarray, shrink_k=5.0) -> np.ndarray:
    """Per-hotel mean review sentiment, shrunk towards the global mean (hotel order preserved)."""
    df = pd.DataFrame({"h": list(review_hotels), "s": review_scores})
    g = df.groupby("h")["s"].agg(["sum", "count"])
    glob = float(df["s"].mean())
    out = np.full(len(hotel_ids), glob)
    for i, h in enumerate(hotel_ids):
        if h in g.index:
            out[i] = (g.at[h, "sum"] + shrink_k * glob) / (g.at[h, "count"] + shrink_k)
    return out


# ---------------------------------------------------------------------------
# Content-based
# ---------------------------------------------------------------------------
class ContentModel:
    BLOCK_W = {"text": 1.0, "dest": 1.0, "style": 1.0, "amenity": 0.5, "aspect": 0.8, "star": 0.3}

    def fit(self, train: pd.DataFrame, catalog: pd.DataFrame) -> "ContentModel":
        cat = catalog.reset_index(drop=True)
        self.hotel_ids = cat["hotel_id"].tolist()
        self.hotel_idx = {h: i for i, h in enumerate(self.hotel_ids)}
        n = len(cat)

        corpus = train.groupby("hotel_id")["review_text"].apply(" ".join).reindex(self.hotel_ids).fillna("")
        self.tfidf = TfidfVectorizer(max_features=400, ngram_range=(1, 2), min_df=3, stop_words="english", sublinear_tf=True)
        text = normalize(self.tfidf.fit_transform(corpus.values).toarray())

        self.dests = sorted(cat["location"].unique())
        dest = np.zeros((n, len(self.dests)))
        for i, d in enumerate(cat["location"]):
            dest[i, self.dests.index(d)] = 1
        self.styles = STYLES
        style = np.zeros((n, len(STYLES)))
        for i, s in enumerate(cat["styles"]):
            for t in _split_tags(s):
                if t in STYLES:
                    style[i, STYLES.index(t)] = 1
        self.amenities = sorted({a for s in cat["amenities"] for a in _split_tags(s)})
        amen = np.zeros((n, len(self.amenities)))
        for i, s in enumerate(cat["amenities"]):
            for a in _split_tags(s):
                amen[i, self.amenities.index(a)] = 1
        # aspect quality from TRAIN reviews only, z-scored across hotels
        asp = train.groupby("hotel_id")[ASPECTS].mean().reindex(self.hotel_ids)
        asp = asp.fillna(asp.mean())
        self.aspect_mu, self.aspect_sd = asp.mean().values, asp.std().values + 1e-9
        aspz = (asp.values - self.aspect_mu) / self.aspect_sd
        self.aspect_z = aspz
        star = ((cat["star_class"].values - 3.5) / 1.0).reshape(-1, 1)

        self.blocks = {"text": text, "dest": dest, "style": style, "amenity": amen, "aspect": aspz, "star": star}
        self.slices, parts, pos = {}, [], 0
        for name, mat in self.blocks.items():
            m = normalize(mat) * self.BLOCK_W[name] if name != "star" else mat * self.BLOCK_W[name]
            parts.append(m)
            self.slices[name] = slice(pos, pos + m.shape[1])
            pos += m.shape[1]
        self.V = np.hstack(parts)
        self.Vn = normalize(self.V)
        return self

    def aspect_fit(self, aspect_weights: Optional[Dict[str, float]]) -> Optional[np.ndarray]:
        """Weighted z-scored aspect quality per hotel (None if all weights are equal = no preference)."""
        if not aspect_weights:
            return None
        w = np.array([float(aspect_weights.get(a, 1.0)) for a in ASPECTS])
        if np.allclose(w, w[0]):
            return None
        return self.aspect_z @ (w / w.sum())

    def preference_vector(self, destination: Optional[str] = None, styles: Sequence[str] = ()) -> Optional[np.ndarray]:
        """Destination / travel-style preferences in the hotel-vector space (None if nothing was specified)."""
        v = np.zeros(self.V.shape[1])
        used = False
        if destination:
            for j, d in enumerate(self.dests):
                if d.lower() == destination.lower():
                    v[self.slices["dest"]][j] = 1 * self.BLOCK_W["dest"]
                    used = True
        sty = [s for s in styles if s in STYLES]
        if sty:
            blk = np.zeros(len(STYLES))
            for s in sty:
                blk[STYLES.index(s)] = 1
            v[self.slices["style"]] = normalize(blk.reshape(1, -1))[0] * self.BLOCK_W["style"]
            used = True
        return normalize(v.reshape(1, -1))[0] if used else None

    def history_vector(self, history: Dict[str, float]) -> Optional[np.ndarray]:
        """Profile = sum over rated hotels of (rating - user mean) * hotel vector."""
        items = [(self.hotel_idx[h], r) for h, r in history.items() if h in self.hotel_idx]
        if not items:
            return None
        mean = np.mean([r for _, r in items])
        w = np.array([r - mean for _, r in items])
        if np.allclose(w, 0):
            w = np.ones(len(items))
        prof = (w.reshape(-1, 1) * self.Vn[[i for i, _ in items]]).sum(axis=0)
        return normalize(prof.reshape(1, -1))[0] if np.linalg.norm(prof) > 0 else None

    def score(self, history: Optional[Dict[str, float]] = None, pref: Optional[np.ndarray] = None,
              aspect_weights: Optional[Dict[str, float]] = None):
        """Content score for every hotel. Returns (scores, mode).

        cosine(profile, hotel) uses rated history and/or destination/style preferences;
        explicit aspect weights add a weighted aspect-quality fit. When both exist they
        are averaged after min-max normalisation.
        """
        h = self.history_vector(history) if history else None
        parts = [p for p in (h, pref) if p is not None]
        components, modes = [], []
        if parts:
            prof = normalize(np.sum(parts, axis=0).reshape(1, -1))[0]
            components.append(minmax(self.Vn @ prof))
            modes.append("history+preferences" if len(parts) == 2 else ("history" if h is not None else "preferences"))
        fit = self.aspect_fit(aspect_weights)
        if fit is not None:
            components.append(minmax(fit))
            modes.append("aspect weights")
        if not components:
            return np.zeros(len(self.hotel_ids)), "none"
        return np.mean(components, axis=0), " + ".join(modes)


# ---------------------------------------------------------------------------
# Popularity baseline + hybrid
# ---------------------------------------------------------------------------
def popularity_scores(train: pd.DataFrame, hotel_ids: Sequence[str], prior_n=20) -> np.ndarray:
    """Bayesian average rating: the standard non-personalised baseline."""
    g = train.groupby("hotel_id")["overall"].agg(["sum", "count"])
    mu = train["overall"].mean()
    out = np.full(len(hotel_ids), mu)
    for i, h in enumerate(hotel_ids):
        if h in g.index:
            out[i] = (g.at[h, "sum"] + prior_n * mu) / (g.at[h, "count"] + prior_n)
    return out


class HybridModel:
    """Weighted blend of min-max normalised component scores.

    `weights` apply when the user has personal signal (history or a known id).
    `cold_weights` apply to brand-new users with only explicit preferences, where CF
    can only offer an item-bias prior.
    """

    def __init__(self, weights=None, cold_weights=None):
        self.weights = weights or {"cf": 0.5, "content": 0.3, "sentiment": 0.2}
        self.cold_weights = cold_weights or {"cf": 0.2, "content": 0.5, "sentiment": 0.3}

    def combine(self, cf: np.ndarray, content: np.ndarray, sentiment: np.ndarray, cf_personal: bool,
                content_active: bool = True):
        w = dict(self.weights if cf_personal else self.cold_weights)
        if not content_active:                       # no profile -> content has nothing to say
            w["content"] = 0.0
        tot = sum(w.values())
        w = {k: v / tot for k, v in w.items()}
        parts = {"cf": minmax(cf), "content": minmax(content), "sentiment": minmax(sentiment)}
        score = sum(w[k] * parts[k] for k in w)
        return score, {k: w[k] * parts[k] for k in w}, w


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------
class Recommender:
    """Fitted bundle of all four models + the catalogue they are defined over."""

    def __init__(self, catalog, cf, content, sentiment, hotel_sentiment, popularity, hybrid):
        self.catalog = catalog.reset_index(drop=True)
        self.hotel_ids = self.catalog["hotel_id"].tolist()
        self.cf, self.content, self.sentiment = cf, content, sentiment
        self.hotel_sentiment, self.popularity, self.hybrid = hotel_sentiment, popularity, hybrid

    @classmethod
    def fit(cls, train: pd.DataFrame, catalog: pd.DataFrame, hybrid: Optional[HybridModel] = None,
            cf_params: Optional[dict] = None) -> "Recommender":
        ids = catalog["hotel_id"].tolist()
        cf = CFModel(**(cf_params or {})).fit(train, ids)
        content = ContentModel().fit(train, catalog)
        sent = SentimentModel().fit(train["review_text"], train["overall"])
        oof = SentimentModel.out_of_fold_scores(train["review_text"].tolist(), train["overall"].tolist())
        hs = hotel_sentiment_table(ids, train["hotel_id"].tolist(), oof)
        pop = popularity_scores(train, ids)
        return cls(catalog, cf, content, sent, hs, pop, hybrid or HybridModel())

    def score_all(self, user_id: Optional[str] = None, history: Optional[Dict[str, float]] = None,
                  pref: Optional[np.ndarray] = None, aspect_weights: Optional[Dict[str, float]] = None) -> dict:
        """Raw per-hotel scores from every model for one user."""
        cf_score, cf_rating, cf_mode = self.cf.rank_score(user_id, history)
        content, content_mode = self.content.score(history, pref, aspect_weights)
        personal = cf_mode in ("trained", "fold_in")
        hyb, contrib, w = self.hybrid.combine(cf_score, content, self.hotel_sentiment, personal,
                                              content_active=content_mode != "none")
        return {"collaborative": cf_score, "cf_rating": cf_rating, "content": content, "sentiment": self.hotel_sentiment,
                "popularity": self.popularity, "hybrid": hyb, "contributions": contrib, "weights": w,
                "cf_mode": cf_mode, "content_mode": content_mode}
