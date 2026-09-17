"use client";

import React from "react";
import { NRVTimeComparisonResponse } from "@/lib/api/types";

interface TimeScenarioComparisonProps {
  comparison: NRVTimeComparisonResponse;
}

export const TimeScenarioComparison: React.FC<TimeScenarioComparisonProps> = ({ comparison }) => {
  const baseScenario = comparison.scenarios.find((s) => s.storage_days === 0) || comparison.scenarios[0];
  const baseNRV = baseScenario ? baseScenario.nrv_p50 : 1;
  const isDemo = comparison.scenarios.some((s) => s.provenance_status === "DEMO");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">
            Temporal Holding Horizon Trajectory ({comparison.commodity_id.toUpperCase()} @ {comparison.market_id})
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Evaluating gross price evolution against storage fees and cumulative spoilage decay ({comparison.storage_type} storage).
          </p>
        </div>
        {isDemo && (
          <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
            DEMO ASSUMPTION
          </span>
        )}
      </div>

      {/* Scenario Horizon Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {comparison.scenarios.map((s) => {
          const deltaNRV = s.nrv_p50 - baseNRV;
          const deltaPerKg = s.nrv_per_kg_p50 - (baseScenario ? baseScenario.nrv_per_kg_p50 : 0);
          const isBase = s.storage_days === 0;

          return (
            <div
              key={s.storage_days}
              className={`p-4 rounded-xl border transition-all ${
                isBase
                  ? "bg-zinc-900/80 border-zinc-700 shadow-md"
                  : "bg-zinc-900/40 border-zinc-800/80 hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-zinc-300">
                  {isBase ? "T+0 (Immediate Sale)" : `T+${s.storage_days} Days Holding`}
                </span>
                <span className="text-[10px] font-mono text-zinc-500">{s.scenario_date}</span>
              </div>

              <div className="my-3">
                <div className="text-xs font-mono text-zinc-400">Realizable Net (P50)</div>
                <div className="text-xl font-bold text-white mt-0.5">
                  ₹{s.nrv_p50.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </div>
                <div className="text-xs font-mono text-zinc-400">
                  ₹{s.nrv_per_kg_p50.toFixed(2)}/kg
                </div>

                {!isBase && (
                  <div
                    className={`text-xs font-mono mt-1.5 flex items-center gap-1 font-semibold ${
                      deltaNRV >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    <span>{deltaNRV >= 0 ? "▲ +" : "▼ "}</span>
                    <span>₹{Math.abs(deltaNRV).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
                    <span className="text-[10px] font-normal text-zinc-500">
                      ({deltaPerKg >= 0 ? "+" : ""}{deltaPerKg.toFixed(2)}/kg vs T+0)
                    </span>
                  </div>
                )}
              </div>

              {/* Economic Drain Metrics */}
              <div className="pt-3 border-t border-zinc-800/80 space-y-1.5 text-xs">
                <div className="flex justify-between text-zinc-400">
                  <span>Gross Rev:</span>
                  <span className="font-mono text-zinc-200">
                    ₹{s.gross_revenue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Storage Fee:</span>
                  <span className="font-mono text-cyan-400">
                    ₹{s.storage_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Spoilage Loss:</span>
                  <span className="font-mono text-rose-400">
                    ₹{s.spoilage_loss_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between text-zinc-400">
                  <span>Eff. Quantity:</span>
                  <span className="font-mono text-zinc-300">
                    {s.effective_quantity_kg.toFixed(0)} kg
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Trajectory Table */}
      <div className="rounded-xl border border-zinc-800 overflow-hidden">
        <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 flex justify-between items-center">
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
            Time Horizon Trade-Off Ledger
          </div>
          <div className="text-[11px] text-zinc-500 font-mono">
            Evaluates price gain against perishability decay
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-zinc-900/40 text-zinc-400 font-mono border-b border-zinc-800">
              <tr>
                <th className="p-3 text-left">Holding Duration</th>
                <th className="p-3 text-right">Scenario Date</th>
                <th className="p-3 text-right">Eff. Qty (kg)</th>
                <th className="p-3 text-right">Gross</th>
                <th className="p-3 text-right">Storage Cost</th>
                <th className="p-3 text-right">Spoilage Loss</th>
                <th className="p-3 text-right">Total Deductions</th>
                <th className="p-3 text-right font-semibold text-emerald-400">NRV (P50)</th>
                <th className="p-3 text-right">Δ Net vs T+0</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50 font-mono">
              {comparison.scenarios.map((s) => {
                const diff = s.nrv_p50 - baseNRV;
                return (
                  <tr key={s.storage_days} className="hover:bg-zinc-900/30 transition-colors">
                    <td className="p-3 font-sans font-medium text-white">
                      {s.storage_days === 0 ? "Immediate (0 days)" : `${s.storage_days} days`}
                    </td>
                    <td className="p-3 text-right text-zinc-400">{s.scenario_date}</td>
                    <td className="p-3 text-right text-zinc-300">
                      {s.effective_quantity_kg.toFixed(0)}
                    </td>
                    <td className="p-3 text-right text-zinc-300">
                      ₹{s.gross_revenue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </td>
                    <td className="p-3 text-right text-cyan-400">
                      ₹{s.storage_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </td>
                    <td className="p-3 text-right text-rose-400">
                      ₹{s.spoilage_loss_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </td>
                    <td className="p-3 text-right text-rose-300">
                      ₹{s.total_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </td>
                    <td className="p-3 text-right font-bold text-white">
                      ₹{s.nrv_p50.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </td>
                    <td
                      className={`p-3 text-right font-bold ${
                        diff > 0 ? "text-emerald-400" : diff < 0 ? "text-rose-400" : "text-zinc-400"
                      }`}
                    >
                      {s.storage_days === 0 ? "—" : `${diff >= 0 ? "+" : ""}₹${diff.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 font-mono">
        ℹ️ <span className="font-semibold text-zinc-300">Disclaimer:</span> {comparison.disclaimer}
      </div>
    </div>
  );
};
