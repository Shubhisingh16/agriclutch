"use client";

import React from "react";

interface FreshnessBadgeProps {
  observationDate: string | null;
  retrievedAt: string | null;
  sourceName?: string | null;
  dataSourceHeader?: string | null;
  dataMode?: "DEMO" | "DATABASE" | null;
  className?: string;
}

export const FreshnessBadge: React.FC<FreshnessBadgeProps> = ({
  observationDate,
  retrievedAt,
  sourceName,
  dataSourceHeader,
  dataMode,
  className = "",
}) => {
  const isDemo =
    dataMode === "DEMO" ||
    dataSourceHeader === "SYNTHETIC_TEST_FIXTURE" ||
    dataSourceHeader === "DEMO_BENCHMARK_SEED" ||
    sourceName?.toUpperCase().includes("SYNTHETIC") ||
    sourceName?.toUpperCase().includes("DEMO");

  const formattedObservationDate = observationDate
    ? new Date(observationDate).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "No records";

  const formattedRetrievalTime = retrievedAt
    ? new Date(retrievedAt).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : null;

  return (
    <div
      className={`inline-flex flex-wrap items-center gap-2 p-2 rounded-xl bg-zinc-900/60 border border-zinc-800/80 text-xs font-mono ${className}`}
    >
      {/* Historical Trading Session Label */}
      <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-300">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
        <span className="text-[11px]">
          {isDemo ? "Demo Trading Date: " : "Session: "}
          <strong className="text-white">{formattedObservationDate}</strong>
        </span>
      </div>

      {/* Provenance Indicator */}
      {sourceName && (
        <div className="px-2 py-0.5 rounded bg-zinc-800/60 text-zinc-400 text-[11px]">
          Source: <span className="text-zinc-200">{sourceName}</span>
        </div>
      )}

      {/* Demo vs Database Disclosure */}
      {isDemo ? (
        <div className="flex items-center space-x-1 px-2.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px] font-semibold">
          <span>⚠️</span>
          <span>DEMO DATA — Synthetic test fixture</span>
        </div>
      ) : (
        <div className="flex items-center space-x-1 px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-semibold">
          <span>🏛️</span>
          <span>Historical APMC Mandi Records</span>
        </div>
      )}

      {/* Retrieval Timestamp Distinction: Demo Fixture vs DB Sync */}
      {formattedRetrievalTime && (
        <div className="text-[10px] text-zinc-500 pl-1">
          {isDemo ? `Fixture Loaded: ${formattedRetrievalTime}` : `DB Synced: ${formattedRetrievalTime}`}
        </div>
      )}
    </div>
  );
};
