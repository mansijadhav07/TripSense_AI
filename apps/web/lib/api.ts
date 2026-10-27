/**
 * TripSense AI - Web API Client
 *
 * Connects the Next.js frontend to the FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Hotel {
  hotel_id: string;
  name?: string;
  location?: string;
  avg_rating: number;
  review_count: number;
  cleanliness?: number;
  service?: number;
  location_score?: number;
  rooms?: number;
  value?: number;
  sleep_quality?: number;
  sentiment_score?: number;
}

export interface Recommendation {
  hotel_id: string;
  hotel_name?: string;
  name?: string;
  destination?: string;
  location?: string;
  avg_rating: number;
  review_count: number;
  score: number;
  match_percentage: number;
  rank: number;
  explanation: {
    primary_reason: string;
    contributing_factors: string[];
    model_contribution?: Record<string, number>;
  };
  aspect_scores?: {
    cleanliness?: number;
    service?: number;
    location?: number;
    rooms?: number;
    value?: number;
  };
}

export interface RecommendationParams {
  token?: string | null;
  travel_styles?: string[];
  dataset_user_id?: string;
  destination?: string;
  min_rating?: number;
  top_n?: number;
  model_type?: string;
  aspect_weights?: {
    cleanliness: number;
    service: number;
    location: number;
    rooms: number;
    value: number;
  };
}

export interface Personalization {
  mode: "dataset_user" | "history" | "preferences" | "none";
  cf_mode: string;
  content_mode: string;
  history_size: number;
  hybrid_weights: Record<string, number>;
}

export interface RecommendationResult {
  recommendations: Recommendation[];
  data_source?: string;
  scoring?: string;
  personalization?: Personalization;
}

export const TRAVEL_STYLES = ["family", "business", "romantic", "budget", "luxury", "adventure"] as const;

export interface Persona {
  user_id: string;
  reviews: number;
  favourite_destination: string;
  favourite_styles: string[];
}

export interface SentimentResult {
  label: "negative" | "neutral" | "positive";
  score: number;
  confidence: number;
  probabilities: Record<string, number>;
}

async function errorDetail(res: Response): Promise<string> {
  try {
    const j = await res.json();
    return typeof j?.detail === "string" ? j.detail : res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function fetchRecommendations(params: RecommendationParams = {}): Promise<RecommendationResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(params.token ? { Authorization: `Bearer ${params.token}` } : {}),
    },
    body: JSON.stringify({
      top_n: params.top_n || 12,
      model_type: params.model_type || "hybrid",
      travel_styles: params.travel_styles?.length ? params.travel_styles : null,
      dataset_user_id: params.dataset_user_id || null,
      filters: {
        destination: params.destination || null,
        min_rating: params.min_rating || null,
      },
      aspect_weights: params.aspect_weights || {
        cleanliness: 1.0,
        service: 1.0,
        location: 1.0,
        rooms: 1.0,
        value: 1.0,
      },
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(await errorDetail(res));
  }

  const json = await res.json();
  const data = json?.data ?? {};
  return {
    recommendations: Array.isArray(data.recommendations) ? data.recommendations : [],
    data_source: data.data_source,
    scoring: data.scoring,
    personalization: data.personalization,
  };
}

export async function fetchPersonas(): Promise<Persona[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/personas`, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()).data ?? [];
  } catch {
    return [];
  }
}

/** Sentiment of arbitrary text (not stored). */
export async function analyzeSentiment(text: string): Promise<SentimentResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/reviews/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return (await res.json()).data;
}

export interface SubmittedReview {
  id: string;
  hotel_id: string;
  rating: number | null;
  text: string;
  sentiment: SentimentResult;
}

export async function submitReview(
  token: string,
  review: { hotel_id: string; text: string; rating?: number | null }
): Promise<SubmittedReview> {
  const res = await fetch(`${API_BASE_URL}/api/v1/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(review),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return (await res.json()).data;
}

export async function setHotelSaved(token: string, hotelId: string, saved: boolean): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/users/me/saved-hotels`;
  const res = saved
    ? await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ hotel_id: hotelId }),
      })
    : await fetch(`${url}/${encodeURIComponent(hotelId)}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
  if (!res.ok && res.status !== 404) throw new Error(await errorDetail(res));
}

export async function fetchSavedHotelIds(token: string): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/users/me/saved-hotels`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return [];
    return ((await res.json()).data ?? []).map((s: { hotel_id: string }) => s.hotel_id);
  } catch {
    return [];
  }
}

export async function fetchHotelDetail(hotelId: string): Promise<Hotel | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/hotels/${encodeURIComponent(hotelId)}`, {
      cache: "no-store",
    });
    if (res.ok) {
      const json = await res.json();
      return json.data;
    }
  } catch (e) {
    console.error("fetchHotelDetail error:", e);
  }
  return null;
}

export interface DatasetSummary {
  total_reviews: number;
  total_users: number;
  total_hotels: number;
  avg_rating: number;
  rating_std: number;
  sparsity_percent: number;
  date_range?: { start: string; end: string };
  hotel_id_is_unique_per_row?: boolean;
  data_warning?: string;
}

export interface ModelMetrics {
  model_name: string;
  model_type: string;
  description: string;
  status: "evaluated" | "not_evaluable";
  reason?: string | null;
  precision_at_10: number | null;
  recall_at_10: number | null;
  ndcg_at_10: number | null;
  hit_rate: number | null;
  coverage?: number | null;
  rating_metrics?: {
    rmse: number;
    mae: number;
    baseline_global_mean_rmse: number;
    baseline_global_mean_mae: number;
  };
  weights?: Record<string, number>;
  text_metrics?: {
    accuracy: number;
    macro_f1: number;
    majority_class_accuracy: number;
    majority_class_macro_f1: number;
    auc_positive_vs_rest: number;
    n_test_reviews: number;
  };
}

export interface SparkBenchmark {
  dataset_size: number;
  operation: string;
  pandas_seconds: number;
  spark_seconds: number;
  speedup: number | null;
  winner: string;
}

export interface AnalyticsOverview {
  dataset_summary: Partial<DatasetSummary>;
  top_models: ModelMetrics[];
  spark_benchmarks: SparkBenchmark[];
  model_performance: {
    evaluation_timestamp?: string;
    note?: string;
    leakage_checks?: Record<string, number>;
    tuning?: { hybrid_weights?: Record<string, number> };
  };
}

/** Returns null (and the page shows an explicit error) when the API or its pipeline results are unavailable. */
export async function fetchAnalyticsOverview(): Promise<AnalyticsOverview | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics/overview`, { cache: "no-store" });
    if (!res.ok) return null;
    const raw = (await res.json()).data || {};
    return {
      dataset_summary: raw.dataset_summary || {},
      top_models: raw.top_models || [],
      spark_benchmarks: raw.spark_benchmarks || [],
      model_performance: raw.model_performance || {},
    };
  } catch (e) {
    console.error("fetchAnalyticsOverview error:", e);
    return null;
  }
}
