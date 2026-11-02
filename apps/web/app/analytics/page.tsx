import { Suspense } from "react";
import { connection } from "next/server";
import { fetchAnalyticsOverview } from "@/lib/api";
import AnalyticsCharts from "@/components/AnalyticsCharts";

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 py-20 text-slate-400">Loading analytics…</div>}>
      <AnalyticsContent />
    </Suspense>
  );
}

async function AnalyticsContent() {
  await connection();
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
  const hybridWeights = data.model_performance.tuning?.hybrid_weights
    ?? models.find((model) => model.model_type === "ensemble")?.weights;
  const fmt = (v: number | null | undefined, d = 4) => (v === null || v === undefined ? "n/a" : v.toFixed(d));
  const num = (v: number | undefined) => (v === undefined ? "—" : v.toLocaleString());

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      <div>
        <h1 className="text-2xl font-extrabold text-white sm:text-3xl">System Analytics & ML Evaluation</h1>
        <p className="text-sm text-slate-400 mt-1">
          Verified TripAdvisor source dataset statistics and model-ranking evaluation
        </p>
      </div>

      {/* Dataset Overview Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-sm text-slate-400 block">Source reviews</span>
          <span className="text-2xl font-black tabular-nums text-white mt-1 block">
            {num(ds.total_reviews)}
          </span>
          <span className="text-[13px] text-emerald-400">TripAdvisor dataset</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-sm text-slate-400 block">Unique reviewers</span>
          <span className="text-2xl font-black tabular-nums text-cyan-400 mt-1 block">
            {num(ds.total_users)}
          </span>
          <span className="text-[13px] text-slate-400">Distinct user IDs</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-sm text-slate-400 block">Unique hotel IDs</span>
          <span className="text-2xl font-black tabular-nums text-indigo-400 mt-1 block">
            {num(ds.distinct_hotel_ids ?? ds.total_hotels)}
          </span>
          <span className="text-[13px] text-slate-400">One ID per source review</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-sm text-slate-400 block">Average rating</span>
          <span className="text-2xl font-black tabular-nums text-amber-400 mt-1 block">
            {fmt(ds.avg_rating, 2)} stars
          </span>
          <span className="text-[13px] text-slate-400">Std: ±{fmt(ds.rating_std, 2)}</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-sm text-slate-400 block">Matrix sparsity</span>
          <span className="text-2xl font-black tabular-nums text-rose-400 mt-1 block">
            {ds.sparsity_percent ?? "—"}%
          </span>
          <span className="text-[13px] text-rose-300">User × hotel matrix</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-sm text-slate-400 block">Temporal range</span>
          <span className="text-sm font-bold text-slate-200 mt-2 block">
            {ds.date_range ? `${ds.date_range.start} – ${ds.date_range.end}` : "—"}
          </span>
          <span className="text-[13px] text-slate-400">Review post dates</span>
        </div>
      </div>

      {ds.data_warning && (
        <div role="alert" className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
          <strong>Data limitation:</strong> {ds.data_warning}
        </div>
      )}

      <div>
        <h2 className="mb-1 text-lg font-bold text-white">Model ranking evaluation</h2>
        <p className="text-[13px] text-slate-400">
          Evaluated on a separate synthetic dataset ({num(ds.benchmark_total_reviews ?? undefined)} reviews, seed 42); these metrics are not computed from the TripAdvisor source dataset.
        </p>
      </div>
      <AnalyticsCharts models={models} hybridWeights={hybridWeights} />

      {/* Model Performance Comparison Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Recommendation Algorithm Benchmark</h2>
            <p className="text-[13px] text-slate-400">
              Per-user chronological split (each user’s latest 20% of reviews held out), fit on train only, full-catalogue ranking with already-reviewed hotels excluded, K=10.
            </p>
          </div>
          <span className="text-[13px] font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
            Cutoff: K=10
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm tabular-nums">
            <thead className="bg-slate-950/70 text-[13px] text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Model name</th>
                <th className="py-3 px-4">Family</th>
                <th className="py-3 px-4 text-right font-mono">NDCG@10</th>
                <th className="py-3 px-4 text-right font-mono">Recall@10</th>
                <th className="py-3 px-4 text-right font-mono">Precision@10</th>
                <th className="py-3 px-4 text-right font-mono">Hit rate</th>
                <th className="py-3 px-4">Specialization</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {(Array.isArray(models) ? models : []).map((m) => (
                <tr key={m.model_name} className="hover:bg-slate-850/30 transition">
                  <td className="py-3.5 px-4 font-semibold text-white">{m.model_name}</td>
                  <td className="py-3.5 px-4 text-[13px]">
                    <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60">
                      {m.model_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-bold text-cyan-400">
                    {fmt(m.ndcg_at_10)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-emerald-400">
                    {fmt(m.recall_at_10)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-slate-300">
                    {fmt(m.precision_at_10)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-indigo-400">
                    {fmt(m.hit_rate)}
                  </td>
                  <td className="py-3.5 px-4 text-[13px] text-slate-400">
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

    </div>
  );
}
