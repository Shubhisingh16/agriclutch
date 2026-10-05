"use client";

import React, { useState } from "react";
import { LogisticsScenario } from "@/types/logistics";
import { AssumptionBadge } from "./AssumptionBadge";

interface ScenarioCardProps {
  scenario: LogisticsScenario;
}

export const ScenarioCard: React.FC<ScenarioCardProps> = ({ scenario }) => {
  const [showCostDetails, setShowCostDetails] = useState<boolean>(false);

  const feas = scenario.feasibility;
  const isFeasible = feas.status === "FEASIBLE";
  const isPartial = feas.status === "PARTIALLY_FEASIBLE";

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4 hover:border-zinc-700/80 transition-all">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-base font-extrabold text-white">{scenario.scenario_name}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
              {scenario.scenario_id}
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Destination: <span className="text-zinc-200 font-medium">{scenario.destination.name}</span> ({scenario.destination.location})
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Feasibility Status */}
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono border ${
              isFeasible
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : isPartial
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                : "bg-red-500/10 text-red-400 border-red-500/30"
            }`}
          >
            {feas.status}
          </span>
          <AssumptionBadge status={scenario.economic_status} isDemo={scenario.provenance.is_demo} />
        </div>
      </div>

      {/* Demo Scenario Disclosure Banner */}
      {scenario.provenance.is_demo && (
        <div className="px-3 py-1.5 rounded bg-amber-500/10 border border-amber-500/25 flex items-center justify-between text-[11px] font-mono text-amber-300">
          <span className="flex items-center space-x-1.5">
            <span>ℹ️</span>
            <span>DEMO SCENARIO — NOT LIVE ROUTING DATA — NOT EMPIRICAL TRANSACTION DATA</span>
          </span>
          <span className="text-[10px] text-amber-400/80">Synthetic Corridor</span>
        </div>
      )}

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[10px] font-mono text-zinc-400">DISTANCE & DURATION</div>
          <div className="text-base font-bold text-white font-mono mt-0.5">
            {scenario.distance_km != null ? `${scenario.distance_km} km` : "N/A"}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">
            {scenario.total_elapsed_hours.toFixed(1)} hrs total
          </div>
        </div>

        <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[10px] font-mono text-zinc-400">STORAGE HOLDING</div>
          <div className="text-base font-bold text-cyan-400 font-mono mt-0.5">
            {scenario.storage_duration_days} days
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">
            {scenario.storage_facility ? scenario.storage_facility.storage_type : "Direct Transit"}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[10px] font-mono text-zinc-400">DELIVERED VOLUME</div>
          <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
            {scenario.effective_delivered_quantity_kg.toFixed(0)} kg
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">
            of {scenario.initial_quantity_kg.toFixed(0)} kg initial
          </div>
        </div>

        <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[10px] font-mono text-zinc-400">TOTAL PATHWAY COST</div>
          <div className="text-base font-bold text-amber-300 font-mono mt-0.5">
            ₹{scenario.total_pathway_cost.toFixed(2)}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">
            (₹{(scenario.total_pathway_cost / scenario.initial_quantity_kg).toFixed(2)}/kg)
          </div>
        </div>
      </div>

      {/* Warnings & Constraints if present */}
      {(feas.warnings.length > 0 || feas.failed_constraints.length > 0) && (
        <div className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-1 text-xs">
          {feas.failed_constraints.map((fc, i) => (
            <div key={i} className="text-red-400 flex items-center space-x-1.5">
              <span>⚠️</span>
              <span>{fc}</span>
            </div>
          ))}
          {feas.warnings.map((w, i) => (
            <div key={i} className="text-amber-400 flex items-center space-x-1.5">
              <span>ℹ️</span>
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Cost Decomposition Accordion */}
      <div className="pt-2 border-t border-zinc-800/60">
        <button
          onClick={() => setShowCostDetails(!showCostDetails)}
          className="text-xs font-mono text-zinc-400 hover:text-zinc-200 flex items-center space-x-1 transition-colors"
        >
          <span>{showCostDetails ? "▼ Hide" : "▶ View"} Itemized Cost & Handling Breakdown</span>
        </button>

        {showCostDetails && (
          <div className="mt-3 p-3 rounded-lg bg-zinc-950 border border-zinc-800 space-y-2 text-xs font-mono">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-zinc-300 border-b border-zinc-800/60 pb-2">
              <div>
                Transport: <span className="text-white font-bold">₹{scenario.logistics_cost.transport_cost.toFixed(2)}</span>
              </div>
              <div>
                Loading: <span className="text-white font-bold">₹{scenario.logistics_cost.loading_cost.toFixed(2)}</span>
              </div>
              <div>
                Unloading: <span className="text-white font-bold">₹{scenario.logistics_cost.unloading_cost.toFixed(2)}</span>
              </div>
              <div>
                Storage Holding: <span className="text-white font-bold">₹{scenario.storage_cost.toFixed(2)}</span>
              </div>
            </div>

            {/* Line items */}
            <div className="space-y-1 pt-1 text-[11px] text-zinc-400">
              {scenario.logistics_cost.items.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center py-0.5">
                  <span>{item.component_name} ({item.unit_basis})</span>
                  <span className="text-zinc-200 font-bold">₹{item.amount.toFixed(2)}</span>
                </div>
              ))}
            </div>

            <div className="text-[10px] text-zinc-400 pt-2 border-t border-zinc-800/40">
              Audit Lineage: {scenario.provenance.justification}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
