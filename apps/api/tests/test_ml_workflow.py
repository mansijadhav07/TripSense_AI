"""
End-to-end tests of the ML-backed user workflow, against the real trained artifacts
(artifacts/models/recommender.pkl) and the real catalogue. Nothing here is mocked.

Run `python ml/scripts/generate_synthetic_dataset.py && python ml/scripts/train_and_evaluate.py`
first if the artifacts are missing.
"""
import uuid
from collections import Counter

import pytest

REC = "/api/v1/recommendations/generate"


def _recs(client, **body):
    body.setdefault("top_n", 10)
    r = client.post(REC, json=body)
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.fixture
def user_token(client):
    email = f"wf_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "WorkflowPass123!"})
    assert r.status_code == 201, r.text
    return r.json()["data"]["token"]["access_token"]


def test_all_models_are_loaded(client):
    ready = client.get("/ready").json()
    assert ready["checks"]["ml_models"].startswith("loaded")


@pytest.mark.parametrize("model", ["hybrid", "collaborative", "content", "sentiment", "popularity"])
def test_every_model_type_returns_ranked_scores(client, model):
    body = {"model_type": model, "travel_styles": ["family"],
            "aspect_weights": {"cleanliness": 2.0, "service": 1.0, "location": 0.5, "rooms": 1.0, "value": 1.0}}
    data = _recs(client, **body)
    scores = [r["score"] for r in data["recommendations"]]
    assert len(scores) == 10
    assert scores == sorted(scores, reverse=True) and len(set(scores)) > 1   # real, varying scores


def test_travel_style_preference_drives_content_ranking(client):
    lux = _recs(client, model_type="content", travel_styles=["luxury"])["recommendations"]
    bud = _recs(client, model_type="content", travel_styles=["budget"])["recommendations"]
    assert {r["hotel_id"] for r in lux}.isdisjoint({r["hotel_id"] for r in bud})
    assert sum("luxury" in r["styles"] for r in lux) >= 8
    assert sum("budget" in r["styles"] for r in bud) >= 8


def test_aspect_weights_change_ranking(client):
    def top(aspect):
        w = {a: 0.0 for a in ("cleanliness", "service", "location", "rooms", "value")}
        w[aspect] = 3.0
        return _recs(client, model_type="content", aspect_weights=w, top_n=5)["recommendations"]
    clean, value = top("cleanliness"), top("value")
    assert [r["hotel_id"] for r in clean] != [r["hotel_id"] for r in value]
    all_hotels = client.get("/api/v1/hotels/search?page_size=100&sort_by=cleanliness").json()["data"]["hotels"]
    assert min(r["aspect_scores"]["cleanliness"] for r in clean) > 4.0
    assert min(r["aspect_scores"]["value"] for r in value) > 4.0
    assert len(all_hotels) == 100


def test_untouched_preferences_are_reported_as_not_personalised(client):
    data = _recs(client, model_type="hybrid")
    assert data["personalization"]["mode"] == "none"
    assert data["personalization"]["cf_mode"] == "item_bias"
    r = client.post(REC, json={"model_type": "content"})
    assert r.status_code == 200         # cold start falls back to aspect quality, labelled as such
    assert "no profile" in r.json()["data"]["personalization"]["content_mode"]


def test_models_return_different_rankings_without_a_profile(client):
    tops = {m: [h["hotel_id"] for h in _recs(client, model_type=m, top_n=10)["recommendations"]]
            for m in ("popularity", "collaborative", "content", "sentiment")}
    assert len({tuple(v) for v in tops.values()}) >= 3 and all(tops.values())


def test_dataset_user_gets_trained_cf_and_distinct_results(client):
    a = _recs(client, dataset_user_id="user_00001")
    b = _recs(client, dataset_user_id="user_00004")
    assert a["personalization"]["cf_mode"] == "trained" and a["personalization"]["mode"] == "dataset_user"
    ids_a = [r["hotel_id"] for r in a["recommendations"]]
    ids_b = [r["hotel_id"] for r in b["recommendations"]]
    assert ids_a != ids_b
    assert client.post(REC, json={"dataset_user_id": "nobody"}).status_code == 422


def test_personas_endpoint(client):
    personas = client.get("/api/v1/recommendations/personas").json()["data"]
    assert len(personas) >= 3 and len({p["favourite_destination"] for p in personas}) == len(personas)


def test_saved_hotels_personalise_via_fold_in(client, user_token):
    h = {"Authorization": f"Bearer {user_token}"}
    before = _recs(client, model_type="hybrid")
    tokyo = client.get("/api/v1/hotels/search?destination=Tokyo&page_size=3").json()["data"]["hotels"]
    for hotel in tokyo:
        assert client.post("/api/v1/users/me/saved-hotels", json={"hotel_id": hotel["hotel_id"]}, headers=h).status_code == 201
    r = client.post(REC, json={"top_n": 10, "model_type": "hybrid"}, headers=h)
    data = r.json()["data"]
    assert data["personalization"]["cf_mode"] == "fold_in" and data["personalization"]["history_size"] == 3
    dests = Counter(x["location"] for x in data["recommendations"])
    assert dests["Tokyo"] >= 6, dests          # learned from three saved Tokyo hotels
    assert [x["hotel_id"] for x in data["recommendations"]] != [x["hotel_id"] for x in before["recommendations"]]


def test_review_submission_runs_sentiment_model_and_feeds_history(client, user_token):
    h = {"Authorization": f"Bearer {user_token}"}
    hotel_id = _recs(client, model_type="hybrid", travel_styles=["family"])["recommendations"][0]["hotel_id"]
    pos = client.post("/api/v1/reviews", headers=h, json={
        "hotel_id": hotel_id, "rating": 5,
        "text": "Spotless room, friendly staff and a perfect location. Would definitely stay again!"})
    neg = client.post("/api/v1/reviews", headers=h, json={
        "hotel_id": hotel_id, "rating": 1,
        "text": "Dirty room, rude staff and terrible value. Would not recommend this hotel."})
    assert pos.status_code == neg.status_code == 201
    assert pos.json()["data"]["sentiment"]["label"] == "positive" and pos.json()["data"]["sentiment"]["score"] > 0.5
    assert neg.json()["data"]["sentiment"]["label"] == "negative" and neg.json()["data"]["sentiment"]["score"] < -0.5
    stored = client.get(f"/api/v1/reviews/hotel/{hotel_id}").json()["data"]
    assert {s["sentiment_label"] for s in stored} == {"positive", "negative"}
    after = client.post(REC, json={"top_n": 10, "model_type": "hybrid"}, headers=h).json()["data"]
    assert hotel_id not in [x["hotel_id"] for x in after["recommendations"]]     # already reviewed
    assert after["personalization"]["history_size"] == 1      # two reviews of one hotel -> one averaged entry


def test_review_requires_auth_and_valid_hotel(client, user_token):
    body = {"hotel_id": "hotel_0001", "text": "Nice place to stay."}
    assert client.post("/api/v1/reviews", json=body).status_code == 401
    h = {"Authorization": f"Bearer {user_token}"}
    assert client.post("/api/v1/reviews", headers=h, json={**body, "hotel_id": "nope"}).status_code == 404
    assert client.post("/api/v1/reviews", headers=h, json={**body, "rating": 9}).status_code == 422


def test_sentiment_analyze_endpoint_probabilities(client):
    r = client.post("/api/v1/reviews/analyze", json={"text": "Lovely hotel, amazing staff and a great breakfast!"})
    d = r.json()["data"]
    assert d["label"] == "positive"
    assert abs(sum(d["probabilities"].values()) - 1) < 1e-3
    neg = client.post("/api/v1/reviews/analyze", json={"text": "Worst stay ever, dirty bathroom and rude reception."}).json()["data"]
    assert neg["label"] == "negative" and neg["score"] < d["score"]
