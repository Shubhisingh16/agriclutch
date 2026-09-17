"use client";

import React from "react";
import { CostBreakdownResponse } from "@/lib/api/types";

interface CostBreakdownProps {
  costBreakdown: CostBreakdownResponse;
  effectiveQuantityKg: number;
  initialQuantityKg: number;
}

export const CostBreakdown: React.FC<CostBreakdownProps> = ({
  costBreakdown,
  effectiveQuantityKg,
  initialQuantityKg,
}) => {
  const items = [
    { key: "transport", data: costBreakdown.transport_cost, color: "bg-blue-500", border: "border-blue-500/30" },
    { key: "storage", data: costBreakdown.storage_cost, color: "bg-cyan-500", border: "border-cyan-500/30" },
    { key: "handling", data: costBreakdown.handling_cost, color: "bg-amber-500", border: "border-amber-500/30" },
    { key: "market", data: costBreakdown.market_charges, color: "bg-rose-500", border: "border-rose-500/30" },
    { key: "other", data: costBreakdown.other_costs, color: "bg-purple-500", border: "border-purple-500/30" },
    { key: "loss", data: costBreakdown.loss_cost, color: "bg-red-500", border: "border-red-500/30" },
    { key: "risk", data: costBreakdown.risk_cost, color: "bg-zinc-500", border: "border-zinc-500/30" },
  ];

  const total = costBreakdown.total_cost > 0 ? costBreakdown.total_cost : 1.0;

  return (
    <div className="space-y-6">
      {/* Header & Total */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
        <div>
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider">Total Friction Deductions</div>
          <div className="text-2xl font-bold text-white mt-0.5">
            ₹{costBreakdown.total_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono text-zinc-400">Effective Quantity Handled</div>
          <div className="text-sm font-semibold text-emerald-400 mt-0.5">
            {effectiveQuantityKg.toLocaleString("en-IN", { maximumFractionDigits: 1 })} kg
            <span className="text-xs text-zinc-500 ml-1.5 font-normal">
              (from {initialQuantityKg.toLocaleString("en-IN")} kg harvested)
            </span>
          </div>
        </div>
      </div>

      {/* Stacked Visual Bar */}
      <div>
        <div className="text-xs font-medium text-zinc-400 mb-2">Cost Share Distribution</div>
        <div className="h-4 w-full rounded-full bg-zinc-800 overflow-hidden flex shadow-inner">
          {items.map((item) => {
            const pct = (item.data.amount / total) * 100;
            if (pct <= 0) return null;
            return (
              <div
                key={item.key}
                className={`${item.color} transition-all duration-300 relative group`}
                style={{ width: `${pct}%` }}
                title={`${item.data.name}: ₹${item.data.amount} (${pct.toFixed(1)}%)`}
              />
            );
          })}
        </div>
      </div>

      {/* Itemized Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-400 font-mono">
              <th className="py-2.5 px-3">Cost Category</th>
              <th className="py-2.5 px-3">Rate Basis</th>
              <th className="py-2.5 px-3 text-right">Deduction (₹)</th>
              <th className="py-2.5 px-3 text-right">% of Total</th>
              <th className="py-2.5 px-3">Provenance Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-850">
            {items.map((item) => {
              const pct = (item.data.amount / total) * 100;
              const isDemo = item.data.provenance.is_demo;
              const rateBasisDisplay =
                item.key === "risk" && (item.data.rate_basis === "NOT_MODELED" || item.data.amount === 0)
                  ? "Risk adjustment not modeled"
                  : item.data.rate_basis || "Fixed rate";

              return (
                <tr key={item.key} className="hover:bg-zinc-900/40 transition-colors">
                  <td className="py-3 px-3 font-medium text-zinc-200 flex items-center space-x-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${item.color} inline-block`} />
                    <span>{item.data.name}</span>
                  </td>
                  <td className="py-3 px-3 font-mono text-zinc-400">
                    {rateBasisDisplay}
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold text-right text-zinc-100">
                    ₹{item.data.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-3 font-mono text-right text-zinc-400">
                    {pct.toFixed(1)}%
                  </td>
                  <td className="py-3 px-3">
                    {item.key === "risk" && (item.data.rate_basis === "NOT_MODELED" || item.data.amount === 0) ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-800 text-zinc-400 border border-zinc-700">
                        NOT_MODELED
                      </span>
                    ) : isDemo ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                        DEMO ASSUMPTION
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {item.data.provenance.status}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 font-mono">
        ℹ️ <span className="font-semibold text-zinc-300">Risk Model Semantics:</span> Operational risk penalty is ₹0.00 because risk adjustment is not modeled. This reflects the absence of a certified behavioral or transit risk model, and must NOT be communicated as zero real-world risk. Downside price variance is captured separately via the P10 quantile forecast.
      </div>
    </div>
  );
};
