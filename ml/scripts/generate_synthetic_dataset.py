"""
TripSense AI - Synthetic Dataset Generator
==========================================
The original tripadvisor_reviews.csv has one review per hotel_id, so no
user/hotel structure can be learned from it. This script generates a
reproducible synthetic dataset with a *known, learnable* structure:

  * Hotels have a destination, star class, style tags (family, business, ...),
    amenities, per-aspect quality, and a hidden "taste" vector.
  * Users have preferred destinations and styles, aspect-importance weights,
    a strictness bias and a hidden taste vector.
  * Which hotels a user reviews depends on destination/style affinity.
  * The rating depends on (a) hotel quality weighted by what the user cares
    about, (b) style match, (c) a low-rank user x hotel taste interaction
    (this is what matrix factorisation can learn) and (d) noise.
  * Review text is built from aspect-specific sentences whose polarity follows
    the aspect sub-ratings, plus a sentence describing the hotel's destination /
    style / amenities (this is what content-based models can learn). A small
    fraction of closing sentences intentionally disagree with the rating.

Everything is seeded (default 42): the same arguments always produce
byte-identical parquet files.

Outputs (under data/processed/):
  synthetic_reviews.parquet               - all reviews
  train.parquet / test.parquet            - per-user chronological split (also in splits/)
  features/hotel_features_complete.parquet
  features/user_features_complete.parquet
  hotel_catalog.parquet                   - hotel attributes (no review statistics)
  dataset_stats.json                      - statistics served by the analytics API
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.recsys.core import per_user_chronological_split  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

SEED = 42
TEST_FRACTION = 0.2          # last 20% of every user's reviews (by date) are held out
START_DATE = datetime(2022, 1, 1)
SPAN_DAYS = 900

DESTINATIONS = [
    "Paris", "London", "New York", "Tokyo", "Rome", "Barcelona", "Sydney", "Dubai",
    "Amsterdam", "Prague", "Vienna", "Singapore", "Bangkok", "Istanbul", "Lisbon",
]
ASPECTS = ["cleanliness", "service", "rooms", "location", "value"]
STYLES = ["family", "business", "romantic", "budget", "luxury", "adventure"]

STYLE_AMENITIES = {
    "family":    ["kids club", "family rooms", "pool", "free breakfast"],
    "business":  ["business center", "meeting rooms", "airport shuttle", "fast wifi"],
    "romantic":  ["spa", "rooftop bar", "candlelit restaurant", "balcony rooms"],
    "budget":    ["free wifi", "self check-in", "shared kitchen", "free breakfast"],
    "luxury":    ["spa", "concierge", "fine dining", "infinity pool"],
    "adventure": ["tour desk", "bike rental", "hiking trails", "beach access"],
}

PREFIX = ["Grand", "Royal", "Harbor", "City", "Ocean", "Mountain", "Boutique", "Elite",
          "Premier", "Classic", "Heritage", "Garden", "Central", "Riverside", "Sunset"]
SUFFIX = ["Palace", "Inn", "View", "Suites", "Retreat", "Lodge", "Resort", "Manor",
          "Plaza", "House", "Residence", "Stay"]

# ---------------------------------------------------------------------------
# Text vocabulary: several phrasings per (aspect, polarity)
# ---------------------------------------------------------------------------
ASPECT_PHRASES = {
    "cleanliness": {
        "pos": ["The room was spotless and smelled fresh.", "Everything was impeccably clean.",
                "Housekeeping did a superb job, immaculate bathroom.", "Very clean linens and tidy common areas."],
        "neu": ["Cleanliness was acceptable, nothing special.", "The room was reasonably clean."],
        "neg": ["The room was dirty and the bathroom had mold.", "Stained sheets and dusty corners, not clean at all.",
                "Cleanliness was a real problem, we found hair in the shower.", "Filthy carpet and a musty smell."],
    },
    "service": {
        "pos": ["The staff were friendly and incredibly helpful.", "Check-in was quick and the team went above and beyond.",
                "Attentive, welcoming service from everyone.", "Reception staff were courteous and solved every request."],
        "neu": ["Service was fine, staff were polite but slow.", "The staff were okay, average service."],
        "neg": ["The staff were rude and dismissive.", "Terrible service, nobody answered our requests.",
                "Reception was unhelpful and check-in took forever.", "Unfriendly team and ignored complaints."],
    },
    "rooms": {
        "pos": ["Spacious, comfortable room with a great bed.", "Beautifully designed room, very quiet and cozy.",
                "The suite was luxurious with a superb view.", "Comfortable mattress and modern fittings."],
        "neu": ["The room was an average size and decently equipped.", "Room was fine but a little dated."],
        "neg": ["The room was tiny, noisy and outdated.", "Uncomfortable bed and broken air conditioning.",
                "Cramped room with thin walls and a leaking tap.", "Dark, shabby room that needed renovation."],
    },
    "location": {
        "pos": ["Perfect location, steps from the main sights.", "Ideally located with great transport links.",
                "Wonderful neighbourhood, everything within walking distance.", "Superb central location."],
        "neu": ["Location was okay, a short taxi ride from the centre.", "Reasonably located, a bit of a walk to the metro."],
        "neg": ["The location was inconvenient and far from everything.", "Awful area, noisy at night and far from transport.",
                "Remote location, we needed a taxi for every trip.", "Poor location with nothing nearby."],
    },
    "value": {
        "pos": ["Excellent value for money.", "Great price for what you get, a real bargain.",
                "Worth every penny.", "Very reasonable rates for the quality."],
        "neu": ["Fair price, about what you would expect.", "Value was average for the area."],
        "neg": ["Overpriced for what it offers.", "Terrible value, not worth the price at all.",
                "Way too expensive for such poor quality.", "We felt ripped off by the rates."],
    },
}
CLOSING = {
    "pos": ["Would definitely stay again.", "Highly recommended!", "We had a wonderful stay overall.",
            "An excellent hotel, we loved it."],
    "neu": ["It was an okay stay overall.", "Decent hotel, but nothing memorable.", "Average experience, mixed feelings."],
    "neg": ["Would not recommend this hotel.", "A disappointing stay overall.",
            "We will not be coming back.", "Very disappointed, avoid if you can."],
}
# Short opinion sentences ("The staff was awful.") widen the vocabulary beyond the long templates
GENERIC_NOUNS = {
    "cleanliness": ["room", "bathroom", "bedding", "hotel"],
    "service": ["staff", "reception", "service", "front desk"],
    "rooms": ["room", "bed", "suite", "view"],
    "location": ["location", "neighbourhood", "area"],
    "value": ["price", "rate", "deal"],
}
GENERIC_ADJ = {
    "pos": ["great", "amazing", "lovely", "wonderful", "excellent", "fantastic", "perfect", "superb",
            "fabulous", "brilliant", "friendly", "comfortable", "clean", "helpful", "good"],
    "neu": ["fine", "okay", "average", "decent", "acceptable", "ordinary", "so-so", "mediocre"],
    "neg": ["awful", "terrible", "horrible", "poor", "bad", "disgusting", "dreadful", "disappointing",
            "noisy", "dirty", "rude", "unacceptable", "worst", "uncomfortable"],
}
GENERIC_TEMPLATES = ["The {noun} was {adj}.", "{Adj} {noun}.", "Honestly the {noun} was really {adj}.",
                     "We found the {noun} {adj}."]
DESCRIPTOR_TEMPLATES = [
    "Stayed here for a {style} trip to {dest} and the {amenity} stood out.",
    "A good choice in {dest} if you want a {style} stay, the {amenity} is a highlight.",
    "We visited {dest} and picked this {style}-oriented hotel for its {amenity}.",
    "The {amenity} suits a {style} visit to {dest}.",
]


# ---------------------------------------------------------------------------
# Catalogue and users
# ---------------------------------------------------------------------------
def generate_hotels(rng: np.random.Generator, n_hotels: int) -> pd.DataFrame:
    stars = rng.choice([2, 3, 4, 5], size=n_hotels, p=[0.15, 0.35, 0.33, 0.17])
    dests = rng.choice(DESTINATIONS, size=n_hotels)
    rows = []
    for i in range(n_hotels):
        star = int(stars[i])
        pool = [s for s in STYLES if not (s == "luxury" and star < 4) and not (s == "budget" and star > 3)]
        n_styles = 1 if rng.random() < 0.6 else 2
        styles = list(rng.choice(pool, size=min(n_styles, len(pool)), replace=False))
        amenities = []
        for s in styles:
            amenities += list(rng.choice(STYLE_AMENITIES[s], size=2, replace=False))
        amenities = sorted(set(amenities))
        base = 0.25 + 0.13 * (star - 2) + rng.normal(0, 0.08)           # star class drives quality
        quality = np.clip(base + rng.normal(0, 0.10, size=len(ASPECTS)), 0.03, 0.97)
        taste = rng.normal(0, 1, size=4)
        for s in styles:                                                # taste is partly style-driven
            taste[STYLES.index(s) % 4] += 0.8
        row = {
            "hotel_id": f"hotel_{i:04d}",
            "name": f"{PREFIX[rng.integers(len(PREFIX))]} {dests[i]} {SUFFIX[rng.integers(len(SUFFIX))]}",
            "location": str(dests[i]),
            "star_class": star,
            "price_per_night": int(round(45 + 55 * (star - 2) + rng.normal(0, 18))),
            "styles": ",".join(styles),
            "amenities": ",".join(amenities),
            "_taste": taste,
        }
        for a, q in zip(ASPECTS, quality):
            row[f"q_{a}"] = float(q)
        rows.append(row)
    return pd.DataFrame(rows)


def generate_users(rng: np.random.Generator, n_users: int) -> pd.DataFrame:
    rows = []
    for i in range(n_users):
        n_s = 1 if rng.random() < 0.5 else 2
        n_d = 1 if rng.random() < 0.6 else 2
        rows.append({
            "user_id": f"user_{i:05d}",
            "pref_styles": list(rng.choice(STYLES, size=n_s, replace=False)),
            "pref_dests": list(rng.choice(DESTINATIONS, size=n_d, replace=False)),
            "aspect_w": rng.dirichlet(np.ones(len(ASPECTS)) * 1.2),
            "bias": float(rng.normal(0, 0.3)),
            "_taste": rng.normal(0, 1, size=4),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Review simulation
# ---------------------------------------------------------------------------
def _polarity(score: float) -> str:
    return "pos" if score >= 4 else ("neg" if score <= 2 else "neu")


def _review_text(rng, hotel, aspect_scores, aspect_w, overall) -> str:
    n_mention = int(rng.integers(2, 4))
    # users talk mostly about what they care about
    mentioned = rng.choice(len(ASPECTS), size=n_mention, replace=False, p=aspect_w / aspect_w.sum())
    parts = []
    for ai in mentioned:
        a = ASPECTS[ai]
        pool = ASPECT_PHRASES[a][_polarity(aspect_scores[a])]
        parts.append(pool[rng.integers(len(pool))])
    for ai in rng.choice(len(ASPECTS), size=int(rng.integers(1, 3)), replace=False):
        a = ASPECTS[ai]
        adjs = GENERIC_ADJ[_polarity(aspect_scores[a])]
        adj = adjs[rng.integers(len(adjs))]
        nouns = GENERIC_NOUNS[a]
        parts.append(GENERIC_TEMPLATES[rng.integers(len(GENERIC_TEMPLATES))].format(
            noun=nouns[rng.integers(len(nouns))], adj=adj, Adj=adj.capitalize()))
    style = hotel["styles"].split(",")[0]
    amen = hotel["amenities"].split(",")
    parts.append(DESCRIPTOR_TEMPLATES[rng.integers(len(DESCRIPTOR_TEMPLATES))].format(
        style=style, dest=hotel["location"], amenity=amen[rng.integers(len(amen))]))
    pol = _polarity(overall)
    if rng.random() < 0.10:                                  # deliberate label noise
        pol = str(rng.choice([p for p in ("pos", "neu", "neg") if p != pol]))
    closing = CLOSING[pol]
    parts.append(closing[rng.integers(len(closing))])
    order = rng.permutation(len(parts) - 1)                  # keep closing last
    return " ".join([parts[j] for j in order] + [parts[-1]])


def generate_reviews(rng, hotels, users, min_reviews, max_reviews) -> pd.DataFrame:
    n_hotels = len(hotels)
    h_dest = hotels["location"].values
    h_styles = [set(s.split(",")) for s in hotels["styles"]]
    h_taste = np.stack(hotels["_taste"].values)
    h_q = hotels[[f"q_{a}" for a in ASPECTS]].values
    h_pop = rng.normal(0, 0.5, size=n_hotels)               # latent visibility
    rows, rid = [], 0
    for _, u in users.iterrows():
        dest_m = np.array([1.0 if d in u["pref_dests"] else 0.0 for d in h_dest])
        pref_styles = set(u["pref_styles"])
        style_m = np.array([len(pref_styles & s) / len(pref_styles) for s in h_styles])
        taste = np.tanh(h_taste @ u["_taste"] / 3.0)
        logits = 2.0 * dest_m + 1.2 * style_m + 0.8 * taste + 0.4 * h_pop
        p = np.exp(logits - logits.max())
        p /= p.sum()
        n = int(rng.integers(min_reviews, max_reviews + 1))
        chosen = rng.choice(n_hotels, size=n, replace=False, p=p)
        days = np.sort(rng.integers(0, SPAN_DAYS, size=n))
        for hi, day in zip(chosen, days):
            q_user = float(h_q[hi] @ u["aspect_w"])
            r_star = (3.2 + 3.2 * (q_user - 0.55) + 1.0 * style_m[hi] + 0.9 * taste[hi]
                      + u["bias"] + rng.normal(0, 0.45))
            overall = int(np.clip(round(r_star), 1, 5))
            sub = {}
            for k, a in enumerate(ASPECTS):
                v = 1 + 4 * (0.65 * h_q[hi, k] + 0.35 * (overall - 1) / 4) + rng.normal(0, 0.45)
                sub[a] = float(np.clip(round(v), 1, 5))
            hotel = hotels.iloc[hi]
            date = START_DATE + timedelta(days=int(day))
            rows.append({
                "review_id": f"rev_{rid:07d}", "user_id": u["user_id"], "hotel_id": hotel["hotel_id"],
                "overall": overall, **sub,
                "review_text": _review_text(rng, hotel, sub, u["aspect_w"], overall),
                "date_stayed": date.strftime("%Y-%m"), "post_date": date.strftime("%Y-%m-%d"),
                "is_synthetic": True,
            })
            rid += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------
def build_hotel_features(reviews: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    agg = reviews.groupby("hotel_id").agg(
        review_count=("review_id", "count"), avg_rating=("overall", "mean"), rating_std=("overall", "std"),
        cleanliness=("cleanliness", "mean"), service=("service", "mean"), rooms=("rooms", "mean"),
        location_score=("location", "mean"), value=("value", "mean"),
        pct_positive=("overall", lambda x: (x >= 4).mean()),
    ).reset_index()
    for c in ["avg_rating", "rating_std", "cleanliness", "service", "rooms", "location_score", "value", "pct_positive"]:
        agg[c] = agg[c].round(3)
    return agg.merge(catalog, on="hotel_id", how="left")


def build_user_features(reviews: pd.DataFrame) -> pd.DataFrame:
    agg = reviews.groupby("user_id").agg(
        total_reviews=("review_id", "count"), avg_rating_given=("overall", "mean"),
        rating_std=("overall", "std"), distinct_hotels=("hotel_id", "nunique")).reset_index()
    agg["avg_rating_given"] = agg["avg_rating_given"].round(3)
    return agg


def dataset_stats(reviews, train, test) -> dict:
    per_hotel = reviews.groupby("hotel_id").size()
    per_user = reviews.groupby("user_id").size()
    dist = reviews["overall"].value_counts(normalize=True).sort_index()
    return {
        "total_reviews": int(len(reviews)), "total_users": int(reviews["user_id"].nunique()),
        "total_hotels": int(reviews["hotel_id"].nunique()),
        "train_reviews": int(len(train)), "test_reviews": int(len(test)),
        "avg_rating": round(float(reviews["overall"].mean()), 3),
        "rating_std": round(float(reviews["overall"].std()), 3),
        "rating_distribution": [{"rating": str(int(k)), "percentage": round(float(v) * 100, 1)} for k, v in dist.items()],
        "reviews_per_hotel": {"mean": round(float(per_hotel.mean()), 1), "min": int(per_hotel.min()), "max": int(per_hotel.max())},
        "reviews_per_user": {"mean": round(float(per_user.mean()), 1), "min": int(per_user.min()), "max": int(per_user.max())},
        "sparsity_percent": round(100 * (1 - len(reviews) / (reviews["user_id"].nunique() * reviews["hotel_id"].nunique())), 2),
        "date_range": {"start": reviews["post_date"].min(), "end": reviews["post_date"].max()},
        "split": "per-user chronological: each user's latest 20% of reviews held out",
        "seed": SEED, "is_synthetic": True,
    }


# ---------------------------------------------------------------------------
def generate(n_hotels=500, n_users=3000, min_reviews=10, max_reviews=30, seed=SEED):
    rng = np.random.default_rng(seed)
    hotels = generate_hotels(rng, n_hotels)
    users = generate_users(rng, n_users)
    reviews = generate_reviews(rng, hotels, users, min_reviews, max_reviews)
    catalog = hotels[["hotel_id", "name", "location", "star_class", "price_per_night", "styles", "amenities"]].copy()
    return reviews, catalog


def main():
    ap = argparse.ArgumentParser(description="Generate the TripSense synthetic dataset")
    ap.add_argument("--n-hotels", type=int, default=500)
    ap.add_argument("--n-users", type=int, default=3000)
    ap.add_argument("--min-reviews-per-user", type=int, default=10)
    ap.add_argument("--max-reviews-per-user", type=int, default=30)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--output-dir", type=str, default=None)
    args = ap.parse_args()

    out = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parents[2] / "data" / "processed"
    (out / "features").mkdir(parents=True, exist_ok=True)
    (out / "splits").mkdir(parents=True, exist_ok=True)

    reviews, catalog = generate(args.n_hotels, args.n_users, args.min_reviews_per_user,
                                args.max_reviews_per_user, args.seed)
    train, test = per_user_chronological_split(reviews)

    reviews.to_parquet(out / "synthetic_reviews.parquet", index=False)
    catalog.to_parquet(out / "hotel_catalog.parquet", index=False)
    for d in (out, out / "splits"):
        train.to_parquet(d / "train.parquet", index=False)
        test.to_parquet(d / "test.parquet", index=False)
    build_hotel_features(reviews, catalog).to_parquet(out / "features" / "hotel_features_complete.parquet", index=False)
    build_user_features(reviews).to_parquet(out / "features" / "user_features_complete.parquet", index=False)
    stats = dataset_stats(reviews, train, test)
    (out / "dataset_stats.json").write_text(json.dumps(stats, indent=2))

    logger.info("Reviews %d | users %d | hotels %d | train %d | test %d",
                len(reviews), stats["total_users"], stats["total_hotels"], len(train), len(test))
    logger.info("Reviews/hotel %s | reviews/user %s | avg rating %.3f",
                stats["reviews_per_hotel"], stats["reviews_per_user"], stats["avg_rating"])
    logger.info("Rating distribution %s", stats["rating_distribution"])


if __name__ == "__main__":
    main()
