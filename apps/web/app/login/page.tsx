"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Quick fill demo credentials
  const fillDemo = () => {
    setEmail("traveler@tripsense.ai");
    setPassword("DemoPass123!");
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Please provide both email and password.");
      return;
    }

    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        // If user not registered yet in DB, offer intuitive feedback
        throw new Error(data.detail || data.message || "Invalid email or password");
      }

      const token = data.access_token || data.data?.token?.access_token;
      const user = data.user || data.data?.user || { id: "user_demo", email };

      if (!token) {
        throw new Error("Missing authentication token in response.");
      }

      login(token, user);
      setSuccess(true);
      setTimeout(() => {
        router.push("/discover");
      }, 700);
    } catch (err: unknown) {
      setError((err instanceof Error && err.message) || "Login failed. Please check credentials or register.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden bg-slate-950">
      {/* 3D Dynamic Ambient Glows */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none animate-pulse-glow"></div>
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[28rem] h-[28rem] bg-indigo-600/15 rounded-full blur-3xl pointer-events-none animate-pulse-glow delay-1000"></div>

      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
        
        {/* Left Column: 3D Robot Mascot Showcase */}
        <div className="lg:col-span-6 flex flex-col items-center justify-center text-center p-6 sm:p-8 rounded-3xl bg-gradient-to-b from-slate-900/60 to-slate-950/80 border border-slate-800/80 backdrop-blur-xl shadow-2xl relative group">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3.5 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-500/30">
            🤖 Meet SenseBot • AI Travel Companion
          </div>

          {/* Interactive Floating 3D Robot Card */}
          <div className="relative mt-4 w-72 h-80 sm:w-80 sm:h-96 flex items-center justify-center animate-float">
            <div className="absolute inset-0 bg-gradient-to-t from-cyan-500/20 via-transparent to-transparent rounded-full blur-2xl group-hover:from-cyan-400/30 transition-all duration-700"></div>
            
            <Image
              src="/tripsense-robot.png"
              alt="TripSense AI Intelligent Robot Concierge"
              width={380}
              height={420}
              priority
              className="object-contain drop-shadow-[0_20px_35px_rgba(6,182,212,0.35)] transition-transform duration-500 group-hover:scale-105"
            />
          </div>

          <div className="mt-4 max-w-sm">
            <h2 className="text-xl font-extrabold text-white">
              AI Concierge Ready to Assist
            </h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Personalized stay matches powered by distributed Spark ML with 50 latent factors & NLP sentiment synthesis.
            </p>

            <div className="mt-4 flex items-center justify-center gap-3 text-[11px] text-slate-300">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Real-time Inference
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60">
                50,780 Hotels Indexed
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Glassmorphic Login Form */}
        <div className="lg:col-span-6 bg-slate-900/80 p-8 sm:p-10 rounded-3xl border border-slate-800/90 shadow-2xl backdrop-blur-2xl relative">
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 mb-3">
              <span>Secure Authentication</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Welcome back
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Sign in to unlock personalized hotel scores and custom aspect rankings.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2 animate-shake">
              <span className="font-bold">⚠️</span>
              <div className="flex-1 leading-relaxed">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-6 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
              <span>✓</span>
              <span>Authentication successful! Redirecting to Discovery Studio...</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <button
                  type="button"
                  onClick={fillDemo}
                  className="text-xs text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
                >
                  Quick Demo Account
                </button>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading || success}
              className="w-full relative group overflow-hidden bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:via-blue-500 hover:to-indigo-500 text-white font-semibold py-3.5 rounded-xl text-sm transition-all shadow-lg shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-cyan-500/40 transform active:scale-[0.99]"
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Validating Credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to TripSense</span>
                    <span>→</span>
                  </>
                )}
              </span>
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center text-xs text-slate-400">
            Don&apos;t have an account yet?{" "}
            <Link
              href="/register"
              className="font-semibold text-cyan-400 hover:text-cyan-300 transition"
            >
              Create free account →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
