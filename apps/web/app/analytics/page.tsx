import { Suspense } from "react";
import { fetchAnalyticsOverview } from "@/lib/api";

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 py-20 text-slate-400">Loading analytics…</div>}>
      <AnalyticsContent />
    </Suspense>
  );
}

async function AnalyticsContent() {
  const data = await fetchAnalyticsOverview();

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center" role="alert">
        <h1 className="text-2xl font-bold text-white">Analytics unavailable</h1>
        <p className="text-sm text-slate-400 mt-2">
          The API could not provide pipeline results. Run{" "}
          <code className="text-cyan-400">python ml/scripts/generate_synthetic_dataset.py && python ml/scripts/train_and_evaluate.py</code> and make sure the API is running.
        </p>
      </div>
    );
  }

  const ds = data.dataset_summary;
  const models = data.top_models;
  const benchmarks = data.spark_benchmarks;
  const fmt = (v: number | null | undefined, d = 4) => (v === null || v === undefined ? "n/a" : v.toFixed(d));
  const num = (v: number | undefined) => (v === undefined ? "—" : v.toLocaleString());

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      <div>
        <h1 className="text-3xl font-extrabold text-white">System Analytics & ML Evaluation</h1>
        <p className="text-sm text-slate-400 mt-1">
          Statistics and leakage-free evaluation results written by the ML pipeline
        </p>
      </div>

      {/* Dataset Overview Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block">Total Reviews</span>
          <span className="text-2xl font-black text-white mt-1 block">
            {num(ds.total_reviews)}
          </span>
          <span className="text-[11px] text-emerald-400">Synthetic dataset (seed 42)</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block">Total Hotels</span>
          <span className="text-2xl font-black text-cyan-400 mt-1 block">
            {num(ds.total_hotels)}
          </span>
          <span className="text-[11px] text-slate-500">Distinct hotel_id values</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block">Unique Users</span>
          <span className="text-2xl font-black text-indigo-400 mt-1 block">
            {num(ds.total_users)}
          </span>
          <span className="text-[11px] text-slate-500">Global Reviewers</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block">Avg Rating</span>
          <span className="text-2xl font-black text-amber-400 mt-1 block">
            {fmt(ds.avg_rating, 2)} ★
          </span>
          <span className="text-[11px] text-slate-500">Std: ±{fmt(ds.rating_std, 2)}</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block">Matrix Sparsity</span>
          <span className="text-2xl font-black text-rose-400 mt-1 block">
            {ds.sparsity_percent ?? "—"}%
          </span>
          <span className="text-[11px] text-rose-400/80">User × hotel matrix</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block">Temporal Range</span>
          <span className="text-sm font-bold text-slate-200 mt-2 block">
            {ds.date_range ? `${ds.date_range.start} – ${ds.date_range.end}` : "—"}
          </span>
          <span className="text-[11px] text-slate-500">Review post dates</span>
        </div>
      </div>

      {ds.data_warning && (
        <div role="alert" className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
          <strong>Data limitation:</strong> {ds.data_warning}
        </div>
      )}

      {/* Model Performance Comparison Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Recommendation Algorithm Benchmark</h2>
            <p className="text-xs text-slate-400">
              Per-user chronological split (each user’s latest 20% of reviews held out), fit on train only, full-catalogue ranking with already-reviewed hotels excluded, K=10.
            </p>
          </div>
          <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
            Cutoff: K=10
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/70 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Model Name</th>
                <th className="py-3 px-4">Family</th>
                <th className="py-3 px-4 font-mono">NDCG@10</th>
                <th className="py-3 px-4 font-mono">Recall@10</th>
                <th className="py-3 px-4 font-mono">Precision@10</th>
                <th className="py-3 px-4 font-mono">Hit rate</th>
                <th className="py-3 px-4">Specialization</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {(Array.isArray(models) ? models : []).map((m) => (
                <tr key={m.model_name} className="hover:bg-slate-850/30 transition">
                  <td className="py-3.5 px-4 font-semibold text-white">{m.model_name}</td>
                  <td className="py-3.5 px-4 text-xs">
                    <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60">
                      {m.model_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-cyan-400">
                    {fmt(m.ndcg_at_10)}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-emerald-400">
                    {fmt(m.recall_at_10)}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">
                    {fmt(m.precision_at_10)}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-indigo-400">
                    {fmt(m.hit_rate)}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-400">
                    {m.description}
                    {m.status === "not_evaluable" && m.reason && (
                      <span className="block text-amber-300/90 mt-1">Not evaluable: {m.reason}</span>
                    )}
                    {m.rating_metrics && (
                      <span className="block text-emerald-300/90 mt-1 font-mono">
                        Rating prediction: RMSE {fmt(m.rating_metrics.rmse, 3)} (global-mean baseline {fmt(m.rating_metrics.baseline_global_mean_rmse, 3)}), MAE {fmt(m.rating_metrics.mae, 3)}
                      </span>
                    )}
                    {m.weights && (
                      <span className="block text-emerald-300/90 mt-1 font-mono">
                        Tuned weights (validation set): {Object.entries(m.weights).map(([k, v]) => `${k} ${v}`).join(" · ")}
                      </span>
                    )}
                    {m.text_metrics && (
                      <span className="block text-emerald-300/90 mt-1 font-mono">
                        3-class text classification on {m.text_metrics.n_test_reviews.toLocaleString()} held-out reviews: accuracy {fmt(m.text_metrics.accuracy, 3)} (majority-class {fmt(m.text_metrics.majority_class_accuracy, 3)}), macro-F1 {fmt(m.text_metrics.macro_f1, 3)} (majority {fmt(m.text_metrics.majority_class_macro_f1, 3)}), AUC pos-vs-rest {fmt(m.text_metrics.auc_positive_vs_rest, 3)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.model_performance.leakage_checks && (
        <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
          <h2 className="text-lg font-bold text-white">Data Leakage Checks</h2>
          <p className="text-xs text-slate-400 mb-3">Verified by the training pipeline before any model is fit; all must be 0.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            {Object.entries(data.model_performance.leakage_checks).map(([k, v]) => (
              <div key={k} className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-slate-400 block">{k.replace(/_/g, " ")}</span>
                <span className={`text-lg font-black ${v === 0 ? "text-emerald-400" : "text-rose-400"}`}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Spark vs Pandas Benchmarking */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
        <div className="mb-4">
          <h2 className="text-lg font-bold text-white">Apache Spark vs Pandas Performance Scaling</h2>
          <p className="text-xs text-slate-400">
            Measured multi-column aggregation timings; at these sizes Spark start-up overhead dominates
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {(Array.isArray(benchmarks) ? benchmarks : []).map((b) => (
            <div key={`${b.dataset_size}-${b.operation}`} className="p-5 rounded-xl bg-slate-950/80 border border-slate-800">
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold text-white">{b.dataset_size.toLocaleString()} Records</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                  {b.winner} faster
                </span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Pandas Time:</span>
                  <span className="font-mono text-slate-200">{b.pandas_seconds}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Spark 3.5 Time:</span>
                  <span className="font-mono text-cyan-400 font-bold">{b.spark_seconds}s</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
