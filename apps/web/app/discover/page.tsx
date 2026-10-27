"use client";

import { useState, useEffect, useTransition, Suspense, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  fetchRecommendations,
  fetchPersonas,
  fetchSavedHotelIds,
  setHotelSaved,
  Recommendation,
  Personalization,
  Persona,
  TRAVEL_STYLES,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ErrorBoundary } from "@/components/ErrorBoundary";

function DiscoverContent() {
  const searchParams = useSearchParams();
  const initialDestination = searchParams.get("destination") || "";
  const { token } = useAuth();

  const [destination, setDestination] = useState(initialDestination);
  const [minRating, setMinRating] = useState(3.0);
  const [modelType, setModelType] = useState("hybrid");
  const [weights, setWeights] = useState({
    cleanliness: 1.0,
    service: 1.0,
    location: 1.0,
    rooms: 1.0,
    value: 1.0,
  });

  const [styles, setStyles] = useState<string[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [persona, setPersona] = useState("");
  const [personalization, setPersonalization] = useState<Personalization | undefined>();

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<string | undefined>();
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [isPending, startTransition] = useTransition();

  const loadRecs = useCallback(
    async (
      destOverride?: string,
      modelOverride?: string,
      minRatingOverride?: number,
      weightsOverride?: typeof weights,
      stylesOverride?: string[],
      personaOverride?: string
    ) => {
      setLoading(true);
      const targetDest = destOverride !== undefined ? destOverride : destination;
      const targetModel = modelOverride !== undefined ? modelOverride : modelType;
      const targetMinRating = minRatingOverride !== undefined ? minRatingOverride : minRating;
      const targetWeights = weightsOverride !== undefined ? weightsOverride : weights;

      try {
        const data = await fetchRecommendations({
          destination: targetDest.trim() || undefined,
          min_rating: targetMinRating,
          model_type: targetModel,
          aspect_weights: targetWeights,
          travel_styles: stylesOverride !== undefined ? stylesOverride : styles,
          dataset_user_id: (personaOverride !== undefined ? personaOverride : persona) || undefined,
          token,
          top_n: 12,
        });
        setRecommendations(data.recommendations);
        setPersonalization(data.personalization);
        setDataSource(data.data_source);
        setError(null);
      } catch (e) {
        console.error("Failed to load recommendations:", e);
        setRecommendations([]);
        setError(e instanceof Error ? e.message : "Recommendations are unavailable.");
      } finally {
        setLoading(false);
      }
    },
    [destination, minRating, modelType, weights, styles, persona, token]
  );

  // Demo travelers + the logged-in user's saved hotels
  useEffect(() => {
    fetchPersonas().then((list) => {
      setPersonas(list);
      // Anonymous visitors start as a demo traveler so each model visibly personalises.
      let loggedIn = false;
      try { loggedIn = !!localStorage.getItem("tripsense_token"); } catch {}
      if (!loggedIn && list.length) {
        setPersona(list[0].user_id);
        loadRecs(undefined, undefined, undefined, undefined, undefined, list[0].user_id);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    if (token) fetchSavedHotelIds(token).then((ids) => setSavedIds(new Set(ids)));
  }, [token]);

  // Load on mount and whenever the ?destination= query param changes.
  // Filter state is intentionally read once per navigation, not on every edit.
  const urlDest = searchParams.get("destination") || "";
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDestination(urlDest);
    loadRecs(urlDest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlDest, token]);   // token is restored from localStorage after mount: reload so history is used

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    startTransition(() => {
      loadRecs(destination, modelType, minRating, weights, styles, persona);
    });
  };

  const handleModelChange = (newModel: string) => {
    setModelType(newModel);
    startTransition(() => {
      loadRecs(destination, newModel, minRating, weights, styles, persona);
    });
  };

  const toggleSave = (hotelId: string) => {
    if (token) {
      setHotelSaved(token, hotelId, !savedIds.has(hotelId)).catch((e) => console.error("save failed", e));
    }
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (next.has(hotelId)) {
        next.delete(hotelId);
      } else {
        next.add(hotelId);
      }
      return next;
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Hotel Recommendation Studio</h1>
          <p className="text-sm text-slate-400 mt-1">
            Multi-model hotel ranking with aspect-weighted tuning
          </p>
        </div>

        {/* Model Selector Tabs */}
        <div className="flex flex-wrap bg-slate-900 p-1.5 rounded-xl border border-slate-800 text-xs gap-1">
          {[
            { id: "collaborative", label: "Collaborative Filtering" },
            { id: "content", label: "Content-Based" },
            { id: "sentiment", label: "Sentiment Analysis" },
            { id: "hybrid", label: "Hybrid" },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => handleModelChange(m.id)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                modelType === m.id
                  ? "bg-cyan-500 text-white shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mt-8">
        {/* Filter & Aspect Tuning Sidebar */}
        <div className="lg:col-span-1 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 self-start sticky top-24">
          <form onSubmit={handleApplyFilters} className="space-y-6">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Destination Filter
              </label>
              <input
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g. Paris, New York, London..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Min Overall Rating</span>
                <span className="font-bold text-cyan-400">{minRating.toFixed(1)} ★</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="5.0"
                step="0.1"
                value={minRating}
                onChange={(e) => setMinRating(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Travel Style
              </label>
              <div className="flex flex-wrap gap-1.5">
                {TRAVEL_STYLES.map((t) => {
                  const on = styles.includes(t);
                  return (
                    <button
                      type="button"
                      key={t}
                      onClick={() => setStyles((prev) => (on ? prev.filter((x) => x !== t) : [...prev, t]))}
                      className={`px-2.5 py-1 rounded-lg text-xs capitalize border transition ${
                        on
                          ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                          : "text-slate-400 border-slate-800 hover:text-white"
                      }`}
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
            </div>

            {personas.length > 0 && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Browse As Demo Traveler
                </label>
                <select
                  value={persona}
                  onChange={(e) => setPersona(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                >
                  <option value="">Me (my preferences & history)</option>
                  {personas.map((p) => (
                    <option key={p.user_id} value={p.user_id}>
                      {p.user_id} · likes {p.favourite_destination}
                      {p.favourite_styles.length ? ` (${p.favourite_styles.join(", ")})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="pt-4 border-t border-slate-800">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
                Aspect Importance Weights
              </h3>

              <div className="space-y-3">
                {Object.entries(weights).map(([aspect, val]) => (
                  <div key={aspect}>
                    <div className="flex justify-between text-xs text-slate-400 mb-1 capitalize">
                      <span>{aspect}</span>
                      <span className="font-mono text-cyan-400">{val.toFixed(1)}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="3.0"
                      step="0.1"
                      value={val}
                      onChange={(e) =>
                        setWeights((prev) => ({ ...prev, [aspect]: parseFloat(e.target.value) }))
                      }
                      className="w-full accent-cyan-500 cursor-pointer"
                    />
                  </div>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || isPending}
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-2.5 rounded-xl text-sm transition shadow-lg shadow-cyan-600/20 disabled:opacity-50"
            >
              {loading || isPending ? "Computing Recommendations..." : "Apply & Recalculate"}
            </button>
          </form>
        </div>

        {/* Results Grid */}
        <div className="lg:col-span-3">
          {dataSource === "synthetic-demo" && (
            <div role="status" className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-300">
              Demo mode: these hotels are synthetic sample data, not real properties.
            </div>
          )}
          {!loading && !error && personalization && (
            <div role="status" className="mb-4 rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-4 py-2 text-xs text-slate-300">
              {personalization.mode === "dataset_user" &&
                `Personalized for demo traveler ${persona} using their ${personalization.history_size} reviews (trained SVD factors).`}
              {personalization.mode === "history" &&
                `Personalized from your ${personalization.history_size} saved/reviewed hotels${styles.length ? " and your travel style" : ""}.`}
              {personalization.mode === "preferences" &&
                "Personalized from your stated preferences (travel style / aspect weights). Save or review hotels to unlock collaborative filtering."}
              {personalization.mode === "none" &&
                "Not personalized yet: pick a travel style, adjust aspect weights, or log in and save/review hotels."}
            </div>
          )}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-64 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse"></div>
              ))}
            </div>
          ) : error ? (
            <div role="alert" className="text-center py-20 bg-slate-900/30 rounded-2xl border border-rose-500/30">
              <p className="text-lg text-rose-300">Recommendations are unavailable</p>
              <p className="text-sm text-slate-400 mt-2 max-w-xl mx-auto">{error}</p>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="text-center py-20 bg-slate-900/30 rounded-2xl border border-slate-800">
              <p className="text-lg text-slate-400">No hotels matched your selected criteria.</p>
              <button
                onClick={() => {
                  setDestination("");
                  setMinRating(1.0);
                  setWeights({
                    cleanliness: 1.0,
                    service: 1.0,
                    location: 1.0,
                    rooms: 1.0,
                    value: 1.0,
                  });
                  setStyles([]);
                  setPersona("");
                  loadRecs("", modelType, 1.0, {
                    cleanliness: 1.0,
                    service: 1.0,
                    location: 1.0,
                    rooms: 1.0,
                    value: 1.0,
                  }, [], "");
                }}
                className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-xl text-sm transition"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {recommendations.map((rec) => {
                const isSaved = savedIds.has(rec.hotel_id);
                const hotelTitle = rec.hotel_name || rec.name || `Hotel ${rec.hotel_id}`;
                const hotelLocation = rec.destination || rec.location || "Verified Location";
                const aspects = rec.aspect_scores || {};

                return (
                  <div
                    key={rec.hotel_id}
                    className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-cyan-500/30 transition flex flex-col justify-between shadow-lg"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                              #{rec.rank}
                            </span>
                            <span className="text-xs text-slate-400">{hotelLocation}</span>
                          </div>
                          <h3 className="text-lg font-bold text-white leading-tight line-clamp-2">
                            {hotelTitle}
                          </h3>
                        </div>

                        {/* Match Percentage Badge */}
                        <div className="text-right flex flex-col items-end shrink-0">
                          <span className="text-lg font-black text-emerald-400">{rec.match_percentage}%</span>
                          <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Match</span>
                        </div>
                      </div>

                      {/* Ratings Bar */}
                      <div className="flex items-center gap-3 mt-3 text-xs text-slate-300">
                        <span className="text-amber-400 font-bold">★ {rec.avg_rating?.toFixed(1) || "4.0"}</span>
                        <span className="text-slate-500">•</span>
                        <span>{(rec.review_count || 1).toLocaleString()} traveler reviews</span>
                      </div>

                      {/* Explanation */}
                      {rec.explanation && (
                        <div className="mt-4 p-3 rounded-xl bg-slate-950/80 border border-slate-800/60 text-xs">
                          <div className="font-semibold text-cyan-300 mb-1">
                            Why Recommended:
                          </div>
                          <p className="text-slate-400 leading-relaxed">
                            {rec.explanation.primary_reason}
                          </p>
                        </div>
                      )}

                      {/* Aspect Badges */}
                      {(aspects.cleanliness || aspects.service || aspects.location) && (
                        <div className="grid grid-cols-3 gap-2 mt-4 text-[11px]">
                          {aspects.cleanliness !== undefined && aspects.cleanliness !== null && (
                            <div className="bg-slate-800/40 p-1.5 rounded-lg border border-slate-800 text-center">
                              <span className="text-slate-400 block text-[10px]">Clean</span>
                              <span className="font-bold text-slate-200">
                                {Number(aspects.cleanliness).toFixed(1)}
                              </span>
                            </div>
                          )}
                          {aspects.service !== undefined && aspects.service !== null && (
                            <div className="bg-slate-800/40 p-1.5 rounded-lg border border-slate-800 text-center">
                              <span className="text-slate-400 block text-[10px]">Service</span>
                              <span className="font-bold text-slate-200">
                                {Number(aspects.service).toFixed(1)}
                              </span>
                            </div>
                          )}
                          {aspects.location !== undefined && aspects.location !== null && (
                            <div className="bg-slate-800/40 p-1.5 rounded-lg border border-slate-800 text-center">
                              <span className="text-slate-400 block text-[10px]">Location</span>
                              <span className="font-bold text-slate-200">
                                {Number(aspects.location).toFixed(1)}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
                      <button
                        onClick={() => toggleSave(rec.hotel_id)}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                          isSaved
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : "text-slate-400 hover:text-white border-slate-800 hover:bg-slate-800/60"
                        }`}
                      >
                        {isSaved ? "♥ Saved" : "♡ Save Hotel"}
                      </button>

                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono text-slate-500">
                          Score: {rec.score?.toFixed(3) || "0.000"}
                        </span>
                        <Link
                          href={`/hotels/${rec.hotel_id}`}
                          className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 transition"
                        >
                          Details →
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DiscoverPage() {
  return (
    <ErrorBoundary>
      <Suspense
        fallback={
          <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-400">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent mb-4"></div>
            <p>Loading Hotel Recommendation Studio...</p>
          </div>
        }
      >
        <DiscoverContent />
      </Suspense>
    </ErrorBoundary>
  );
}
