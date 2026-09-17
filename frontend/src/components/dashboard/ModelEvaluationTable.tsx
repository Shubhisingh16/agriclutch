"use client";

import React from "react";
import { ModelEvaluationMetric } from "@/lib/api/types";

interface ModelEvaluationTableProps {
  evaluations: ModelEvaluationMetric[];
  splitCount: number;
  horizon: number;
  isLoading?: boolean;
}

export const ModelEvaluationTable: React.FC<ModelEvaluationTableProps> = ({
  evaluations,
  splitCount,
  horizon,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-3">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
        <p className="text-sm text-zinc-400">Executing walk-forward cross-validation across models...</p>
      </div>
    );
  }

  if (evaluations.length === 0) {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-2">
        <h4 className="text-sm font-semibold text-zinc-300">No Evaluation Benchmarks Available</h4>
        <p className="text-xs text-zinc-500">
          Insufficient historical depth to form multi-fold rolling temporal splits.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 backdrop-blur-md shadow-xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-zinc-800/80">
        <div>
          <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2">
            <span>📊</span> Rolling-Origin Temporal Benchmark Comparison
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Evaluation Protocol: Walk-forward cross-validation ({splitCount} folds) &bull; Horizon: {horizon} Days &bull; No Presumed Winner
          </p>
        </div>
        <div className="text-[11px] font-mono text-zinc-500 px-3 py-1 bg-zinc-950 rounded-lg border border-zinc-800">
          Identical Folds &bull; Zero Leakage
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-400 font-medium">
              <th className="py-2.5 px-3">Model Engine</th>
              <th className="py-2.5 px-3 text-right">MAE (₹/kg)</th>
              <th className="py-2.5 px-3 text-right">RMSE (₹/kg)</th>
              <th className="py-2.5 px-3 text-right">sMAPE (%)</th>
              <th className="py-2.5 px-3 text-right">MASE</th>
              <th className="py-2.5 px-3 text-right">Pinball Loss</th>
              <th className="py-2.5 px-3 text-right">80% Coverage</th>
              <th className="py-2.5 px-3 text-right">Folds</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60 font-mono">
            {evaluations.map((metric) => {
              const isChronos = metric.model_name.toLowerCase().includes("chronos");
              return (
                <tr
                  key={metric.model_name}
                  className={`hover:bg-zinc-800/40 transition-colors ${
                    isChronos ? "bg-purple-950/20" : ""
                  }`}
                >
                  <td className="py-3 px-3 font-sans font-medium text-zinc-200 flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        isChronos ? "bg-purple-500" : "bg-zinc-500"
                      }`}
                    />
                    <span>{metric.model_name.replace("_", " ").toUpperCase()}</span>
                    {isChronos && (
                      <span className="text-[10px] text-purple-300 font-mono px-1.5 py-0.5 rounded bg-purple-900/60 border border-purple-700/50">
                        FOUNDATION
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-right text-zinc-200 font-bold">
                    ₹{metric.mae.toFixed(3)}
                  </td>
                  <td className="py-3 px-3 text-right text-zinc-300">
                    ₹{metric.rmse.toFixed(3)}
                  </td>
                  <td className="py-3 px-3 text-right text-zinc-300">
                    {metric.smape.toFixed(2)}%
                  </td>
                  <td className="py-3 px-3 text-right text-zinc-300">
                    {metric.mase.toFixed(3)}
                  </td>
                  <td className="py-3 px-3 text-right text-zinc-300">
                    {metric.pinball_loss.toFixed(3)}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] ${
                        metric.coverage_80 >= 70 && metric.coverage_80 <= 90
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {metric.coverage_80.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right text-zinc-500">
                    {metric.windows_evaluated}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="p-3 rounded-xl bg-zinc-950/60 border border-zinc-800 text-[11px] text-zinc-400 space-y-1">
        <p>
          <strong className="text-zinc-300">Scientific Cross-Validation Note:</strong> Models are evaluated strictly chronologically on walk-forward rolling test windows with identical temporal cutoffs. Features and scaling are fit only on historical context prior to each cutoff.
        </p>
      </div>
    </div>
  );
};
