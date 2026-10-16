"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

interface SavedHotel {
  hotel_id: string;
  hotel_name: string;
  destination: string;
  avg_rating: number;
  review_count: number;
  match_percentage: number;
  saved_at: string;
}

const DEMO_SAVED: SavedHotel[] = [
  {
    hotel_id: "hotel_1",
    hotel_name: "Grand Palace Hotel Paris",
    destination: "Paris",
    avg_rating: 4.8,
    review_count: 1820,
    match_percentage: 95,
    saved_at: "2026-10-14",
  },
  {
    hotel_id: "hotel_3",
    hotel_name: "The Landmark Suites New York",
    destination: "New York",
    avg_rating: 4.6,
    review_count: 4102,
    match_percentage: 91,
    saved_at: "2026-10-13",
  },
  {
    hotel_id: "hotel_5",
    hotel_name: "Metropolis Executive Tower Tokyo",
    destination: "Tokyo",
    avg_rating: 4.4,
    review_count: 738,
    match_percentage: 87,
    saved_at: "2026-10-12",
  },
];

const STAT_CARDS = [
  { label: "Hotels Saved", icon: "♥", colorClass: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20", key: "saved" },
  { label: "Avg Rating Saved", icon: "★", colorClass: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", key: "avgRating" },
  { label: "Destinations", icon: "📍", colorClass: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20", key: "destinations" },
  { label: "AI Sessions", icon: "🤖", colorClass: "text-indigo-400", bg: "bg-indigo-500/10 border-indigo-500/20", key: "sessions" },
];

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const [saved, setSaved] = useState<SavedHotel[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading saved hotels
    const timer = setTimeout(() => {
      setSaved(DEMO_SAVED);
      setLoading(false);
    }, 700);
    return () => clearTimeout(timer);
  }, []);

  const handleRemove = (hotelId: string) => {
    setRemoving(hotelId);
    setTimeout(() => {
      setSaved((prev) => prev.filter((h) => h.hotel_id !== hotelId));
      setRemoving(null);
    }, 400);
  };

  const handleSignOut = () => {
    logout();
    router.push("/");
  };

  const avgRating =
    saved.length > 0
      ? (saved.reduce((s, h) => s + h.avg_rating, 0) / saved.length).toFixed(1)
      : "–";

  const uniqueDestinations = new Set(saved.map((h) => h.destination)).size;

  const statValues: Record<string, string> = {
    saved: String(saved.length),
    avgRating: `${avgRating} ★`,
    destinations: String(uniqueDestinations),
    sessions: "12",
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-950 relative overflow-hidden">
      {/* Ambient glows */}
      <div className="absolute top-0 right-1/4 w-[32rem] h-[32rem] bg-indigo-600/8 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-80 h-80 bg-cyan-500/8 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10">

        {/* Page Header */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Authenticated Session
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Your Travel Profile
          </h1>
          <p className="text-slate-400 mt-2 text-sm">
            Manage your saved hotels, preferences, and AI recommendation history.
          </p>
        </div>

        {/* Profile Hero Card */}
        <div className="bg-slate-900/70 rounded-3xl border border-slate-800 p-8 mb-8 backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-cyan-500/5 to-transparent rounded-full blur-2xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row sm:items-center gap-6 relative z-10">
            {/* Avatar */}
            <div className="relative shrink-0">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center text-3xl font-black text-white shadow-xl shadow-cyan-500/20">
                {(user?.email?.[0] || "T").toUpperCase()}
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-2 border-slate-900 flex items-center justify-center">
                <span className="w-2 h-2 rounded-full bg-white" />
              </div>
            </div>

            {/* User info */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h2 className="text-xl font-bold text-white">
                  {user?.email ? user.email.split("@")[0] : "Traveler"}
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  ✓ Verified
                </span>
              </div>
              <p className="text-sm text-slate-400 truncate">{user?.email || "traveler@tripsense.ai"}</p>
              <p className="text-xs text-slate-500 mt-1">Member since October 2026 · TripSense AI Early Access</p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 shrink-0">
              <Link
                href="/discover"
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 transition"
              >
                + Discover Hotels
              </Link>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 border border-slate-700 hover:border-rose-500/40 hover:text-rose-400 hover:bg-rose-500/10 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {STAT_CARDS.map((stat) => (
            <div
              key={stat.key}
              className={`p-5 rounded-2xl border backdrop-blur-sm ${stat.bg} relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300`}
            >
              <div className="absolute -top-4 -right-4 text-5xl opacity-10 group-hover:opacity-20 transition-opacity duration-300">
                {stat.icon}
              </div>
              <div className={`text-2xl font-black ${stat.colorClass} mb-1`}>
                {statValues[stat.key]}
              </div>
              <div className="text-xs text-slate-400">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Preferences Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
          <div className="lg:col-span-1">
            <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6 h-full">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-5">
                AI Preferences
              </h2>
              <div className="space-y-4">
                {[
                  { label: "Preferred Model", value: "Hybrid Ensemble", icon: "🤖" },
                  { label: "Top Aspect", value: "Cleanliness", icon: "✨" },
                  { label: "Min Rating", value: "4.0 ★", icon: "⭐" },
                  { label: "Preferred Style", value: "Business / Luxury", icon: "💼" },
                  { label: "Budget Range", value: "Mid-High", icon: "💰" },
                ].map((pref) => (
                  <div key={pref.label} className="flex items-center justify-between py-2 border-b border-slate-800/60 last:border-0">
                    <span className="flex items-center gap-2 text-xs text-slate-400">
                      <span>{pref.icon}</span>
                      <span>{pref.label}</span>
                    </span>
                    <span className="text-xs font-semibold text-white">{pref.value}</span>
                  </div>
                ))}
              </div>
              <button className="mt-5 w-full py-2.5 rounded-xl text-xs font-semibold text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/10 transition">
                Edit Preferences →
              </button>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6 h-full">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-5">
                Recent AI Activity
              </h2>
              <div className="space-y-3">
                {[
                  { action: "Hybrid Ensemble run", detail: "Paris · 12 recommendations generated", time: "2h ago", icon: "🤖", color: "text-cyan-400" },
                  { action: "Hotel viewed", detail: "Grand Palace Hotel Paris · Detail page", time: "2h ago", icon: "👁", color: "text-blue-400" },
                  { action: "Hotel saved", detail: "The Landmark Suites New York", time: "Yesterday", icon: "♥", color: "text-rose-400" },
                  { action: "Content-Based run", detail: "Tokyo · 8 recommendations generated", time: "2 days ago", icon: "📊", color: "text-indigo-400" },
                  { action: "Account created", detail: "Joined TripSense AI Early Access", time: "Oct 14, 2026", icon: "✓", color: "text-emerald-400" },
                ].map((activity, i) => (
                  <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-slate-950/40 border border-slate-800/50 hover:border-slate-700/60 transition">
                    <div className={`w-8 h-8 rounded-lg bg-slate-800/80 flex items-center justify-center text-sm shrink-0 ${activity.color}`}>
                      {activity.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-semibold text-white block">{activity.action}</span>
                      <span className="text-[11px] text-slate-400 truncate block">{activity.detail}</span>
                    </div>
                    <span className="text-[11px] text-slate-500 shrink-0">{activity.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Saved Hotels Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white">Saved Hotels</h2>
              <p className="text-sm text-slate-400 mt-0.5">
                {saved.length} {saved.length === 1 ? "property" : "properties"} in your collection
              </p>
            </div>
            <Link
              href="/discover"
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-md shadow-cyan-500/20 transition"
            >
              + Add More
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-52 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse" />
              ))}
            </div>
          ) : saved.length === 0 ? (
            <div className="text-center py-20 bg-slate-900/30 rounded-2xl border border-slate-800 border-dashed">
              <div className="text-4xl mb-4">♡</div>
              <p className="text-lg font-semibold text-white mb-2">No saved hotels yet</p>
              <p className="text-sm text-slate-400 mb-6">
                Browse the discovery studio and save hotels you love.
              </p>
              <Link
                href="/discover"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm transition shadow-lg shadow-cyan-600/20"
              >
                Discover Hotels →
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {saved.map((hotel) => (
                <div
                  key={hotel.hotel_id}
                  className={`bg-slate-900/70 rounded-2xl border border-slate-800 p-6 flex flex-col justify-between hover:border-cyan-500/30 transition-all duration-300 ${
                    removing === hotel.hotel_id ? "opacity-40 scale-95" : "opacity-100 scale-100"
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {hotel.match_percentage}% Match
                      </span>
                      <span className="text-xs text-slate-500">{hotel.saved_at}</span>
                    </div>

                    <h3 className="text-base font-bold text-white leading-snug mb-1 line-clamp-2">
                      {hotel.hotel_name}
                    </h3>
                    <p className="text-xs text-slate-400 flex items-center gap-1.5 mb-3">
                      <span>📍</span>
                      <span>{hotel.destination}</span>
                    </p>

                    <div className="flex items-center gap-3 text-xs text-slate-300">
                      <span className="text-amber-400 font-bold">★ {hotel.avg_rating.toFixed(1)}</span>
                      <span className="text-slate-500">•</span>
                      <span>{hotel.review_count.toLocaleString()} reviews</span>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-800/60 flex items-center gap-2">
                    <Link
                      href={`/hotels/${hotel.hotel_id}`}
                      className="flex-1 py-2 rounded-xl text-xs font-semibold text-center bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 transition"
                    >
                      View Details
                    </Link>
                    <button
                      onClick={() => handleRemove(hotel.hotel_id)}
                      className="px-3 py-2 rounded-xl text-xs text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 border border-slate-700 hover:border-rose-500/30 transition"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bottom CTA */}
        {!isAuthenticated && (
          <div className="mt-12 text-center p-8 bg-gradient-to-r from-cyan-500/10 to-indigo-600/10 rounded-2xl border border-cyan-500/20">
            <h3 className="text-xl font-bold text-white mb-2">Sign in to access your profile</h3>
            <p className="text-slate-400 text-sm mb-6">Create a free account to save hotels and personalize your AI recommendations.</p>
            <div className="flex justify-center gap-3">
              <Link href="/login" className="px-6 py-3 rounded-xl text-sm font-semibold text-slate-300 border border-slate-700 hover:bg-slate-800 transition">
                Sign In
              </Link>
              <Link href="/register" className="px-6 py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 transition">
                Create Account →
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
