"use client";

import React, { useState, useEffect } from "react";
import {
  evaluatePathways,
  getTransportModes,
} from "@/lib/api/logistics";
import {
  EvaluatePathwaysResponse,
  TransportMode,
} from "@/types/logistics";
import { AssumptionBadge } from "./AssumptionBadge";
import { DistanceCard } from "./DistanceCard";
import { ScenarioCard } from "./ScenarioCard";

interface LogisticsPanelProps {
  selectedCommodityId: string;
}

export const LogisticsPanel: React.FC<LogisticsPanelProps> = ({
  selectedCommodityId,
}) => {
  const [quantityKg, setQuantityKg] = useState<number>(2500);
  const [originLocation, setOriginLocation] = useState<string>("Kalka Farm Gate");
  const [transportModes, setTransportModes] = useState<TransportMode[]>([]);
  const [selectedModeId, setSelectedModeId] = useState<string>("DEMO_LCV_TATA_407");
  const [storageDays, setStorageDays] = useState<number>(7);

  const [loading, setLoading] = useState<boolean>(true);
  const [evaluation, setEvaluation] = useState<EvaluatePathwaysResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load modes and run default evaluation
  useEffect(() => {
    let isMounted = true;
    (async () => {
      setLoading(true);
      try {
        const modes = await getTransportModes();
        if (!isMounted) return;
        setTransportModes(modes);

        const evalRes = await evaluatePathways({
          commodity_id: selectedCommodityId,
          quantity_kg: quantityKg,
          origin_location: originLocation,
          available_from: "2026-09-15",
          available_until: "2026-09-25",
          transport_mode_id: selectedModeId,
          storage_duration_days: storageDays,
        });
        if (!isMounted) return;
        setEvaluation(evalRes);
      } catch (err: unknown) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to evaluate logistics pathways.");
      } finally {
        if (isMounted) setLoading(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [selectedCommodityId, quantityKg, originLocation, selectedModeId, storageDays]);

  const handleReevaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const evalRes = await evaluatePathways({
        commodity_id: selectedCommodityId,
        quantity_kg: quantityKg,
        origin_location: originLocation,
        available_from: "2026-09-15",
        available_until: "2026-09-25",
        transport_mode_id: selectedModeId,
        storage_duration_days: storageDays,
      });
      setEvaluation(evalRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Pathway evaluation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Step 13 Governance Banner */}
      <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-lg">
            🚛
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white">Logistics & Physical Pathway Feasibility Engine</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                STEP 13
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Evaluates physical distance, transit duration, capacity constraints, and friction costs across multi-stage routes.
            </p>
          </div>
        </div>
        <AssumptionBadge status="DEMO_ASSUMPTION" isDemo={true} />
      </div>

      {/* Lot Parameters & Vehicle Selector */}
      <div className="p-5 rounded-xl bg-zinc-900/50 border border-zinc-800 space-y-4">
        <div className="text-xs font-mono font-semibold text-zinc-300">
          PRODUCE LOT SPECIFICATION & VEHICLE DISPATCH
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="text-[10px] font-mono text-zinc-400">Target Crop</label>
            <input
              type="text"
              disabled
              value={selectedCommodityId.toUpperCase()}
              className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-zinc-200 font-mono font-bold"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-zinc-400">Produce Volume (kg)</label>
            <input
              type="number"
              value={quantityKg}
              onChange={(e) => setQuantityKg(parseFloat(e.target.value) || 100)}
              className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-zinc-100 font-mono"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-zinc-400">Origin Location</label>
            <input
              type="text"
              value={originLocation}
              onChange={(e) => setOriginLocation(e.target.value)}
              className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-zinc-100"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-zinc-400">Vehicle Archetype</label>
            <select
              value={selectedModeId}
              onChange={(e) => setSelectedModeId(e.target.value)}
              className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-zinc-100 text-xs"
            >
              {transportModes.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name} ({m.capacity_kg} kg cap)
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-1">
          <button
            onClick={handleReevaluate}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors shadow-sm disabled:opacity-50"
          >
            {loading ? "Evaluating Pathways..." : "Evaluate Multi-Stage Pathways"}
          </button>
        </div>
      </div>

      {error && <div className="text-xs text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</div>}

      {/* Geodesic Distance Tool */}
      <DistanceCard />

      {/* Evaluated Pathways List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-mono font-semibold text-zinc-300">
            DESCRIPTIVE MULTI-STAGE PATHWAY SCENARIOS (FACTUAL COMPARISON)
          </div>
          <span className="text-[10px] text-zinc-400 font-mono">
            Zero Decision Optimization — Factual Physical Profiles Only
          </span>
        </div>

        {/* Demo Disclosure Banner */}
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/25 flex items-start space-x-2 text-xs text-amber-300">
          <span className="text-sm">⚠️</span>
          <div>
            <span className="font-bold">DEMO SCENARIOS:</span> The pathways below use benchmark demo coordinates, speed assumptions, and synthetic facility fixtures. They are not live routing data or empirical transaction records.
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-zinc-400 animate-pulse">
            Simulating physical transport legs, handling stages, and shelf-life decay...
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {evaluation?.scenarios.map((scen) => (
              <ScenarioCard key={scen.scenario_id} scenario={scen} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
