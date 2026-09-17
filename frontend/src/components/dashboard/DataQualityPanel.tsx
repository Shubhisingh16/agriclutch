"use client";

import React from "react";
import { PriceObservation } from "@/lib/api/types";

interface DataQualityPanelProps {
  observation: PriceObservation | null;
  dataSourceHeader?: string | null;
  dataMode?: "DEMO" | "DATABASE" | null;
}

export const DataQualityPanel: React.FC<DataQualityPanelProps> = ({
  observation,
  dataSourceHeader,
  dataMode,
}) => {
  if (!observation) {
    return null;
  }

  const isSynthetic =
    dataMode === "DEMO" ||
    dataSourceHeader === "SYNTHETIC_TEST_FIXTURE" ||
    dataSourceHeader === "DEMO_BENCHMARK_SEED" ||
    observation.source_name.toUpperCase().includes("SYNTHETIC") ||
    observation.source_name.toUpperCase().includes("DEMO");

  return (
    <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/60 pb-3">
        <div className="flex items-center space-x-2">
          <span className="text-base">🛡️</span>
          <div>
            <h4 className="text-sm font-bold text-white tracking-tight">
              Data Quality & Audit Provenance
            </h4>
            <p className="text-[11px] text-zinc-400">
              Verifiable data lineage and conversion audit trail
            </p>
          </div>
        </div>

        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
            isSynthetic
              ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
              : "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
          }`}
        >
          {isSynthetic ? "Synthetic Test Fixture" : "Historical APMC Record"}
        </span>
      </div>

      {/* Grid of Audit Items */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
        <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
          <div className="text-[10px] text-zinc-500 uppercase">Origin Source</div>
          <div className="font-semibold text-zinc-200 mt-1 truncate">
            {observation.source_name}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
          <div className="text-[10px] text-zinc-500 uppercase">Record UID</div>
          <div className="font-semibold text-zinc-200 mt-1 truncate">
            {observation.source_record_id || "Direct"}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
          <div className="text-[10px] text-zinc-500 uppercase">Unit Scaling</div>
          <div className="font-semibold text-emerald-400 mt-1">
            {observation.original_price_unit} → {observation.normalized_price_unit}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
          <div className="text-[10px] text-zinc-500 uppercase">Interpolation</div>
          <div className="font-semibold text-zinc-300 mt-1">
            {observation.is_interpolated ? (
              <span className="text-amber-400">Imputed Gap</span>
            ) : (
              <span className="text-zinc-400">Raw Observed</span>
            )}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
          <div className="text-[10px] text-zinc-500 uppercase">Anomaly Check</div>
          <div className="font-semibold text-zinc-300 mt-1">
            {observation.is_outlier ? (
              <span className="text-rose-400">MAD Spike Flagged</span>
            ) : (
              <span className="text-emerald-400">Within Bounds ✓</span>
            )}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60">
          <div className="text-[10px] text-zinc-500 uppercase">Audit Key</div>
          <div className="font-semibold text-zinc-400 mt-1 text-[10px] truncate" title={observation.observation_id}>
            {observation.observation_id ? observation.observation_id.slice(0, 8) + "..." : "Auto-UUID"}
          </div>
        </div>
      </div>
    </div>
  );
};
