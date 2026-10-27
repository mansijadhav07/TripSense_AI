"""
TripSense AI - Recommendation Service
=====================================
Scores hotels with the trained models from ml/recsys/core.py:

  collaborative  SVD matrix factorisation (rating SVD + interaction SVD)
  content        hotel vectors (review-text TF-IDF, destination, style, amenities,
                 aspect quality) vs. a profile built from the user's history and/or
                 explicit preferences (travel style, aspect weights)
  sentiment      hotels ranked by mean sentiment of their reviews (trained classifier)
  hybrid         tuned blend of the three
  popularity     Bayesian-average rating baseline

Personalisation sources, in priority order:
  * a dataset user id ("demo persona"): the trained user factors and their real history
  * the logged-in user's own history (reviews they submitted + saved hotels), folded
    into the SVD with ridge regression
  * explicit preferences (travel style, aspect weights) for the content model
With none of these the response says so (`personalization.mode == "none"`).
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from services.hotel_service import get_hotel_store
from services.ml_model_loader import get_model_store, REPO_ROOT

logger = logging.getLogger(__name__)

ASPECT_KEYS = ["cleanliness", "service", "rooms", "location", "value"]
ASPECT_COL = {"location": "location_score"}          # hotel table column names
SAVED_IMPLICIT_RATING = 4.5                           # a saved hotel counts as a positive signal
MODEL_TYPES = ["hybrid", "collaborative", "content", "sentiment", "popularity"]


class RecommendationService:
    def __init__(self):
        self.hotel_store = get_hotel_store()
        self.model_store = get_model_store()
        self._persona_history: Optional[Dict[str, Dict[str, float]]] = None

    # ------------------------------------------------------------------ personas
    def _load_personas(self) -> Dict[str, Dict[str, float]]:
        if self._persona_history is None:
            import pandas as pd
            path = REPO_ROOT / "data" / "processed" / "synthetic_reviews.parquet"
            self._persona_history = {}
            if path.exists():
                df = pd.read_parquet(path, columns=["user_id", "hotel_id", "overall"])
                self._persona_history = {u: dict(zip(g["hotel_id"], g["overall"])) for u, g in df.groupby("user_id")}
        return self._persona_history

    def dataset_user_history(self, user_id: str) -> Optional[Dict[str, float]]:
        return self._load_personas().get(user_id)

    def list_personas(self, n: int = 6) -> List[Dict[str, Any]]:
        """A few real dataset users, each with a different favourite destination, for demos."""
        rec = self.model_store.require()
        hist = self._load_personas()
        loc = {h["hotel_id"]: h.get("location") for h in self.hotel_store.hotel_index.values()}
        styles = {h["hotel_id"]: (h.get("styles") or "").split(",") for h in self.hotel_store.hotel_index.values()}
        seen, out = set(), []
        for uid in sorted(hist):
            if not rec.cf.knows_user(uid):
                continue
            liked = [h for h, r in hist[uid].items() if r >= 4]
            if len(liked) < 5:
                continue
            dests = [loc.get(h) for h in liked if loc.get(h)]
            top_dest = max(set(dests), key=dests.count)
            if top_dest in seen:
                continue
            sty = [s for h in liked for s in styles.get(h, []) if s]
            top_styles = sorted(set(sty), key=lambda s: -sty.count(s))[:2]
            seen.add(top_dest)
            out.append({"user_id": uid, "reviews": len(hist[uid]), "favourite_destination": top_dest,
                        "favourite_styles": top_styles})
            if len(out) >= n:
                break
        return out

    # ------------------------------------------------------------------ main API
    def generate_recommendations(
        self,
        top_n: int = 10,
        user_id: Optional[str] = None,                 # dataset user id (persona), not the app account id
        history: Optional[Dict[str, float]] = None,    # app user's own hotel -> rating history
        exclude_ids: Optional[set] = None,
        destination: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        aspect_weights: Optional[Dict[str, float]] = None,
        travel_styles: Optional[List[str]] = None,
        model_type: str = "hybrid",
    ) -> Dict[str, Any]:
        rec = self.model_store.require()

        persona_hist = self.dataset_user_history(user_id) if user_id else None
        if user_id and persona_hist is None:
            raise ValueError(f"Unknown dataset user '{user_id}'")
        if persona_hist is not None:
            history, cf_user = dict(persona_hist), user_id
        else:
            history, cf_user = dict(history or {}), None

        pref = rec.content.preference_vector(styles=travel_styles or [])
        has_aspects = rec.content.aspect_fit(aspect_weights) is not None
        sc = rec.score_all(cf_user, history, pref, aspect_weights)
        key = {"hybrid": "hybrid", "collaborative": "collaborative", "content": "content",
               "sentiment": "sentiment", "popularity": "popularity"}[model_type]
        raw = np.asarray(sc[key], dtype=float)
        if model_type == "content" and sc["content_mode"] == "none":
            # cold start: no profile, so rank by overall aspect quality (mean z-score of the five aspects)
            raw = rec.content.aspect_z.mean(axis=1)
            sc["content_mode"] = "aspect quality (no profile yet)"
        scores = (raw - raw.min()) / (np.ptp(raw) or 1.0)

        hotels, _ = self.hotel_store.search(destination=destination, min_rating=min_rating, max_rating=max_rating,
                                            sort_by="avg_rating", sort_order="desc", page=1, page_size=1000)
        idx = {h: i for i, h in enumerate(rec.hotel_ids)}
        exclude = set(exclude_ids or ()) | (set(history) if persona_hist is not None else set())
        cands = [h for h in hotels if h["hotel_id"] in idx and h["hotel_id"] not in exclude]
        for h in cands:
            i = idx[h["hotel_id"]]
            h["score"] = round(float(scores[i]), 4)
            h["_i"] = i
        cands.sort(key=lambda h: h["score"], reverse=True)
        top = cands[:top_n]
        enriched = [self._enrich(h, r + 1, sc, rec, model_type, aspect_weights, travel_styles) for r, h in enumerate(top)]

        mode = ("dataset_user" if persona_hist is not None
                else "history" if history else "preferences" if (pref is not None or has_aspects) else "none")
        return {
            "recommendations": enriched,
            "total": len(cands),
            "model_used": model_type,
            "data_source": self.hotel_store.data_source,
            "scoring": self._describe(model_type, sc),
            "method_note": self._describe(model_type, sc),
            "personalization": {
                "mode": mode, "cf_mode": sc["cf_mode"], "content_mode": sc["content_mode"],
                "history_size": len(history), "hybrid_weights": {k: round(v, 3) for k, v in sc["weights"].items()},
            },
            "filters_applied": {"destination": destination, "min_rating": min_rating, "max_rating": max_rating},
        }

    @staticmethod
    def _describe(model_type: str, sc: dict) -> str:
        cf = {"trained": "trained user factors", "fold_in": "user folded in from own history",
              "item_bias": "no user information: item-bias prior only"}[sc["cf_mode"]]
        if model_type == "collaborative":
            return f"SVD collaborative filtering ({cf})"
        if model_type == "content":
            return f"Content-based similarity ({sc['content_mode']})"
        if model_type == "sentiment":
            return "Hotels ranked by mean review sentiment (TF-IDF + logistic regression)"
        if model_type == "popularity":
            return "Popularity baseline: Bayesian-average rating"
        w = sc["weights"]
        return (f"Hybrid: CF {w['cf']:.0%} ({cf}) + content {w['content']:.0%} ({sc['content_mode']}) "
                f"+ sentiment {w['sentiment']:.0%}")

    # ------------------------------------------------------------------ sentiment
    def analyze_review(self, text: str) -> Dict[str, Any]:
        return self.model_store.require().sentiment.analyze(text)

    # ------------------------------------------------------------------ explanations
    def explain_hotel(self, hotel_id: str, user_preferences: Optional[Dict] = None) -> Optional[Dict]:
        hotel = self.hotel_store.get_by_id(hotel_id)
        if not hotel:
            return None
        rec = self.model_store.require()
        aspects = {}
        for col in ["cleanliness", "service", "location_score", "rooms", "value"]:
            if hotel.get(col) is not None:
                aspects["location" if col == "location_score" else col] = round(float(hotel[col]), 2)
        mean_a = np.mean(list(aspects.values())) if aspects else 3.0
        strengths = [f"Strong {a} ({v:.1f}/5)" for a, v in aspects.items() if v >= mean_a + 0.25]
        weaknesses = [f"Weaker {a} ({v:.1f}/5)" for a, v in aspects.items() if v <= mean_a - 0.25]
        s = float(rec.hotel_sentiment[rec.hotel_ids.index(hotel_id)]) if hotel_id in rec.hotel_ids else 0.0
        summary = ("Guest reviews are strongly positive" if s > 0.3 else "Guest reviews are mostly positive" if s > 0.1
                   else "Guest reviews are mixed" if s > -0.1 else "Guest reviews are mostly negative")
        return {
            "hotel_id": hotel_id, "hotel_name": hotel.get("name", hotel_id),
            "overall_score": round((hotel.get("avg_rating") or 3.0) / 5.0, 3),
            "aspect_breakdown": aspects,
            "strengths": strengths or ["Balanced across all aspects"],
            "weaknesses": weaknesses,
            "sentiment_summary": f"{summary} (model sentiment {s:+.2f})",
            "similar_hotels": [x["hotel_id"] for x in self.hotel_store.get_similar(hotel_id, top_n=3)],
        }

    def _enrich(self, hotel, rank, sc, rec, model_type, aspect_weights, travel_styles) -> Dict:
        i = hotel.pop("_i")
        avg, n = hotel.get("avg_rating") or 3.0, hotel.get("review_count") or 0
        sent = float(rec.hotel_sentiment[i])
        factors = []
        styles = [s for s in (hotel.get("styles") or "").split(",") if s]
        matched = [s for s in styles if s in (travel_styles or [])]
        if matched:
            factors.append(f"Matches your travel style: {', '.join(matched)}")
        if aspect_weights:
            vals = {a: hotel.get(ASPECT_COL.get(a, a)) for a in ASPECT_KEYS}
            ranked = sorted(((aspect_weights.get(a, 1.0), a) for a in ASPECT_KEYS if vals[a] is not None), reverse=True)
            for w, a in ranked[:2]:
                if w > 1.0 and vals[a] >= 3.8:
                    factors.append(f"Strong {a} ({vals[a]:.1f}/5), which you weighted highly")
        if sc["cf_mode"] in ("trained", "fold_in") and sc["contributions"]["cf"][i] > 0.5 * sc["weights"]["cf"] \
                and model_type in ("hybrid", "collaborative"):
            factors.append("Liked by guests with a similar booking history")
        if sc["content_mode"] != "none" and sc["contributions"]["content"][i] > 0.5 * sc["weights"]["content"] \
                and model_type in ("hybrid", "content"):
            factors.append("Similar to hotels you have rated highly" if "history" in sc["content_mode"]
                           else "Close match to your stated preferences")
        if sent > 0.3:
            factors.append(f"Guest reviews are strongly positive (sentiment {sent:+.2f})")
        if avg >= 4.0:
            factors.append(f"Highly rated ({avg:.1f}/5 from {n} reviews)")
        if not factors:
            factors = [f"Rated {avg:.1f}/5 from {n} reviews"]

        contribution = ({k: round(float(v[i]), 4) for k, v in sc["contributions"].items()} if model_type == "hybrid"
                        else {model_type: round(hotel["score"], 4)})
        loc = hotel.get("location_score")
        return {
            **hotel,
            "hotel_name": hotel.get("name") or f"Hotel {hotel.get('hotel_id')}",
            "destination": hotel.get("location") or "Various",
            "aspect_scores": {a: (float(hotel[ASPECT_COL.get(a, a)]) if hotel.get(ASPECT_COL.get(a, a)) is not None else None)
                              for a in ASPECT_KEYS},
            "rank": rank,
            "match_percentage": int(round(hotel["score"] * 100)),
            "explanation": {"primary_reason": factors[0], "contributing_factors": factors,
                            "model_contribution": contribution},
            "is_trending": False,
        }
