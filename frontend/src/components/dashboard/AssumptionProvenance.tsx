"use client";

import React from "react";
import { EconomicAssumptionsResponse } from "@/lib/api/types";

interface AssumptionProvenanceProps {
  assumptions: EconomicAssumptionsResponse;
}

export const AssumptionProvenance: React.FC<AssumptionProvenanceProps> = ({ assumptions }) => {
  const isDemo = assumptions.assumptions.some((a) => a.is_demo);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">
            Economic Assumptions & Provenance Audit Ledger
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Transparent catalog of operational friction rates, APMC schedules, and decay parameters.
          </p>
        </div>
        {isDemo ? (
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
              DEMO BENCHMARK DATA
            </span>
            <span className="text-[11px] text-zinc-500 font-mono">
              (Non-Contractual)
            </span>
          </div>
        ) : (
          <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            VERIFIED REGULATORY DATA
          </span>
        )}
      </div>

      {isDemo && (
        <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-300 space-y-1">
          <div className="font-semibold flex items-center gap-1.5">
            <span>⚠️</span> Demonstration Mode Active:
          </div>
          <p className="text-amber-300/80 leading-relaxed">
            The friction rates, transport tariffs, and storage fees below reflect synthetic benchmark assumptions.
            In production deployments, these values must be configured against empirical APMC gazette notifications,
            local transport union rate cards, and certified warehouse receipts.
          </p>
        </div>
      )}

      {/* Assumptions Table */}
      <div className="rounded-xl border border-zinc-800 overflow-hidden">
        <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 flex justify-between items-center">
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
            Active Parameters ({assumptions.total} items)
          </div>
          <div className="text-[11px] text-zinc-500 font-mono">
            Auditable Economic Configuration
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-zinc-900/40 text-zinc-400 font-mono border-b border-zinc-800">
              <tr>
                <th className="p-3 text-left">Category</th>
                <th className="p-3 text-left">Parameter Key</th>
                <th className="p-3 text-right">Value</th>
                <th className="p-3 text-left">Unit</th>
                <th className="p-3 text-left">Provenance</th>
                <th className="p-3 text-left">Source Citation</th>
                <th className="p-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50 font-mono">
              {assumptions.assumptions.map((a) => (
                <tr key={a.id} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="p-3 font-sans font-medium text-white capitalize">
                    {a.category}
                  </td>
                  <td className="p-3 text-zinc-300 font-semibold">{a.parameter_key}</td>
                  <td className="p-3 text-right font-bold text-emerald-400">
                    {typeof a.value === "number" ? a.value.toLocaleString("en-IN") : a.value}
                  </td>
                  <td className="p-3 text-zinc-400">{a.unit}</td>
                  <td className="p-3 text-zinc-400">{a.provenance_status}</td>
                  <td className="p-3 font-sans text-zinc-400 max-w-xs truncate" title={a.source}>
                    {a.source}
                  </td>
                  <td className="p-3 text-center">
                    {a.is_demo ? (
                      <span className="px-1.5 py-0.5 text-[10px] rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        DEMO
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 text-[10px] rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        VERIFIED
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 font-mono">
        ℹ️ <span className="font-semibold text-zinc-300">Disclaimer:</span> Net Realizable Value calculations use these transparent parameters. No hidden formulas or arbitrary adjustments applied.
      </div>
    </div>
  );
};
