"use client";

import React, { useState, useEffect } from "react";
import {
  OptimalSellingPlan,
  RiskPreference,
  LiquidityPreference,
} from "@/types/decision";
import { fetchOptimalPlan } from "@/lib/api/decision";

interface DecisionDashboardProps {
  commodityId: string;
}

export function DecisionDashboard({ commodityId }: DecisionDashboardProps) {
  const [totalSupplyKg, setTotalSupplyKg] = useState<number>(3000);
  const [riskPref, setRiskPref] = useState<RiskPreference>("RISK_AWARE");
  const [liquidityPref, setLiquidityPref] = useState<LiquidityPreference>("BALANCED");
  const [plan, setPlan] = useState<OptimalSellingPlan | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const executeOptimization = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchOptimalPlan({
          commodity_id: commodityId,
          total_supply_kg: totalSupplyKg,
          risk_preference: riskPref,
          liquidity_preference: liquidityPref,
          decision_horizon_days: 7,
        });
        if (!isMounted) return;
        setPlan(data);
      } catch (err: unknown) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to compute optimal plan");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    executeOptimization();

    return () => {
      isMounted = false;
    };
  }, [commodityId, riskPref, liquidityPref, totalSupplyKg]);

  return (
    <div className="space-y-6">
      {/* Header & Controls Card */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-zinc-800/80">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl">🎯</span>
              <h2 className="text-lg font-bold text-zinc-100">
                Integrated Optimal Selling Plan
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                HiGHS Dual Simplex LP
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Deterministic, constraint-validated multi-destination selling allocation fusing price forecasts, buyers, freight, storage, and perishability.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono px-2 py-1 rounded bg-zinc-800 text-zinc-400">
              Provenance: {plan?.provenance_status || "DEMO"}
            </span>
            <span className="text-[10px] font-mono px-2 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
              Demo Fixtures Active
            </span>
          </div>
        </div>

        {/* Farmer Configuration Sliders & Dropdowns */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400 font-medium">Available Produce (kg)</span>
              <span className="font-mono text-emerald-400 font-semibold">
                {totalSupplyKg.toLocaleString()} kg
              </span>
            </div>
            <input
              type="range"
              min={500}
              max={15000}
              step={250}
              value={totalSupplyKg}
              onChange={(e) => setTotalSupplyKg(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs text-zinc-400 font-medium block">
              Risk Preference (Downside CVaR Penalty)
            </label>
            <div className="grid grid-cols-3 gap-1.5">
              {(["RISK_NEUTRAL", "RISK_AWARE", "RISK_AVERSE"] as RiskPreference[]).map(
                (pref) => (
                  <button
                    key={pref}
                    type="button"
                    onClick={() => setRiskPref(pref)}
                    className={`py-1.5 text-[10px] font-mono rounded-lg transition-all ${
                      riskPref === pref
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-bold"
                        : "bg-zinc-800/80 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    {pref.replace("RISK_", "")}
                  </button>
                )
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs text-zinc-400 font-medium block">
              Liquidity Preference (Cash Timing)
            </label>
            <div className="grid grid-cols-3 gap-1.5">
              {(["IMMEDIATE", "BALANCED", "DELAY_TOLERANT"] as LiquidityPreference[]).map(
                (pref) => (
                  <button
                    key={pref}
                    type="button"
                    onClick={() => setLiquidityPref(pref)}
                    className={`py-1.5 text-[10px] font-mono rounded-lg transition-all ${
                      liquidityPref === pref
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-bold"
                        : "bg-zinc-800/80 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    {pref === "DELAY_TOLERANT" ? "DELAY" : pref}
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-xs text-zinc-400 font-mono animate-pulse">
          Solving multi-channel HiGHS simplex linear program...
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-950/20 p-6 text-xs text-red-400 font-mono">
          [OPTIMIZER_ERROR]: {error}
        </div>
      )}

      {/* Main Solution Presentation */}
      {!loading && !error && plan && (
        <div className="space-y-6">
          {/* Executive Summary & Key Realization Metrics */}
          <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 to-zinc-900/60 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono tracking-wider uppercase text-emerald-400 font-semibold">
                RECOMMENDED ACTION PLAN
              </span>
              <span className="text-xs font-mono text-zinc-400">
                Solved in {plan.solver_duration_ms.toFixed(1)} ms
              </span>
            </div>

            <div className="text-base font-semibold text-zinc-100">
              {plan.executive_summary}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-zinc-800/60">
              <div className="p-3 bg-zinc-900/80 rounded-xl border border-zinc-800/80">
                <div className="text-[11px] text-zinc-400">Expected Total NRV</div>
                <div className="text-lg font-bold font-mono text-emerald-400">
                  INR {Math.round(plan.expected_total_nrv).toLocaleString()}
                </div>
                <div className="text-[10px] text-zinc-400 mt-0.5">
                  Avg INR {plan.average_effective_nrv_per_kg.toFixed(2)}/kg
                </div>
              </div>

              <div className="p-3 bg-zinc-900/80 rounded-xl border border-zinc-800/80">
                <div className="text-[11px] text-zinc-400">Delivered Produce</div>
                <div className="text-lg font-bold font-mono text-zinc-100">
                  {Math.round(plan.total_delivered_kg).toLocaleString()} kg
                </div>
                <div className="text-[10px] text-zinc-400 mt-0.5">
                  of {plan.total_allocated_kg.toLocaleString()} kg allocated
                </div>
              </div>

              <div className="p-3 bg-zinc-900/80 rounded-xl border border-zinc-800/80">
                <div className="text-[11px] text-zinc-400">Downside Spread (P50-P10)</div>
                <div className="text-lg font-bold font-mono text-amber-400">
                  INR {Math.round(plan.risk_metrics.portfolio_downside_spread ?? plan.risk_metrics.var_95).toLocaleString()}
                </div>
                <div className="text-[10px] text-zinc-400 mt-0.5">
                  Tail Stress (1.25x): INR {Math.round(plan.risk_metrics.configured_tail_stress_estimate ?? plan.risk_metrics.cvar_95).toLocaleString()}
                </div>
              </div>

              <div className="p-3 bg-zinc-900/80 rounded-xl border border-zinc-800/80">
                <div className="text-[11px] text-zinc-400">Total Logistics Friction</div>
                <div className="text-lg font-bold font-mono text-zinc-300">
                  INR {Math.round(plan.total_friction_cost).toLocaleString()}
                </div>
                <div className="text-[10px] text-zinc-400 mt-0.5">
                  Freight + Storage + Fee
                </div>
              </div>
            </div>
          </div>

          {/* Allocation Split Breakdown Table */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-4">
            <h3 className="text-sm font-bold text-zinc-200">
              Channel Split Allocation Breakdown
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono text-left">
                <thead className="bg-zinc-800/60 text-zinc-400 border-b border-zinc-700/60">
                  <tr>
                    <th className="p-3">Destination / Channel</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Allocated Qty</th>
                    <th className="p-3">Delivered Qty</th>
                    <th className="p-3">Gross Price</th>
                    <th className="p-3">Friction</th>
                    <th className="p-3">Effective NRV</th>
                    <th className="p-3">Total NRV</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60">
                  {plan.allocations.map((alloc) => (
                    <tr key={alloc.candidate_id} className="hover:bg-zinc-800/30">
                      <td className="p-3 font-sans font-medium text-zinc-200">
                        {alloc.destination_name}
                        {alloc.buyer_name && (
                          <div className="text-[10px] font-mono text-zinc-400">
                            {alloc.buyer_name}
                          </div>
                        )}
                        {alloc.storage_facility_name && (
                          <div className="text-[10px] font-mono text-cyan-400">
                            Hold {alloc.storage_duration_days}d @ {alloc.storage_facility_name}
                          </div>
                        )}
                      </td>
                      <td className="p-3 text-zinc-400">{alloc.destination_type}</td>
                      <td className="p-3 font-semibold text-emerald-400">
                        {Math.round(alloc.allocated_quantity_kg).toLocaleString()} kg ({alloc.allocation_percentage.toFixed(0)}%)
                      </td>
                      <td className="p-3 text-zinc-300">
                        {Math.round(alloc.delivered_quantity_kg).toLocaleString()} kg
                      </td>
                      <td className="p-3 text-zinc-300">
                        INR {alloc.expected_gross_price_per_kg.toFixed(2)}/kg
                      </td>
                      <td className="p-3 text-zinc-400">
                        INR {Math.round(alloc.total_friction_cost).toLocaleString()}
                      </td>
                      <td className="p-3 text-emerald-300 font-semibold">
                        INR {alloc.effective_nrv_per_kg.toFixed(2)}/kg
                      </td>
                      <td className="p-3 font-bold text-emerald-400">
                        INR {Math.round(alloc.expected_net_realizable_value).toLocaleString()}
                      </td>
                      <td className="p-3">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">
                          {alloc.execution_day === 0 ? "Immediate" : `Day +${alloc.execution_day}`}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Structured Explanations & Constraint Audit */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
              <h3 className="text-sm font-bold text-zinc-200">
                Optimization Decision Rationale
              </h3>
              <ul className="space-y-2 text-xs text-zinc-300">
                {plan.structured_explanations.map((exp, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{exp}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
              <h3 className="text-sm font-bold text-zinc-200">
                Constraint System Audit
              </h3>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between p-2 rounded bg-zinc-800/40">
                  <span className="text-zinc-400">Total Constraints Checked:</span>
                  <span className="text-zinc-200 font-bold">
                    {plan.constraint_summary.total_constraints_checked}
                  </span>
                </div>
                <div className="flex justify-between p-2 rounded bg-zinc-800/40">
                  <span className="text-zinc-400">Binding Constraints:</span>
                  <span className="text-amber-400 font-semibold">
                    {plan.constraint_summary.binding_constraints.length}
                  </span>
                </div>
                <div className="flex justify-between p-2 rounded bg-zinc-800/40">
                  <span className="text-zinc-400">Violations:</span>
                  <span className="text-emerald-400 font-bold">
                    {plan.constraint_summary.violated_constraints.length === 0
                      ? "0 (All Satisfied)"
                      : plan.constraint_summary.violated_constraints.length}
                  </span>
                </div>
                <div className="text-[11px] text-zinc-400 pt-1">
                  Binding limits: {plan.constraint_summary.binding_constraints.join(", ") || "None"}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
