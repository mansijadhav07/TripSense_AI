"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchHotelReviews, HotelReview } from "@/lib/api";

interface HotelReviewsProps {
  hotelId: string;
  refreshKey: number;
}

type ReviewLimit = 5 | 10 | 20 | "all";

const reviewLimitOptions: ReviewLimit[] = [5, 10, 20, "all"];

const sentimentStyles = {
  positive: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  neutral: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  negative: "border-rose-500/30 bg-rose-500/10 text-rose-300",
};

function formatReviewDate(value: string | null): string {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date unavailable"
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

export default function HotelReviews({ hotelId, refreshKey }: HotelReviewsProps) {
  const [reviews, setReviews] = useState<HotelReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewLimit, setReviewLimit] = useState<ReviewLimit>(5);

  const loadReviews = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setReviews(await fetchHotelReviews(hotelId));
    } catch (cause) {
      console.error("Could not load hotel reviews:", cause);
      setError(cause instanceof Error ? cause.message : "Could not load reviews.");
    } finally {
      setLoading(false);
    }
  }, [hotelId]);

  const visibleReviews = reviewLimit === "all" ? reviews : reviews.slice(0, reviewLimit);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadReviews(), 0);
    return () => window.clearTimeout(timer);
  }, [loadReviews, refreshKey]);

  return (
    <section aria-labelledby="submitted-reviews-heading" className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 id="submitted-reviews-heading" className="text-base font-bold text-white">Traveler Reviews</h2>
          <p className="mt-1 text-xs text-slate-400">Catalog sample reviews and reviews submitted through TripSense</p>
        </div>
        {!loading && !error && (
          <span className="text-xs text-slate-500">{reviews.length} {reviews.length === 1 ? "review" : "reviews"}</span>
        )}
      </div>

      {loading ? (
        <p role="status" className="text-sm text-slate-400">Loading reviews…</p>
      ) : error ? (
        <div>
          <p role="alert" className="text-sm text-rose-300">{error}</p>
          <button type="button" onClick={() => void loadReviews()} className="mt-3 text-sm font-medium text-cyan-400 hover:text-cyan-300">
            Try again
          </button>
        </div>
      ) : reviews.length === 0 ? (
        <p className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">
          No catalog or TripSense reviews are available for this hotel yet.
        </p>
      ) : (
        <div>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p aria-live="polite" className="text-xs text-slate-400">
              Showing {visibleReviews.length} of {reviews.length} reviews
            </p>
            {reviews.length > 5 && (
              <div role="group" aria-label="Number of reviews to show" className="flex flex-wrap items-center gap-1.5">
                {reviewLimitOptions.map((limit) => {
                  const label = limit === "all" ? "All" : String(limit);
                  return (
                    <button
                      key={label}
                      type="button"
                      aria-pressed={reviewLimit === limit}
                      onClick={() => setReviewLimit(limit)}
                      className={`rounded-lg border px-2.5 py-1.5 text-xs font-medium transition ${
                        reviewLimit === limit
                          ? "border-cyan-500/50 bg-cyan-500/15 text-cyan-300"
                          : "border-slate-700 text-slate-400 hover:border-slate-600 hover:text-white"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          <div className="space-y-3">
            {visibleReviews.map((review) => (
              <article key={review.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    {review.rating === null ? (
                      <span className="text-xs text-slate-500">No star rating</span>
                    ) : (
                      <span aria-label={`${review.rating} out of 5 stars`} className="text-sm font-bold text-amber-400">
                        {"★".repeat(review.rating)}{"☆".repeat(5 - review.rating)}
                        <span className="ml-1 text-xs text-slate-400">{review.rating}/5</span>
                      </span>
                    )}
                    <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize ${sentimentStyles[review.sentiment_label]}`}>
                      {review.sentiment_label} sentiment
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-500">
                      {review.source === "user" ? "TripSense review" : review.is_synthetic ? "Sample data" : "Catalog review"}
                    </span>
                    <time dateTime={review.created_at ?? undefined} className="text-xs text-slate-500">
                      {formatReviewDate(review.created_at)}
                    </time>
                  </div>
                </div>
                <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-200">{review.text}</p>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
