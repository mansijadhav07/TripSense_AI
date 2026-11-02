import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import { ModelMetrics } from "@/lib/api";

const models: ModelMetrics[] = [
  {
    model_name: "Hybrid Ensemble",
    model_type: "ensemble",
    description: "Validation-tuned blend",
    status: "evaluated",
    ndcg_at_10: 0.0724,
    recall_at_10: 0.1196,
    precision_at_10: 0.0232,
    hit_rate: 0.2088,
    weights: { cf: 0.6, content: 0.3, sentiment: 0.1 },
  },
  {
    model_name: "Random Baseline",
    model_type: "non_personalized",
    description: "Random ranking",
    status: "evaluated",
    ndcg_at_10: 0.0108,
    recall_at_10: 0.0209,
    precision_at_10: 0.0042,
    hit_rate: 0.0416,
  },
  {
    model_name: "Unavailable model",
    model_type: "personalized",
    description: "Not evaluated",
    status: "not_evaluable",
    ndcg_at_10: null,
    recall_at_10: null,
    precision_at_10: null,
    hit_rate: null,
  },
];

describe("analytics charts", () => {
  it("compares actual evaluated metrics and switches metric views", () => {
    render(<AnalyticsCharts models={models} hybridWeights={{ cf: 0.6, content: 0.3, sentiment: 0.1 }} />);

    expect(screen.getByRole("img", { name: /NDCG at 10 comparison: Hybrid Ensemble 0.0724, Random Baseline 0.0108/ })).toBeInTheDocument();
    expect(screen.getByText("Collaborative filtering")).toBeInTheDocument();
    expect(screen.getByText("60%")).toBeInTheDocument();
    expect(screen.queryByText("Unavailable model")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Recall@10" }));
    const recallChart = screen.getByRole("img", { name: /Recall at 10 comparison: Hybrid Ensemble 0.1196, Random Baseline 0.0209/ });
    expect(recallChart).toBeInTheDocument();
    expect(recallChart.firstElementChild?.children[1].firstElementChild).toHaveTextContent(/^0(?:\.0+)?$/);
    expect(screen.getByRole("button", { name: "Recall@10" })).toHaveAttribute("aria-pressed", "true");

    for (const metric of ["Precision@10", "Hit rate"]) {
      fireEvent.click(screen.getByRole("button", { name: metric }));
      const chart = screen.getByRole("img", { name: new RegExp(`${metric.replace("@", " at ")} comparison`) });
      expect(chart.firstElementChild?.children[1].firstElementChild).toHaveTextContent(/^0(?:\.0+)?$/);
    }
  });

  it("shows clear empty states when evaluated chart data is unavailable", () => {
    render(<AnalyticsCharts models={[]} />);

    expect(screen.getByText("No evaluated models have this ranking metric.")).toBeInTheDocument();
    expect(screen.getByText("Hybrid component weights are not available in the evaluation results.")).toBeInTheDocument();
  });
});
