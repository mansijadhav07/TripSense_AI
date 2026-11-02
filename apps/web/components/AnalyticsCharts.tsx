"use client";

import { useState } from "react";
import { ModelMetrics } from "@/lib/api";

type RankingMetric = "ndcg_at_10" | "recall_at_10" | "precision_at_10" | "hit_rate";

const rankingMetrics: { key: RankingMetric; label: string; title: string }[] = [
  { key: "ndcg_at_10", label: "NDCG@10", title: "NDCG at 10" },
  { key: "recall_at_10", label: "Recall@10", title: "Recall at 10" },
  { key: "precision_at_10", label: "Precision@10", title: "Precision at 10" },
  { key: "hit_rate", label: "Hit rate", title: "Hit rate" },
];

const hybridComponents = [
  { key: "cf", label: "Collaborative filtering" },
  { key: "content", label: "Hotel content" },
  { key: "sentiment", label: "Review sentiment" },
] as const;

function formatMetric(value: number): string {
  return value.toFixed(4);
}

function getAxisMaximum(value: number): number {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  const niceStep = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find((step) => step >= normalized);
  return (niceStep ?? 10) * magnitude;
}

function formatAxisTick(value: number, axisMax: number): string {
  const digits = axisMax < 0.1 ? 3 : axisMax < 1 ? 2 : 1;
  return value.toFixed(digits);
}

export default function AnalyticsCharts({
  models,
  hybridWeights,
}: {
  models: ModelMetrics[];
  hybridWeights?: Record<string, number>;
}) {
  const [selectedMetric, setSelectedMetric] = useState<RankingMetric>("ndcg_at_10");
  const metric = rankingMetrics.find(({ key }) => key === selectedMetric)!;
  const rankedModels = models
    .filter((model) => model.status === "evaluated" && model[selectedMetric] !== null && model[selectedMetric] !== undefined)
    .map((model) => ({ name: model.model_name, value: model[selectedMetric] as number }))
    .sort((a, b) => b.value - a.value);
  const axisMax = getAxisMaximum(Math.max(...rankedModels.map(({ value }) => value), 0));
  const ticks = Array.from({ length: 5 }, (_, index) => (axisMax * index) / 4);
  const components = hybridComponents
    .map((component) => ({ ...component, value: hybridWeights?.[component.key] ?? 0 }))
    .filter((component) => component.value > 0);
  const componentTotal = components.reduce((total, component) => total + component.value, 0);

  return (
    <section aria-label="Recommendation model charts" className="grid gap-6 lg:grid-cols-[minmax(0,1.7fr)_minmax(280px,1fr)]">
      <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-white">Ranking quality by model</h2>
            <p className="mt-1 text-xs text-slate-400">Held-out test results · higher is better</p>
          </div>
          <div role="group" aria-label="Ranking metric" className="flex flex-wrap gap-3">
            {rankingMetrics.map((option) => (
              <button
                key={option.key}
                type="button"
                aria-pressed={selectedMetric === option.key}
                onClick={() => setSelectedMetric(option.key)}
                className={`border-b pb-1 text-xs transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-400 ${
                  selectedMetric === option.key
                    ? "border-cyan-400 text-white"
                    : "border-transparent text-slate-400 hover:text-white"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {rankedModels.length > 0 ? (
          <div
            role="img"
            aria-label={`${metric.title} comparison: ${rankedModels.map(({ name, value }) => `${name} ${formatMetric(value)}`).join(", ")}`}
            className="mt-6"
          >
            <div
              className="mb-2 grid grid-cols-[minmax(0,42%)_minmax(0,1fr)_3.5rem] gap-3 text-[11px] tabular-nums text-slate-400"
              aria-hidden="true"
            >
              <span />
              <div className="flex justify-between">
                {ticks.map((tick, index) => (
                  <span key={index}>{formatAxisTick(tick, axisMax)}</span>
                ))}
              </div>
              <span />
            </div>
            <div className="space-y-3">
              {rankedModels.map(({ name, value }) => (
                <div key={name} className="group grid grid-cols-[minmax(0,42%)_minmax(0,1fr)_3.5rem] items-center gap-3">
                  <span className="truncate text-xs text-slate-300" title={name}>{name}</span>
                  <div className="relative h-3 border-l border-slate-700 bg-slate-950/70">
                    {[25, 50, 75].map((position) => (
                      <span key={position} aria-hidden="true" className="absolute inset-y-0 border-l border-slate-800" style={{ left: `${position}%` }} />
                    ))}
                    <span
                      className="absolute inset-y-0 left-0 bg-cyan-500 transition-[filter,width] duration-300 group-hover:bg-cyan-300 group-hover:drop-shadow-[0_0_7px_rgba(34,211,238,0.75)] motion-reduce:transition-none"
                      style={{ width: `${Math.min(100, (value / axisMax) * 100)}%` }}
                    >
                      <span className="sr-only">{metric.title}: {formatMetric(value)}</span>
                    </span>
                  </div>
                  <span className="text-right font-mono text-xs tabular-nums text-white">{formatMetric(value)}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-between border-t border-slate-800 pt-3 text-[11px] text-slate-400">
              <span>{metric.title} · K=10</span>
              <span>Scale: 0–{formatAxisTick(axisMax, axisMax)}</span>
            </div>
          </div>
        ) : (
          <p className="mt-6 border-t border-slate-800 pt-4 text-sm text-slate-400">
            No evaluated models have this ranking metric.
          </p>
        )}
      </article>

      <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6">
        <div>
          <h2 className="text-base font-semibold text-white">How the hybrid score is blended</h2>
          <p className="mt-1 text-xs text-slate-400">Validation-tuned component weights</p>
        </div>

        {components.length > 0 && componentTotal > 0 ? (
          <div
            role="img"
            aria-label={`Hybrid weights: ${components.map(({ label, value }) => `${label} ${Math.round(value * 100)} percent`).join(", ")}`}
            className="mt-6"
          >
            <div className="flex h-3 overflow-hidden rounded-sm bg-slate-950" aria-hidden="true">
              {components.map((component) => (
                <span
                  key={component.key}
                  className="h-full border-r-2 border-slate-950 bg-cyan-400 last:border-r-0"
                  style={{
                    width: `${(component.value / componentTotal) * 100}%`,
                    opacity: component.key === "cf" ? 1 : component.key === "content" ? 0.65 : 0.35,
                  }}
                />
              ))}
            </div>
            <ul className="mt-5 space-y-4">
              {components.map((component) => (
                <li key={component.key} className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-slate-300">{component.label}</span>
                  <span className="font-mono tabular-nums text-white">{Math.round(component.value * 100)}%</span>
                </li>
              ))}
            </ul>
            <p className="mt-5 border-t border-slate-800 pt-4 text-xs leading-relaxed text-slate-400">
              The hybrid model combines user–hotel patterns with hotel attributes and review sentiment, helping balance sparse interaction history.
            </p>
          </div>
        ) : (
          <p className="mt-6 border-t border-slate-800 pt-4 text-sm text-slate-400">
            Hybrid component weights are not available in the evaluation results.
          </p>
        )}
      </article>
    </section>
  );
}
