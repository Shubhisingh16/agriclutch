"use client";

import React, { useState } from "react";
import { NRVDistributionResponse } from "@/lib/api/types";

interface NRVDistributionChartProps {
  forecastQuantiles: Record<string, number>;
  grossRevenueQuantiles: Record<string, number>;
  nrvQuantiles: NRVDistributionResponse;
  nrvPerKgQuantiles: NRVDistributionResponse;
  totalCost: number;
}

export const NRVDistributionChart: React.FC<NRVDistributionChartProps> = ({
  forecastQuantiles,
  grossRevenueQuantiles,
  nrvQuantiles,
  nrvPerKgQuantiles,
  totalCost,
}) => {
  const [activeQuantile, setActiveQuantile] = useState<string>("p50");

  const quantilesList = [
    { key: "p10", label: "P10 (Floor / Downside)", desc: "10% chance price falls below" },
    { key: "p20", label: "P20 (Conservative)", desc: "20th percentile estimate" },
    { key: "p50", label: "P50 (Median / Expected)", desc: "Central expected baseline" },
    { key: "p80", label: "P80 (Favorable)", desc: "80th percentile upside" },
    { key: "p90", label: "P90 (Ceiling / Upside)", desc: "Optimistic high realization" },
  ];

  const currentPrice = forecastQuantiles[activeQuantile] || 0;
  const currentRev = grossRevenueQuantiles[activeQuantile] || 0;
  const currentNRV = (nrvQuantiles as unknown as Record<string, number>)[activeQuantile] || 0;
  const currentNRVPerKg = (nrvPerKgQuantiles as unknown as Record<string, number>)[activeQuantile] || 0;

  // Visual bar scaling against max gross revenue
  const maxRev = Math.max(grossRevenueQuantiles["p90"] || 1, 1);
  const revPct = Math.min(100, Math.max(0, (currentRev / maxRev) * 100));
  const costPct = Math.min(100, Math.max(0, (totalCost / maxRev) * 100));
  const nrvPct = Math.min(100, Math.max(0, (currentNRV / maxRev) * 100));

  return (
    <div className="space-y-6">
      {/* Principle Banner */}
      <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 flex items-start space-x-3">
        <div className="text-xl">⚖️</div>
        <div>
          <div className="text-xs font-bold text-zinc-200">
            HEADLINE PRICE ≠ FARMER NET REALIZATION
          </div>
          <div className="text-xs text-zinc-400 mt-0.5">
            Quoted mandi rates do not include haulage, APMC cess, handling, or holding decay.
            Select a forecast quantile below to trace the exact economic transformation.
          </div>
        </div>
      </div>

      {/* Quantile Selector Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {quantilesList.map((q) => {
          const isActive = activeQuantile === q.key;
          return (
            <button
              key={q.key}
              onClick={() => setActiveQuantile(q.key)}
              className={`p-3 rounded-xl text-left border transition-all ${
                isActive
                  ? "bg-emerald-500/15 border-emerald-500/50 text-white shadow-lg shadow-emerald-500/10"
                  : "bg-zinc-900/40 border-zinc-800 hover:border-zinc-700 text-zinc-400"
              }`}
            >
              <div className="text-xs font-mono font-bold uppercase">{q.key}</div>
              <div className="text-sm font-bold text-zinc-200 mt-1">
                ₹{forecastQuantiles[q.key]?.toFixed(2)}
                <span className="text-[10px] text-zinc-500 font-normal">/kg</span>
              </div>
              <div className="text-[10px] text-zinc-500 truncate mt-0.5">{q.label.split(" ")[1]}</div>
            </button>
          );
        })}
      </div>

      {/* Waterfall Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Step 1: Headline Price & Revenue */}
        <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-zinc-400">1. FORECAST VALUE</span>
            <span className="text-xs font-bold text-blue-400 font-mono">P({activeQuantile})</span>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              ₹{currentRev.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-zinc-400 mt-1">
              Quoted Mandi Price: <strong className="text-zinc-200 font-mono">₹{currentPrice.toFixed(2)}/kg</strong>
            </div>
          </div>
          <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full transition-all duration-300" style={{ width: `${revPct}%` }} />
          </div>
        </div>

        {/* Step 2: Total Deductions */}
        <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-zinc-400">2. TOTAL DEDUCTIONS</span>
            <span className="text-xs font-bold text-rose-400 font-mono">FRICTION</span>
          </div>
          <div>
            <div className="text-2xl font-bold text-rose-400">
              -₹{totalCost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-zinc-400 mt-1">
              Transport, storage, handling, market cess, and loss
            </div>
          </div>
          <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
            <div className="h-full bg-rose-500 rounded-full transition-all duration-300" style={{ width: `${costPct}%` }} />
          </div>
        </div>

        {/* Step 3: Net Realizable Value */}
        <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-400">3. NET REALIZATION</span>
            <span className="text-xs font-bold text-emerald-400 font-mono">NRV</span>
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-300">
              ₹{currentNRV.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-emerald-400/80 mt-1">
              Net Realized Rate: <strong className="text-emerald-300 font-mono">₹{currentNRVPerKg.toFixed(2)}/kg</strong>
            </div>
          </div>
          <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full transition-all duration-300" style={{ width: `${nrvPct}%` }} />
          </div>
        </div>
      </div>

      {/* Complete Quantile Spectrum Table */}
      <div className="rounded-xl border border-zinc-800 overflow-hidden">
        <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 text-xs font-mono text-zinc-300">
          Distribution-Aware Net Realizable Value Spectrum
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 font-mono bg-zinc-900/30">
                <th className="py-2.5 px-3">Quantile Level</th>
                <th className="py-2.5 px-3 text-right">Quoted Price (₹/kg)</th>
                <th className="py-2.5 px-3 text-right">Gross Revenue (₹)</th>
                <th className="py-2.5 px-3 text-right">Total Costs (₹)</th>
                <th className="py-2.5 px-3 text-right font-bold text-emerald-400">Net Realization (₹)</th>
                <th className="py-2.5 px-3 text-right font-bold text-emerald-400">Realized Rate (₹/kg)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850">
              {(["p10", "p20", "p50", "p80", "p90"] as const).map((qk) => {
                const p = forecastQuantiles[qk] || 0;
                const rev = grossRevenueQuantiles[qk] || 0;
                const nrv = (nrvQuantiles as unknown as Record<string, number>)[qk] || 0;
                const nrvKg = (nrvPerKgQuantiles as unknown as Record<string, number>)[qk] || 0;
                const isSelected = activeQuantile === qk;

                return (
                  <tr
                    key={qk}
                    onClick={() => setActiveQuantile(qk)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? "bg-emerald-500/10 font-semibold" : "hover:bg-zinc-900/40"
                    }`}
                  >
                    <td className="py-3 px-3 font-mono uppercase text-zinc-300">
                      {qk} {qk === "p50" ? "(Median Expected)" : ""}
                    </td>
                    <td className="py-3 px-3 font-mono text-right text-zinc-300">₹{p.toFixed(2)}</td>
                    <td className="py-3 px-3 font-mono text-right text-zinc-300">
                      ₹{rev.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3 font-mono text-right text-rose-400/80">
                      -₹{totalCost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3 font-mono text-right text-emerald-400 font-bold">
                      ₹{nrv.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3 font-mono text-right text-emerald-400 font-bold">
                      ₹{nrvKg.toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
