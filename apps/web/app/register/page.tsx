"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password || !confirmPassword) {
      setError("Please fill out all fields.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      // Import the auth API module
      const { signup } = await import("@/lib/auth-api");
      const data = await signup(email, password);

      const token = data.access_token || data.data?.token?.access_token;
      const user = data.user || data.data?.user || { id: "user_new", email };

      if (!token) {
        throw new Error("Missing access token in response.");
      }

      login(token, user);
      setSuccess(true);
      setTimeout(() => {
        router.push("/discover");
      }, 700);
    } catch (err: any) {
      setError(err.message || "Failed to create account. Email may already be in use.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden bg-slate-950">
      {/* 3D Ambient Background Lights */}
      <div className="absolute top-1/3 right-1/4 translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none animate-pulse-glow"></div>
      <div className="absolute bottom-1/3 left-1/4 -translate-x-1/2 translate-y-1/2 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none animate-pulse-glow delay-700"></div>

      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
        
        {/* Left Column: Feature Highlights & Robot Mascot */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center text-center p-6 sm:p-8 rounded-3xl bg-gradient-to-b from-slate-900/60 to-slate-950/80 border border-slate-800/80 backdrop-blur-xl shadow-2xl relative group order-last lg:order-first">
          <div className="relative w-56 h-64 sm:w-64 sm:h-72 flex items-center justify-center animate-float">
            <Image
              src="/tripsense-robot.png"
              alt="TripSense AI Mascot"
              width={260}
              height={300}
              priority
              className="object-contain drop-shadow-[0_15px_30px_rgba(6,182,212,0.3)] transition-transform duration-500 group-hover:scale-105"
            />
          </div>

          <div className="mt-2 text-left space-y-3 w-full">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider text-center">
              What you get with TripSense:
            </h3>
            
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center gap-3">
              <span className="w-7 h-7 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-sm shrink-0">
                ★
              </span>
              <div>
                <span className="font-semibold text-white block">Hyper-Personalized Matching</span>
                <span className="text-slate-400 text-[11px]">Ensemble ML tailored to your unique travel style</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center gap-3">
              <span className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-sm shrink-0">
                ⚡
              </span>
              <div>
                <span className="font-semibold text-white block">Fine-Grained Aspect Tuning</span>
                <span className="text-slate-400 text-[11px]">Prioritize cleanliness, location, or value</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center gap-3">
              <span className="w-7 h-7 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-sm shrink-0">
                🛡️
              </span>
              <div>
                <span className="font-semibold text-white block">Full Explainability</span>
                <span className="text-slate-400 text-[11px]">Know exactly why every hotel is recommended</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Registration Form */}
        <div className="lg:col-span-7 bg-slate-900/80 p-8 sm:p-10 rounded-3xl border border-slate-800/90 shadow-2xl backdrop-blur-2xl relative">
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-3">
              <span>Instant Access • Free Account</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Create your account
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Join thousands of travelers experiencing AI-curated hotel recommendations.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2">
              <span className="font-bold">⚠️</span>
              <div className="flex-1 leading-relaxed">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-6 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
              <span>✓</span>
              <span>Account created successfully! Preparing your studio...</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@domain.com"
                required
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Password <span className="text-slate-500 text-[10px] lowercase">(min 8 characters)</span>
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a strong password"
                required
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-type password"
                required
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading || success}
              className="w-full mt-2 relative group overflow-hidden bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:via-blue-500 hover:to-indigo-500 text-white font-semibold py-3.5 rounded-xl text-sm transition-all shadow-lg shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-cyan-500/40 transform active:scale-[0.99]"
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Creating Your Account...</span>
                  </>
                ) : (
                  <>
                    <span>Create Free Account</span>
                    <span>→</span>
                  </>
                )}
              </span>
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center text-xs text-slate-400">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-cyan-400 hover:text-cyan-300 transition"
            >
              Sign in here →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
