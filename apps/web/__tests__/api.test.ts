import { describe, it, expect, vi, afterEach } from "vitest";
import { fetchRecommendations, fetchAnalyticsOverview } from "@/lib/api";

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

  it("returns null for analytics when the API is down (no hardcoded metrics)", async () => {
    vi.stubGlobal("fetch", vi.fn(() => json({ detail: "missing" }, 503)));
    expect(await fetchAnalyticsOverview()).toBeNull();
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("offline"))));
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(await fetchAnalyticsOverview()).toBeNull();
  });
});
