import { describe, it, expect, vi, afterEach } from "vitest";
import {
  authenticatedApiFetch,
  fetchCurrentUser,
  getAuthHeaders,
  normalizeAccessToken,
} from "@/lib/auth-api";
import {
  fetchRecommendations,
  fetchAnalyticsOverview,
  fetchHotelReviews,
  fetchUserPreferences,
  setHotelSaved,
  submitReview,
  updateUserPreferences,
} from "@/lib/api";

const json = (body: unknown, status = 200) =>
  Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client never fabricates data", () => {
  it("surfaces the API error instead of returning fake hotels", async () => {
    vi.stubGlobal("fetch", vi.fn(() => json({ detail: "Hotel catalogue unavailable" }, 503)));
    await expect(fetchRecommendations({ top_n: 3 })).rejects.toThrow("Hotel catalogue unavailable");
  });

  it("surfaces network failures", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("offline"))));
    await expect(fetchRecommendations()).rejects.toThrow("offline");
  });

  it("returns recommendations with their data source", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => json({ data: { recommendations: [{ hotel_id: "h1" }], data_source: "synthetic-demo", scoring: "heuristic" } })),
    );
    const r = await fetchRecommendations();
    expect(r.recommendations).toHaveLength(1);
    expect(r.data_source).toBe("synthetic-demo");
  });

  it("loads submitted reviews for a hotel without fabricating data", async () => {
    const reviews = [{
      id: "review-1",
      rating: 5,
      text: "Wonderful stay",
      sentiment_label: "positive",
      sentiment_score: 0.9,
      created_at: "2025-01-02T12:00:00",
    }];
    const fetchMock = vi.fn();
    fetchMock.mockResolvedValue(json({ data: reviews }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchHotelReviews("hotel/with spaces")).resolves.toEqual(reviews);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/reviews/hotel/hotel%2Fwith%20spaces");

    vi.stubGlobal("fetch", vi.fn(() => json({ detail: "Review service unavailable" }, 503)));
    await expect(fetchHotelReviews("hotel-1")).rejects.toThrow("Review service unavailable");
  });

  it("returns null for analytics when the API is down (no hardcoded metrics)", async () => {
    vi.stubGlobal("fetch", vi.fn(() => json({ detail: "missing" }, 503)));
    expect(await fetchAnalyticsOverview()).toBeNull();
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("offline"))));
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(await fetchAnalyticsOverview()).toBeNull();
  });

  it("normalizes persisted bearer tokens before sending requests", async () => {
    expect(normalizeAccessToken(" Bearer saved-token ")).toBe("saved-token");
    expect(new Headers(getAuthHeaders("Bearer saved-token")).get("Authorization")).toBe("Bearer saved-token");
  });

  it("uses the current session to save hotels and submit reviews", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ success: true }))
      .mockResolvedValueOnce(json({ success: true }))
      .mockResolvedValueOnce(json({ data: { id: "r1", sentiment: { label: "positive" } } }));
    vi.stubGlobal("fetch", fetchMock);

    await setHotelSaved("valid-token", "hotel-1", true);
    await setHotelSaved("valid-token", "hotel-1", false);
    await submitReview("valid-token", { hotel_id: "hotel-1", text: "Great stay!" });

    for (const [url, options] of fetchMock.mock.calls) {
      expect(url).toContain("/api/v1/");
      expect(new Headers(options.headers).get("Authorization")).toBe("Bearer valid-token");
    }
  });

  it("loads and saves profile preferences through authenticated endpoints", async () => {
    const preferences = {
      destination: "Tokyo",
      min_rating: 4.2,
      travel_style: "luxury",
      cleanliness_weight: 2,
      location_weight: 1,
      rooms_weight: 1,
      service_weight: 1,
      value_weight: 1,
      sleep_quality_weight: 1,
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ data: preferences }))
      .mockResolvedValueOnce(json({ data: preferences }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchUserPreferences("valid-token")).resolves.toEqual(preferences);
    await expect(updateUserPreferences("valid-token", preferences)).resolves.toEqual(preferences);

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/users/me/preferences");
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get("Authorization")).toBe("Bearer valid-token");
    expect(fetchMock.mock.calls[1][1].method).toBe("PUT");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toEqual(preferences);
  });

  it("clears stale sessions after protected requests are rejected", async () => {
    const dispatch = vi.spyOn(window, "dispatchEvent");
    vi.stubGlobal("fetch", vi.fn(() => json({ detail: "Could not validate credentials" }, 401)));

    await expect(authenticatedApiFetch("http://localhost/protected", {}, "expired-token"))
      .rejects.toThrow("Your session has expired");
    await expect(setHotelSaved("expired-token", "hotel-1", true))
      .rejects.toThrow("Your session has expired");
    await expect(submitReview("expired-token", { hotel_id: "hotel-1", text: "Great stay!" }))
      .rejects.toThrow("Your session has expired");
    expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: "tripsense:auth-expired" }));
    expect(await fetchCurrentUser("expired-token")).toBeNull();
  });
});
