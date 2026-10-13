"use client";

import React, { useState } from "react";
import { WhatIfSimulationResult } from "@/types/decision";
import { fetchWhatIfSimulation } from "@/lib/api/decision";

interface WhatIfSimulatorProps {
  commodityId: string;
}

export function WhatIfSimulator({ commodityId }: WhatIfSimulatorProps) {
  const [totalSupplyKg, setTotalSupplyKg] = useState<number>(3000);
  const [transportCostMultiplier, setTransportCostMultiplier] = useState<number>(1.25);
  const [buyerDemandMultiplier, setBuyerDemandMultiplier] = useState<number>(0.8);
  const [priceShockMultiplier, setPriceShockMultiplier] = useState<number>(1.0);
  const [simulation, setSimulation] = useState<WhatIfSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchWhatIfSimulation({
        commodity_id: commodityId,
        total_supply_kg: totalSupplyKg,
        transport_cost_multiplier: transportCostMultiplier,
        buyer_demand_multiplier: buyerDemandMultiplier,
        price_shock_multiplier: priceShockMultiplier,
      });
      setSimulation(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to run simulation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Parameter Control Panel */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-zinc-800/80">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl">🧪</span>
              <h2 className="text-lg font-bold text-zinc-100">
                Counterfactual What-If Sensitivity Lab
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                Comparative Perturbation Re-solve
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Simulate external supply shocks, fuel freight increases, and buyer demand contractions against the baseline plan.
            </p>
          </div>

          <button
            onClick={runSimulation}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-zinc-950 text-xs font-bold font-mono transition-all disabled:opacity-50"
          >
            {loading ? "Re-solving..." : "Run What-If Simulation"}
          </button>
        </div>

        {/* Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">Transport Cost Multiplier</span>
              <span className="font-mono text-cyan-400 font-semibold">
                {transportCostMultiplier.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min={0.5}
              max={2.0}
              step={0.05}
              value={transportCostMultiplier}
              onChange={(e) => setTransportCostMultiplier(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">Buyer Demand Multiplier</span>
              <span className="font-mono text-amber-400 font-semibold">
                {buyerDemandMultiplier.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min={0.2}
              max={2.0}
              step={0.1}
              value={buyerDemandMultiplier}
              onChange={(e) => setBuyerDemandMultiplier(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">Price Shock Multiplier</span>
              <span className="font-mono text-emerald-400 font-semibold">
                {priceShockMultiplier.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min={0.5}
              max={1.5}
              step={0.05}
              value={priceShockMultiplier}
              onChange={(e) => setPriceShockMultiplier(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-950/20 p-6 text-xs text-red-400 font-mono">
          [SIMULATION_ERROR]: {error}
        </div>
      )}

      {/* Comparison Presentation */}
      {simulation && (
        <div className="space-y-6">
          {/* Comparison Delta Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
              <div className="text-[11px] text-zinc-400">Net Realization Delta</div>
              <div
                className={`text-xl font-bold font-mono ${
                  simulation.comparison.nrv_delta >= 0
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}
              >
                {simulation.comparison.nrv_delta >= 0 ? "+" : ""}
                INR {Math.round(simulation.comparison.nrv_delta).toLocaleString()} (
                {simulation.comparison.nrv_percentage_change.toFixed(1)}%)
              </div>
              <div className="text-[10px] text-zinc-400 mt-1">
                From INR {Math.round(simulation.baseline_plan.expected_total_nrv).toLocaleString()} to INR {Math.round(simulation.counterfactual_plan.expected_total_nrv).toLocaleString()}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
              <div className="text-[11px] text-zinc-400">Reallocated Produce</div>
              <div className="text-xl font-bold font-mono text-cyan-400">
                {Math.round(simulation.comparison.allocation_delta_kg ?? simulation.comparison.reallocated_quantity_kg ?? 0).toLocaleString()} kg
              </div>
              <div className="text-[10px] text-zinc-400 mt-1">
                Volume shifted between market channels
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800">
              <div className="text-[11px] text-zinc-400">Downside CVaR Shift</div>
              <div
                className={`text-xl font-bold font-mono ${
                  (simulation.comparison.cvar_delta ?? 0) <= 0
                    ? "text-emerald-400"
                    : "text-amber-400"
                }`}
              >
                {(simulation.comparison.cvar_delta ?? 0) >= 0 ? "+" : ""}
                INR {Math.round(simulation.comparison.cvar_delta ?? 0).toLocaleString()}
              </div>
              <div className="text-[10px] text-zinc-400 mt-1">
                Change in expected tail shortfall
              </div>
            </div>
          </div>

          {/* Reproducibility & Solver Verification Audit Bar */}
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-4 text-xs font-mono space-y-2">
            <div className="text-[11px] text-zinc-400 uppercase font-semibold">
              Independent Solver Run & Hash Verification
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px]">
              <div className="p-2.5 rounded-lg bg-zinc-800/40 border border-zinc-700/40 space-y-1">
                <div className="text-zinc-400">Baseline Solver: <span className="text-emerald-400 font-bold">{simulation.comparison.baseline_solver_status || simulation.baseline_plan.solver_status}</span></div>
                <div className="text-[10px] text-zinc-400 truncate">Hash: {simulation.comparison.baseline_input_hash || simulation.baseline_plan.configuration_hash}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-zinc-800/40 border border-zinc-700/40 space-y-1">
                <div className="text-zinc-400">Counterfactual Solver: <span className="text-cyan-400 font-bold">{simulation.comparison.new_solver_status || simulation.counterfactual_plan.solver_status}</span></div>
                <div className="text-[10px] text-zinc-400 truncate">Hash: {simulation.comparison.counterfactual_input_hash || simulation.counterfactual_plan.configuration_hash}</div>
              </div>
            </div>
          </div>

          {/* Notes and Interpretation */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
            <h3 className="text-sm font-bold text-zinc-200">
              Economic Impact Interpretation
            </h3>
            <ul className="space-y-2 text-xs text-zinc-300">
              {(simulation.comparison.interpretation_notes || [
                simulation.comparison.allocation_shift_summary || "Volume reallocated across viable channels.",
              ]).map((note, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="text-cyan-400 font-bold">•</span>
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
