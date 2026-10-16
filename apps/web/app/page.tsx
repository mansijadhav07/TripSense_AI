"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [destination, setDestination] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = destination.trim() ? `?destination=${encodeURIComponent(destination.trim())}` : "";
    router.push(`/discover${query}`);
  };

  const models = [
    {
      name: "Hybrid Ensemble",
      tag: "⭐ Production Model",
      desc: "Dynamically blends ALS collaborative factors, content cosine matching, and sentiment scores based on user sparsity profile.",
      metric: "NDCG@10: 0.1696",
      color: "from-cyan-500/20 to-blue-500/20 border-cyan-500/40",
    },
    {
      name: "Collaborative Filtering",
      tag: "Matrix Factorization",
      desc: "Apache Spark ALS with 50 latent factors learning subtle interaction patterns from 43,800+ user ratings.",
      metric: "Recall@10: 17.75%",
      color: "from-indigo-500/20 to-purple-500/20 border-indigo-500/30",
    },
    {
      name: "Content-Based Matching",
      tag: "Aspect Vectors",
      desc: "13-dimensional vector space comparing hotel cleanliness, service quality, room comfort, and value for money.",
      metric: "Cosine Sim.",
      color: "from-emerald-500/20 to-teal-500/20 border-emerald-500/30",
    },
    {
      name: "NLP Sentiment Recommender",
      tag: "Aspect Sentiment",
      desc: "Aggregated traveler review sentiment, positive-negative polarities, and textual consistency metrics.",
      metric: "89% Pos. Ratio",
      color: "from-amber-500/20 to-orange-500/20 border-amber-500/30",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-24 border-b border-slate-800/80 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-cyan-500/10 via-transparent to-transparent pointer-events-none"></div>

        <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-6">
            <span>✨ Phase 5 Complete</span>
            <span className="text-slate-500">•</span>
            <span>Serving 50,780 Hotels across 201K+ Reviews</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
            AI-Powered Hotel Intelligence <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              Tailored to Your Stay Style
            </span>
          </h1>

          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Explainable recommendations powered by distributed Apache Spark ML, alternating least squares matrix factorization, and fine-grained aspect sentiment analysis.
          </p>

          {/* Search Box */}
          <form onSubmit={handleSearch} className="max-w-2xl mx-auto flex flex-col sm:flex-row gap-2 bg-slate-900/90 p-2 rounded-2xl border border-slate-800 shadow-2xl shadow-cyan-500/5">
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Where are you traveling? (e.g. Paris, Tokyo, London, Rome)..."
              className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2 text-sm"
            >
              <span>Discover Hotels</span>
              <span>→</span>
            </button>
          </form>

          {/* Quick Stats */}
          <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
              <div className="text-2xl font-bold text-white">50,780</div>
              <div className="text-xs text-slate-400">Indexed Properties</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
              <div className="text-2xl font-bold text-cyan-400">201,382</div>
              <div className="text-xs text-slate-400">Verified Reviews</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
              <div className="text-2xl font-bold text-indigo-400">5</div>
              <div className="text-xs text-slate-400">ML Algorithms</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
              <div className="text-2xl font-bold text-emerald-400">&lt;60ms</div>
              <div className="text-xs text-slate-400">Inference Latency</div>
            </div>
          </div>
        </div>
      </section>

      {/* Model Architecture Section */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white">Multi-Algorithm Recommendation Engine</h2>
          <p className="text-sm text-slate-400 mt-2 max-w-xl mx-auto">
            Each recommendation is computed through specialized models with full explainability of why each property matches your criteria.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {models.map((m) => (
            <div
              key={m.name}
              className={`p-6 rounded-2xl bg-gradient-to-b ${m.color} border backdrop-blur-sm flex flex-col justify-between`}
            >
              <div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800/80 text-cyan-300 border border-slate-700/50">
                  {m.tag}
                </span>
                <h3 className="text-xl font-bold text-white mt-4">{m.name}</h3>
                <p className="text-sm text-slate-300 mt-2 leading-relaxed">{m.desc}</p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-700/40 flex items-center justify-between">
                <span className="text-xs text-slate-400">Benchmark:</span>
                <span className="text-xs font-mono font-semibold text-cyan-400">{m.metric}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link
            href="/discover"
            className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-xl text-sm font-semibold border border-slate-700 transition"
          >
            Launch Interactive Recommendation Studio →
          </Link>
        </div>
      </section>
    </div>
  );
}
