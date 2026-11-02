"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { fetchUserPreferences, updateUserPreferences, TRAVEL_STYLES } from "@/lib/api";

const ASPECTS = ["cleanliness", "location", "rooms", "service", "value"] as const;
type Aspect = (typeof ASPECTS)[number];

interface Preferences {
  destination: string;
  min_rating: number;
  travel_style: string;
  cleanliness_weight: number;
  location_weight: number;
  rooms_weight: number;
  service_weight: number;
  value_weight: number;
  sleep_quality_weight: number;
}

const DEFAULT_PREFERENCES: Preferences = {
  destination: "",
  min_rating: 3,
  travel_style: "leisure",
  cleanliness_weight: 1,
  location_weight: 1,
  rooms_weight: 1,
  service_weight: 1,
  value_weight: 1,
  sleep_quality_weight: 1,
};

const LABELS: Record<Aspect, string> = {
  cleanliness: "Cleanliness",
  location: "Location",
  rooms: "Rooms",
  service: "Service",
  value: "Value",
};

export default function PreferencesPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [preferences, setPreferences] = useState<Preferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!token) return;

    let active = true;
    fetchUserPreferences(token)
      .then((data) => {
        if (!active) return;
        setPreferences({
          ...DEFAULT_PREFERENCES,
          ...data,
          destination: data.destination ?? "",
          min_rating: Number(data.min_rating ?? DEFAULT_PREFERENCES.min_rating),
        });
      })
      .catch((cause: unknown) => {
        console.error("Could not load user preferences:", cause);
        if (active) setError(cause instanceof Error ? cause.message : "Could not load preferences.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  const updateAspect = (aspect: Aspect, value: number) => {
    setPreferences((current) => ({ ...current, [`${aspect}_weight`]: value }));
  };

  const savePreferences = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      router.push("/login");
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const data = await updateUserPreferences(token, {
        ...preferences,
        destination: preferences.destination.trim() || null,
      });
      setPreferences((current) => ({
        ...current,
        ...data,
        destination: data.destination ?? "",
      }));
      setSaved(true);
    } catch (cause) {
      console.error("Could not save user preferences:", cause);
      setError(cause instanceof Error ? cause.message : "Could not save preferences.");
    } finally {
      setSaving(false);
    }
  };

  if (!token) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <h1 className="text-2xl font-bold text-white">Sign in to edit preferences</h1>
        <p className="mt-2 text-sm text-slate-400">Your recommendation preferences are saved to your account.</p>
        <Link href="/login" className="mt-6 inline-block rounded-xl bg-cyan-600 px-5 py-3 text-sm font-semibold text-white">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link href="/profile" className="text-sm text-cyan-400 hover:text-cyan-300">← Back to profile</Link>
      <div className="mb-8 mt-5">
        <h1 className="text-3xl font-extrabold text-white">Edit Preferences</h1>
        <p className="mt-2 text-sm text-slate-400">Tune your recommendations. These settings are saved to your account and used by the discovery studio.</p>
      </div>

      {loading ? (
        <p className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-400">Loading your preferences…</p>
      ) : (
        <form onSubmit={savePreferences} className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8">
          <div>
            <label htmlFor="destination" className="mb-2 block text-sm font-medium text-slate-200">Preferred destination</label>
            <input
              id="destination"
              value={preferences.destination}
              onChange={(event) => setPreferences((current) => ({ ...current, destination: event.target.value }))}
              maxLength={200}
              placeholder="Any destination"
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="min-rating" className="mb-2 flex justify-between text-sm font-medium text-slate-200">
              <span>Minimum hotel rating</span><span className="text-cyan-400">{preferences.min_rating.toFixed(1)} ★</span>
            </label>
            <input
              id="min-rating"
              type="range"
              min="1"
              max="5"
              step="0.1"
              value={preferences.min_rating}
              onChange={(event) => setPreferences((current) => ({ ...current, min_rating: Number(event.target.value) }))}
              className="w-full accent-cyan-500"
            />
          </div>

          <div>
            <label htmlFor="travel-style" className="mb-2 block text-sm font-medium text-slate-200">Travel style</label>
            <select
              id="travel-style"
              value={preferences.travel_style}
              onChange={(event) => setPreferences((current) => ({ ...current, travel_style: event.target.value }))}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm capitalize text-white focus:border-cyan-500 focus:outline-none"
            >
              <option value="leisure">Leisure</option>
              {TRAVEL_STYLES.map((style) => <option key={style} value={style}>{style}</option>)}
            </select>
          </div>

          <fieldset>
            <legend className="mb-3 text-sm font-medium text-slate-200">Recommendation aspect weights</legend>
            <div className="space-y-4">
              {ASPECTS.map((aspect) => {
                const key = `${aspect}_weight` as const;
                return (
                  <label key={aspect} className="block">
                    <span className="mb-1 flex justify-between text-xs text-slate-400">
                      <span>{LABELS[aspect]}</span><span>{preferences[key].toFixed(1)}×</span>
                    </span>
                    <input
                      type="range"
                      min="0"
                      max="3"
                      step="0.1"
                      value={preferences[key]}
                      onChange={(event) => updateAspect(aspect, Number(event.target.value))}
                      className="w-full accent-cyan-500"
                    />
                  </label>
                );
              })}
            </div>
          </fieldset>

          {error && <p role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">{error}</p>}
          {saved && <p role="status" className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-300">Preferences saved successfully.</p>}

          <div className="flex flex-col-reverse gap-3 border-t border-slate-800 pt-5 sm:flex-row sm:justify-end">
            <Link href="/profile" className="rounded-xl border border-slate-700 px-5 py-3 text-center text-sm font-medium text-slate-300 hover:bg-slate-800">Cancel</Link>
            <button type="submit" disabled={saving} className="rounded-xl bg-cyan-600 px-5 py-3 text-sm font-semibold text-white hover:bg-cyan-500 disabled:opacity-50">
              {saving ? "Saving…" : "Save Preferences"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
