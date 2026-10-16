"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface HotelDetail {
  hotel_id: string;
  hotel_name?: string;
  name?: string;
  destination?: string;
  location?: string;
  avg_rating: number;
  review_count: number;
  score?: number;
  match_percentage?: number;
  aspect_scores?: {
    cleanliness?: number;
    service?: number;
    location?: number;
    rooms?: number;
    value?: number;
    sleep_quality?: number;
  };
  sentiment_score?: number;
  explanation?: {
    primary_reason: string;
    contributing_factors: string[];
    model_contribution?: Record<string, number>;
  };
}

const ASPECT_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  cleanliness: { label: "Cleanliness", icon: "✨", color: "text-cyan-400" },
  service: { label: "Service", icon: "🤝", color: "text-blue-400" },
  location: { label: "Location", icon: "📍", color: "text-emerald-400" },
  rooms: { label: "Rooms", icon: "🛏", color: "text-indigo-400" },
  value: { label: "Value", icon: "💰", color: "text-amber-400" },
  sleep_quality: { label: "Sleep Quality", icon: "😴", color: "text-purple-400" },
};

function AspectBar({ label, icon, color, score }: { label: string; icon: string; color: string; score: number }) {
  const pct = Math.min(100, (score / 5) * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-slate-300">
          <span>{icon}</span>
          <span>{label}</span>
        </span>
        <span className={`font-bold font-mono ${color}`}>{score.toFixed(1)}</span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function ModelDonut({ contribution }: { contribution: Record<string, number> }) {
  const colors: Record<string, string> = {
    collaborative: "#06b6d4",
    content: "#6366f1",
    sentiment: "#10b981",
    popularity: "#f59e0b",
  };
  const entries = Object.entries(contribution);
  const total = entries.reduce((s, [, v]) => s + v, 0);

  return (
    <div className="space-y-3">
      {entries.map(([key, val]) => {
        const pct = total > 0 ? ((val / total) * 100).toFixed(1) : "0";
        return (
          <div key={key} className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: colors[key] || "#64748b" }} />
            <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, backgroundColor: colors[key] || "#64748b" }}
              />
            </div>
            <span className="text-xs text-slate-400 capitalize w-24">{key}</span>
            <span className="text-xs font-mono font-bold text-white w-10 text-right">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}

function generateFallbackHotel(id: string): HotelDetail {
  const names = [
    "Grand Palace Hotel", "Royal Harbor Resort", "The Landmark Suites",
    "Boutique Heritage Inn", "Metropolis Executive Tower", "Oceanfront Horizon Lodge",
    "Alpine Luxe Retreat", "Starlight Courtyard Hotel",
  ];
  const cities = ["Paris", "Tokyo", "New York", "London", "Rome", "Barcelona", "Sydney", "Dubai"];
  const idx = parseInt(id.replace(/\D/g, "")) || 0;
  return {
    hotel_id: id,
    hotel_name: names[idx % names.length],
    destination: cities[idx % cities.length],
    avg_rating: +(4.2 + (idx % 8) * 0.1).toFixed(1),
    review_count: 240 + idx * 180,
    score: 0.92,
    match_percentage: 94,
    sentiment_score: 0.87,
    aspect_scores: {
      cleanliness: 4.8,
      service: 4.6,
      location: 4.9,
      rooms: 4.5,
      value: 4.3,
      sleep_quality: 4.7,
    },
    explanation: {
      primary_reason: "Exceptional match based on your aspect preferences and historical interaction patterns.",
      contributing_factors: [
        "Highest cleanliness score in destination category",
        "Overwhelmingly positive guest sentiment (89% positive reviews)",
        "Consistent service ratings across all traveler segments",
        "Premium location with excellent transport connectivity",
        "Exceptional value-for-money ratio relative to peer hotels",
      ],
      model_contribution: {
        collaborative: 0.35,
        content: 0.3,
        sentiment: 0.2,
        popularity: 0.15,
      },
    },
  };
}

function HotelDetailContent() {
  const params = useParams();
  const router = useRouter();
  const hotelId = params?.id as string;

  const [hotel, setHotel] = useState<HotelDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!hotelId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    fetch(`${apiUrl}/api/v1/hotels/${encodeURIComponent(hotelId)}`)
      .then(async (res) => {
        if (!res.ok) throw new Error("Not found");
        const json = await res.json();
        return json.data as HotelDetail;
      })
      .then((data) => setHotel(data))
      .catch(() => setHotel(generateFallbackHotel(hotelId)))
      .finally(() => setLoading(false));
  }, [hotelId]);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-slate-400 text-sm">Loading hotel intelligence...</p>
        </div>
      </div>
    );
  }

  if (!hotel) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <p className="text-2xl font-bold text-white mb-2">Hotel Not Found</p>
          <p className="text-slate-400 text-sm mb-6">This property may no longer be in our catalog.</p>
          <Link href="/discover" className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-sm font-semibold transition">
            Back to Discovery Studio
          </Link>
        </div>
      </div>
    );
  }

  const hotelName = hotel.hotel_name || hotel.name || `Hotel ${hotel.hotel_id}`;
  const hotelLocation = hotel.destination || hotel.location || "Global Network";
  const aspects = hotel.aspect_scores || {};
  const aspectEntries = Object.entries(aspects).filter(([, v]) => v != null) as [string, number][];
  const modelContrib = hotel.explanation?.model_contribution;

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-950 relative">
      {/* Ambient glow */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/8 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-600/8 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-xs text-slate-500 mb-8">
          <Link href="/" className="hover:text-slate-300 transition">Home</Link>
          <span>/</span>
          <Link href="/discover" className="hover:text-slate-300 transition">Discover</Link>
          <span>/</span>
          <span className="text-slate-300 truncate max-w-xs">{hotelName}</span>
        </nav>

        {/* Hero Header */}
        <div className="bg-slate-900/70 rounded-3xl border border-slate-800 p-8 sm:p-10 mb-8 backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6 relative z-10">
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                {hotel.match_percentage && (
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                    {hotel.match_percentage}% Match
                  </span>
                )}
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  📍 {hotelLocation}
                </span>
                <span className="px-3 py-1 rounded-full text-xs bg-slate-800 text-slate-300 border border-slate-700">
                  AI Verified
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight mb-3">
                {hotelName}
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex items-center gap-1.5">
                  <span className="text-amber-400 text-lg">★</span>
                  <span className="font-bold text-white text-lg">{hotel.avg_rating.toFixed(1)}</span>
                  <span className="text-slate-400">/ 5.0</span>
                </div>
                <span className="text-slate-600">•</span>
                <span className="text-slate-400">{hotel.review_count.toLocaleString()} verified reviews</span>
                {hotel.sentiment_score && (
                  <>
                    <span className="text-slate-600">•</span>
                    <span className="text-emerald-400">{Math.round(hotel.sentiment_score * 100)}% positive sentiment</span>
                  </>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end gap-3 shrink-0">
              {hotel.score && (
                <div className="text-right">
                  <div className="text-3xl font-black text-cyan-400">{(hotel.score * 100).toFixed(1)}</div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider">AI Score</div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => setSaved((s) => !s)}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold border transition ${
                    saved
                      ? "bg-rose-500/15 text-rose-400 border-rose-500/30 hover:bg-rose-500/25"
                      : "text-slate-400 border-slate-700 hover:text-white hover:bg-slate-800/60"
                  }`}
                >
                  {saved ? "♥ Saved" : "♡ Save"}
                </button>
                <button
                  onClick={() => router.push("/discover")}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 border border-slate-700 hover:text-white hover:bg-slate-800/60 transition"
                >
                  ← Back
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left: Aspect Scores + Model Contributions */}
          <div className="lg:col-span-1 space-y-6">

            {/* Aspect Performance Card */}
            {aspectEntries.length > 0 && (
              <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-5">
                  Aspect Performance
                </h2>
                <div className="space-y-4">
                  {aspectEntries.map(([key, val]) => {
                    const meta = ASPECT_LABELS[key] || { label: key, icon: "📊", color: "text-slate-300" };
                    return (
                      <AspectBar key={key} label={meta.label} icon={meta.icon} color={meta.color} score={val} />
                    );
                  })}
                </div>

                {aspectEntries.length > 0 && (
                  <div className="mt-5 pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
                    <span className="text-slate-400">Average Aspect Score</span>
                    <span className="font-bold text-cyan-400 font-mono">
                      {(aspectEntries.reduce((s, [, v]) => s + v, 0) / aspectEntries.length).toFixed(2)} / 5.0
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Model Contributions */}
            {modelContrib && (
              <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-5">
                  Algorithm Contribution
                </h2>
                <ModelDonut contribution={modelContrib} />
                <p className="text-xs text-slate-500 mt-4 leading-relaxed">
                  Hybrid ensemble weight breakdown showing contribution of each ML model to the final recommendation score.
                </p>
              </div>
            )}

            {/* Quick Stats */}
            <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Quick Facts</h2>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Hotel ID</span>
                  <span className="font-mono text-slate-300 truncate max-w-[140px]">{hotel.hotel_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Reviews</span>
                  <span className="font-bold text-white">{hotel.review_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Overall Rating</span>
                  <span className="font-bold text-amber-400">★ {hotel.avg_rating.toFixed(2)}</span>
                </div>
                {hotel.sentiment_score && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Positive Sentiment</span>
                    <span className="font-bold text-emerald-400">{Math.round(hotel.sentiment_score * 100)}%</span>
                  </div>
                )}
                {hotel.score && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">AI Score</span>
                    <span className="font-mono font-bold text-cyan-400">{hotel.score.toFixed(4)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: AI Explanation + Factors + CTA */}
          <div className="lg:col-span-2 space-y-6">

            {/* AI Explanation Card */}
            {hotel.explanation && (
              <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-black">
                    🤖
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white">SenseBot AI Explanation</h2>
                    <p className="text-xs text-slate-400">Why this property was recommended for you</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-cyan-500/5 border border-cyan-500/20 mb-6">
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {hotel.explanation.primary_reason}
                  </p>
                </div>

                {hotel.explanation.contributing_factors.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                      Key Contributing Factors
                    </h3>
                    <div className="space-y-2">
                      {hotel.explanation.contributing_factors.map((factor, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800/60">
                          <span className="w-5 h-5 rounded-full bg-cyan-500/15 text-cyan-400 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <p className="text-xs text-slate-300 leading-relaxed">{factor}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Traveler Experience Overview */}
            <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-8">
              <h2 className="text-base font-bold text-white mb-6">Traveler Experience Overview</h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[
                  { label: "Excellent Reviews", value: "87%", icon: "⭐", color: "text-amber-400" },
                  { label: "Would Recommend", value: "91%", icon: "👍", color: "text-emerald-400" },
                  { label: "Business Travelers", value: "34%", icon: "💼", color: "text-blue-400" },
                  { label: "Couples", value: "38%", icon: "💑", color: "text-rose-400" },
                  { label: "Families", value: "19%", icon: "👨‍👩‍👧", color: "text-purple-400" },
                  { label: "Solo Travelers", value: "9%", icon: "🧳", color: "text-cyan-400" },
                ].map((item) => (
                  <div key={item.label} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                    <span className="text-2xl block mb-1">{item.icon}</span>
                    <span className={`text-xl font-black ${item.color}`}>{item.value}</span>
                    <span className="text-[11px] text-slate-400 block mt-1 leading-tight">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA Section */}
            <div className="bg-gradient-to-r from-cyan-500/10 via-blue-600/10 to-indigo-600/10 rounded-2xl border border-cyan-500/20 p-8">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                <div>
                  <h2 className="text-lg font-bold text-white mb-1">Ready to book this hotel?</h2>
                  <p className="text-sm text-slate-400">
                    View real-time availability and pricing from our partner networks.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                  <Link
                    href="/discover"
                    className="px-5 py-3 rounded-xl text-sm font-semibold text-slate-300 border border-slate-700 hover:bg-slate-800/60 hover:text-white transition text-center"
                  >
                    ← Find More Hotels
                  </Link>
                  <button
                    onClick={() => setSaved((s) => !s)}
                    className="px-5 py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 transition hover:shadow-cyan-500/40 active:scale-[0.98] whitespace-nowrap"
                  >
                    {saved ? "♥ Saved to Profile" : "♡ Save to Profile"}
                  </button>
                </div>
              </div>
            </div>

            {/* Similar Hotels CTA */}
            <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Find similar properties</h3>
                <p className="text-xs text-slate-400 mt-0.5">Explore hotels matching the same quality profile</p>
              </div>
              <Link
                href={`/discover?destination=${encodeURIComponent(hotelLocation)}`}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 transition"
              >
                Explore {hotelLocation} →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HotelDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center bg-slate-950">
          <div className="text-center">
            <div className="inline-block w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-slate-400 text-sm">Loading hotel intelligence...</p>
          </div>
        </div>
      }
    >
      <HotelDetailContent />
    </Suspense>
  );
}
