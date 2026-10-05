"use client";

import React, { useState, useEffect, useCallback } from "react";
import { DemandAggregate, DemandDistribution } from "@/types/buyer";
import { getDemandAggregate, getDemandDistribution } from "@/lib/api/buyers";
import { BuyerProvenance } from "./BuyerProvenance";

interface DemandAggregationPanelProps {
  commodityId: string;
}

export const DemandAggregationPanel: React.FC<DemandAggregationPanelProps> = ({
  commodityId,
}) => {
  const [regionFilter, setRegionFilter] = useState<string>("");
  const [aggregate, setAggregate] = useState<DemandAggregate | null>(null);
  const [distribution, setDistribution] = useState<DemandDistribution | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [aggData, distData] = await Promise.all([
        getDemandAggregate(commodityId, regionFilter ? regionFilter : undefined),
        getDemandDistribution(commodityId, regionFilter ? regionFilter : undefined),
      ]);
      setAggregate(aggData);
      setDistribution(distData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load regional demand data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [commodityId, regionFilter]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      getDemandAggregate(commodityId, regionFilter ? regionFilter : undefined),
      getDemandDistribution(commodityId, regionFilter ? regionFilter : undefined),
    ])
      .then(([aggData, distData]) => {
        if (!isMounted) return;
        setAggregate(aggData);
        setDistribution(distData);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : "Failed to load regional demand data";
        setError(msg);
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [commodityId, regionFilter]);

  // Format kg into quintals / metric tonnes
  const formatQuantity = (kg: number) => {
    if (kg >= 1000) {
      return `${(kg / 1000).toLocaleString("en-IN", { maximumFractionDigits: 1 })} MT (${kg.toLocaleString("en-IN")} kg)`;
    }
    return `${(kg / 100).toLocaleString("en-IN", { maximumFractionDigits: 1 })} Qtl (${kg.toLocaleString("en-IN")} kg)`;
  };

  const getHhiInterpretation = (hhi: number | null | undefined) => {
    if (hhi === null || hhi === undefined) return { label: "N/A", color: "text-zinc-500", desc: "No buyers" };
    if (hhi < 1500) {
      return {
        label: "Unconcentrated (<1500)",
        color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
        desc: "Configured benchmark band adapted from antitrust guidelines (<1500 indicates distributed purchasing volume).",
      };
    }
    if (hhi <= 2500) {
      return {
        label: "Moderate Concentration (1500–2500)",
        color: "text-amber-400 border-amber-500/30 bg-amber-500/10",
        desc: "Configured benchmark band adapted from antitrust guidelines (1500–2500 indicates moderate volume concentration).",
      };
    }
    return {
      label: "Concentrated (>2500)",
      color: "text-rose-400 border-rose-500/30 bg-rose-500/10",
      desc: "Configured benchmark band adapted from antitrust guidelines (>2500 indicates concentrated volume in fewer entities).",
    };
  };

  return (
    <div className="space-y-6">
      {/* Panel Header */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-bold tracking-tight text-white">
                Regional Demand Depth & Market Concentration
              </h2>
              {aggregate && (
                <BuyerProvenance
                  status={aggregate.provenance_status}
                  isDemo={aggregate.is_demo}
                />
              )}
            </div>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
              Factual, auditable aggregation of posted buyer requirements and active procurement orders.
              Calculates market volume depth, structural buyer concentration (HHI), and order size distributions without normative ranking.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs font-mono text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Regions (Corridor Master)</option>
              <option value="Punjab">Punjab</option>
              <option value="Haryana">Haryana</option>
              <option value="Chandigarh">Chandigarh</option>
              <option value="Delhi">Delhi NCR</option>
            </select>

            <button
              onClick={refreshData}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-xs font-mono text-zinc-200 transition-colors disabled:opacity-50"
            >
              {loading ? "Refreshing..." : "Refresh Depth"}
            </button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-center space-y-2">
          <p className="text-xs font-mono text-rose-400 uppercase tracking-wide">
            Data Retrieval Failure
          </p>
          <p className="text-sm text-zinc-300">{error}</p>
          <button
            onClick={refreshData}
            className="mt-2 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-xs font-medium text-white transition-colors"
          >
            Retry Aggregation
          </button>
        </div>
      ) : loading ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center space-y-3">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          <p className="text-xs font-mono text-zinc-400">
            Computing regional demand depth and HHI concentration...
          </p>
        </div>
      ) : aggregate ? (
        <>
          {/* Top Key Statistics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Stated Demand */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-1">
              <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
                Total Stated Demand
              </span>
              <div className="text-2xl font-bold font-mono text-white">
                {aggregate.total_demand_kg.toLocaleString("en-IN")} <span className="text-xs font-normal text-zinc-400">kg</span>
              </div>
              <p className="text-xs font-mono text-emerald-400">
                {formatQuantity(aggregate.total_demand_kg)}
              </p>
            </div>

            {/* Distinct Active Buyers */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-1">
              <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
                Active Purchasing Entities
              </span>
              <div className="text-2xl font-bold font-mono text-white">
                {aggregate.buyer_count}
              </div>
              <p className="text-xs text-zinc-400">
                Commercial buyer entities in corridor scope
              </p>
            </div>

            {/* Market Concentration (HHI) */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
                  Concentration (HHI)
                </span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                  CONFIGURED
                </span>
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                {aggregate.hhi_concentration !== null && aggregate.hhi_concentration !== undefined
                  ? aggregate.hhi_concentration.toFixed(0)
                  : "N/A"}
              </div>
              {aggregate.hhi_concentration !== null && aggregate.hhi_concentration !== undefined && (
                <div className="text-[10px] font-medium font-mono flex items-center gap-1.5 flex-wrap">
                  <span className={`px-1.5 py-0.5 rounded border ${getHhiInterpretation(aggregate.hhi_concentration).color}`}>
                    {getHhiInterpretation(aggregate.hhi_concentration).label}
                  </span>
                </div>
              )}
            </div>

            {/* Top Buyer Share */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-1">
              <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
                Top Buyer Share
              </span>
              <div className="text-2xl font-bold font-mono text-white">
                {aggregate.top_buyer_share_pct !== null && aggregate.top_buyer_share_pct !== undefined
                  ? `${aggregate.top_buyer_share_pct.toFixed(1)}%`
                  : "N/A"}
              </div>
              <p className="text-xs text-zinc-400">
                Share of total stated corridor demand
              </p>
            </div>
          </div>

          {/* Breakdown Section: Quality Grades & Buyer Categories */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Demand by Quality Requirement */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-zinc-200">
                  Demand by Quality Requirement
                </h3>
                <span className="text-[10px] font-mono text-zinc-400 uppercase">
                  Volume Breakdown
                </span>
              </div>

              {Object.keys(aggregate.breakdown_by_quality).length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-4">No quality-specific demand registered.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(aggregate.breakdown_by_quality).map(([grade, vol]) => {
                    const share = aggregate.total_demand_kg > 0
                      ? (vol / aggregate.total_demand_kg) * 100
                      : 0;
                    return (
                      <div key={grade} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono text-zinc-300 font-medium">
                            {grade.replace(/_/g, " ")}
                          </span>
                          <span className="font-mono text-zinc-400">
                            {vol.toLocaleString("en-IN")} kg ({share.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-emerald-500"
                            style={{ width: `${Math.min(100, Math.max(0, share))}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Demand by Buyer Type */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-zinc-200">
                  Demand by Buyer Category
                </h3>
                <span className="text-[10px] font-mono text-zinc-400 uppercase">
                  Channel Share
                </span>
              </div>

              {Object.keys(aggregate.breakdown_by_type).length === 0 ? (
                <p className="text-xs text-zinc-500 italic py-4">No category breakdown available.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(aggregate.breakdown_by_type).map(([type, vol]) => {
                    const share = aggregate.total_demand_kg > 0
                      ? (vol / aggregate.total_demand_kg) * 100
                      : 0;
                    return (
                      <div key={type} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono text-zinc-300 font-medium capitalize">
                            {type.replace(/_/g, " ")}
                          </span>
                          <span className="font-mono text-zinc-400">
                            {vol.toLocaleString("en-IN")} kg ({share.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-teal-500"
                            style={{ width: `${Math.min(100, Math.max(0, share))}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Order Size Distribution ($N \ge 3$ Configured Gate) */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800 pb-3">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-semibold text-zinc-200">
                    Order Size Distribution Quantiles
                  </h3>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                    CONFIGURED GATE (N ≥ 3)
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400 mt-0.5">
                  Descriptive quantile distribution of individual buyer lot requests. Minimum N ≥ 3 is a configured heuristic gate to suppress small-sample summaries.
                </p>
              </div>

              {distribution && (
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border self-start sm:self-auto ${
                    distribution.status === "VALID"
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                      : "text-amber-400 bg-amber-500/10 border-amber-500/30"
                  }`}
                >
                  {distribution.status === "VALID"
                    ? `GATE PASSED (N=${distribution.sample_size})`
                    : `GATE UNMET (N=${distribution.sample_size})`}
                </span>
              )}
            </div>

            {distribution?.status === "VALID" ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 pt-2">
                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">Min</span>
                  <div className="text-base font-bold font-mono text-zinc-200 mt-1">
                    {distribution.min_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-zinc-400">kg</span>
                  </div>
                </div>

                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">P10</span>
                  <div className="text-base font-bold font-mono text-zinc-200 mt-1">
                    {distribution.p10_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-zinc-400">kg</span>
                  </div>
                </div>

                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">P25</span>
                  <div className="text-base font-bold font-mono text-zinc-200 mt-1">
                    {distribution.p25_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-zinc-400">kg</span>
                  </div>
                </div>

                <div className="bg-emerald-950/20 p-3 rounded-lg border border-emerald-500/30">
                  <span className="text-[10px] font-mono text-emerald-400 uppercase font-semibold">Median (P50)</span>
                  <div className="text-base font-bold font-mono text-emerald-300 mt-1">
                    {distribution.median_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-emerald-400/80">kg</span>
                  </div>
                </div>

                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">P75</span>
                  <div className="text-base font-bold font-mono text-zinc-200 mt-1">
                    {distribution.p75_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-zinc-400">kg</span>
                  </div>
                </div>

                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">P90</span>
                  <div className="text-base font-bold font-mono text-zinc-200 mt-1">
                    {distribution.p90_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-zinc-400">kg</span>
                  </div>
                </div>

                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">Max</span>
                  <div className="text-base font-bold font-mono text-zinc-200 mt-1">
                    {distribution.max_kg?.toLocaleString("en-IN") ?? "—"} <span className="text-[10px] font-normal text-zinc-400">kg</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-xs font-mono text-amber-300">
                Distribution metrics fail closed: sample size (N={distribution?.sample_size ?? 0}) does not meet configured minimum sample-size gate (N ≥ 3).
                Quantiles are suppressed to prevent displaying misleading small-sample summaries (CONFIGURED heuristic).
              </div>
            )}
          </div>

          {/* Mathematical & Methodology Card */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 space-y-3 font-mono text-xs">
            <span className="text-zinc-400 uppercase tracking-wider font-semibold">
              Mathematical Provenance & Gating Protocol
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-zinc-400 font-sans text-xs">
              <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/80 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-emerald-400 font-semibold text-[11px]">
                    Herfindahl-Hirschman Index (HHI)
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                    CONFIGURED CONVENTION
                  </span>
                </div>
                <p className="text-[11px] leading-relaxed text-zinc-400">
                  Calculated as HHI = 10,000 × Σ (q_i / Q)², quantifying volume concentration across purchasing entities.
                  Interpretive bands (&lt;1,500 unconcentrated; 1,500–2,500 moderate; &gt;2,500 concentrated) are a CONFIGURED convention adapted from DOJ/FTC Horizontal Merger Guidelines, not an empirical agricultural standard.
                </p>
              </div>

              <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/80 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-teal-400 font-semibold text-[11px]">
                    Descriptive Aggregation & Gating
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                    CONFIGURED (N ≥ 3)
                  </span>
                </div>
                <p className="text-[11px] leading-relaxed text-zinc-400">
                  Regional demand depth is reported as factual arithmetic totals with zero normative ranking or selling advice.
                  Order size quantiles require minimum N ≥ 3 observations as a conservative heuristic gate to suppress 1- or 2-order summaries.
                </p>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
