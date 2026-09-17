"use client";

import React from "react";
import { NRVMarketComparisonResponse } from "@/lib/api/types";

interface MarketNRVComparisonProps {
  comparison: NRVMarketComparisonResponse;
}

export const MarketNRVComparison: React.FC<MarketNRVComparisonProps> = ({ comparison }) => {
  const isDemo = comparison.scenarios.some((s) => s.provenance_status === "DEMO");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">
            Cross-Market Net Realization Comparison ({comparison.commodity_id.toUpperCase()})
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Objective cost & net realization comparison for {comparison.harvest_quantity_kg.toLocaleString("en-IN")} kg at {comparison.storage_days} holding days ({comparison.storage_type}).
          </p>
        </div>
        {isDemo && (
          <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
            DEMO ASSUMPTION
          </span>
        )}
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {comparison.scenarios.map((m) => (
          <div
            key={m.market_id}
            className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-3">
                <div>
                  <h4 className="text-sm font-semibold text-white">{m.market_name}</h4>
                  <div className="text-xs text-zinc-500 font-mono">
                    ID: {m.market_id} • {m.distance_km} km
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-zinc-400">Net Value (P50)</div>
                  <div className="text-base font-bold text-emerald-400">
                    ₹{m.nrv_p50.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-xs text-zinc-400 font-mono">
                    ₹{m.nrv_per_kg_p50.toFixed(2)}/kg
                  </div>
                </div>
              </div>

              {/* Economic Metric Rows */}
              <div className="space-y-2 py-3 border-t border-b border-zinc-800/80 text-xs">
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="text-zinc-400">Gross Rev:</span>
                  <span className="font-mono">
                    ₹{m.gross_revenue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="text-zinc-400">Transport:</span>
                  <span className="font-mono text-blue-400">
                    -₹{m.transport_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="text-zinc-400">Storage:</span>
                  <span className="font-mono text-cyan-400">
                    -₹{m.storage_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="text-zinc-400">Handling & Market Fee:</span>
                  <span className="font-mono text-amber-400">
                    -₹{(m.handling_cost + m.market_charges).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="text-zinc-400">Spoilage Loss:</span>
                  <span className="font-mono text-red-400">
                    -₹{m.spoilage_loss_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between items-center pt-1 border-t border-zinc-800 text-zinc-200">
                  <span className="font-medium text-zinc-300">Total Deductions:</span>
                  <span className="font-mono font-medium text-rose-400">
                    -₹{m.total_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>
            </div>

            {/* Break-Even Quoted Price */}
            <div className="mt-3 pt-2 text-xs flex items-center justify-between bg-zinc-950/60 p-2 rounded-lg border border-zinc-800/60">
              <span className="text-zinc-400">Break-Even Quoted Price:</span>
              <span className="font-mono font-bold text-amber-300">
                {m.break_even_price !== null ? `₹${m.break_even_price.toFixed(2)}/kg` : "N/A"}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Comparative Summary Table */}
      <div className="rounded-xl border border-zinc-800 overflow-hidden">
        <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 flex justify-between items-center">
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
            Objective Mandi Economic Ledger
          </div>
          <div className="text-[11px] text-zinc-500 font-mono">
            Values strictly auditable; no ranking applied
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-zinc-900/40 text-zinc-400 font-mono border-b border-zinc-800">
              <tr>
                <th className="p-3 text-left">Market</th>
                <th className="p-3 text-right">Gross</th>
                <th className="p-3 text-right">Transport</th>
                <th className="p-3 text-right">Storage</th>
                <th className="p-3 text-right">Other Fees</th>
                <th className="p-3 text-right">Total Friction</th>
                <th className="p-3 text-right">NRV (P50)</th>
                <th className="p-3 text-right font-semibold text-emerald-400">Net ₹/kg</th>
                <th className="p-3 text-right font-semibold text-amber-400">Break-Even</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50 font-mono">
              {comparison.scenarios.map((m) => (
                <tr key={m.market_id} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="p-3 font-sans font-medium text-white">{m.market_name}</td>
                  <td className="p-3 text-right text-zinc-300">
                    ₹{m.gross_revenue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </td>
                  <td className="p-3 text-right text-blue-400">
                    ₹{m.transport_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </td>
                  <td className="p-3 text-right text-cyan-400">
                    ₹{m.storage_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </td>
                  <td className="p-3 text-right text-amber-400">
                    ₹{(m.handling_cost + m.market_charges + m.other_costs).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </td>
                  <td className="p-3 text-right text-rose-400">
                    ₹{m.total_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </td>
                  <td className="p-3 text-right font-bold text-white">
                    ₹{m.nrv_p50.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </td>
                  <td className="p-3 text-right font-bold text-emerald-400">
                    ₹{m.nrv_per_kg_p50.toFixed(2)}
                  </td>
                  <td className="p-3 text-right font-bold text-amber-300">
                    {m.break_even_price !== null ? `₹${m.break_even_price.toFixed(2)}` : "—"}
                  </td>
                </tr>
              ))}
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
