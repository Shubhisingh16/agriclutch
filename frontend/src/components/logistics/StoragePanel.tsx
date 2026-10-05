"use client";

import React, { useState, useEffect } from "react";
import {
  evaluateStorageFeasibility,
  getStorageFacilities,
} from "@/lib/api/logistics";
import {
  StorageFacility,
  StorageFeasibility,
} from "@/types/logistics";
import { AssumptionBadge } from "./AssumptionBadge";
import { PerishabilityChart } from "./PerishabilityChart";

interface StoragePanelProps {
  selectedCommodityId: string;
}

export const StoragePanel: React.FC<StoragePanelProps> = ({
  selectedCommodityId,
}) => {
  const [facilities, setFacilities] = useState<StorageFacility[]>([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState<string>("DEMO_COLD_STORAGE_NORTH");
  const [storageQtyKg, setStorageQtyKg] = useState<number>(2500);
  const [durationDays, setDurationDays] = useState<number>(14);

  const [loading, setLoading] = useState<boolean>(true);
  const [feasibility, setFeasibility] = useState<StorageFeasibility | null>(null);
  const [feasLoading, setFeasLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load facilities
  useEffect(() => {
    let isMounted = true;
    (async () => {
      setLoading(true);
      try {
        const facs = await getStorageFacilities();
        if (!isMounted) return;
        setFacilities(facs);
        if (facs.length > 0) {
          const defaultFac = facs.find((f) => f.id === "DEMO_COLD_STORAGE_NORTH") || facs[0];
          setSelectedFacilityId(defaultFac.id);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load storage facilities.");
      } finally {
        if (isMounted) setLoading(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, []);

  // Evaluate feasibility whenever facility, qty, or duration changes
  useEffect(() => {
    let isMounted = true;
    (async () => {
      if (!selectedFacilityId) return;
      setFeasLoading(true);
      try {
        const res = await evaluateStorageFeasibility({
          facility_id: selectedFacilityId,
          requested_quantity_kg: storageQtyKg,
          requested_duration_days: durationDays,
        });
        if (!isMounted) return;
        setFeasibility(res);
      } catch {
        // Handled silently
      } finally {
        if (isMounted) setFeasLoading(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [selectedFacilityId, storageQtyKg, durationDays]);

  const activeFac = facilities.find((f) => f.id === selectedFacilityId);

  return (
    <div className="space-y-6">
      {/* Step 13 Governance Banner */}
      <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-lg">
            ❄️
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white">Storage Capacity & Shelf-Life Deterioration Engine</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                STEP 13
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Evaluates facility volume allocations, duration constraints, and exponential crop decay trajectories.
            </p>
          </div>
        </div>
        <AssumptionBadge status="DEMO_ASSUMPTION" isDemo={true} />
      </div>

      {/* Facility Directory & Capacity Explorer */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-mono font-semibold text-zinc-300">
            SYNTHETIC DEMO STORAGE FACILITIES (NON-REAL ARCHETYPES)
          </div>
          <span className="text-[10px] text-zinc-400 font-mono">
            Purely Synthetic Demo Entities — Not Certified Real Facilities
          </span>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-zinc-400 animate-pulse">
            Loading storage network fixtures...
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {facilities.map((fac) => {
              const isSelected = fac.id === selectedFacilityId;
              const isCold = fac.storage_type === "COLD";
              return (
                <div
                  key={fac.id}
                  onClick={() => setSelectedFacilityId(fac.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-zinc-900 border-cyan-500/50 shadow-md shadow-cyan-500/10"
                      : "bg-zinc-950/60 border-zinc-800 hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-lg">{isCold ? "❄️" : "🌾"}</span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                        isCold
                          ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {fac.storage_type}
                    </span>
                  </div>

                  <div className="mt-2 text-xs font-bold text-white truncate">{fac.facility_name}</div>
                  <div className="text-[11px] text-zinc-400 truncate mt-0.5">{fac.location}</div>

                  <div className="mt-3 pt-2 border-t border-zinc-800/60 grid grid-cols-2 gap-1 text-[10px] font-mono">
                    <div>
                      <div className="text-zinc-500">AVAILABLE</div>
                      <div className="text-zinc-200 font-bold">{(fac.available_capacity_kg / 1000).toFixed(0)} MT</div>
                    </div>
                    <div>
                      <div className="text-zinc-500">RATE</div>
                      <div className="text-emerald-400 font-bold">₹{fac.cost_per_kg_day}/kg/d</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Interactive Storage Feasibility Calculator */}
      <div className="p-5 rounded-xl bg-zinc-900/50 border border-zinc-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs font-mono font-semibold text-zinc-300">
            HOLDING FEASIBILITY CALCULATOR: {activeFac?.facility_name}
          </div>
          <AssumptionBadge status="DEMO_ASSUMPTION" isDemo={true} />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="text-[10px] font-mono text-zinc-400">Produce Volume to Store (kg)</label>
            <input
              type="number"
              value={storageQtyKg}
              onChange={(e) => setStorageQtyKg(parseFloat(e.target.value) || 100)}
              className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-zinc-100 font-mono"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-zinc-400">Planned Storage Duration (days)</label>
            <input
              type="number"
              value={durationDays}
              onChange={(e) => setDurationDays(parseInt(e.target.value) || 1)}
              className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-zinc-100 font-mono"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono text-zinc-400">Facility Operating Horizon</label>
            <div className="w-full mt-1 p-2 rounded bg-zinc-950 border border-zinc-800/80 text-[11px] text-zinc-300 font-mono">
              Min: {activeFac?.min_duration_days}d | Max: {activeFac?.max_duration_days}d
            </div>
          </div>
        </div>

        {/* Feasibility Result Summary */}
        {feasLoading ? (
          <div className="py-4 text-center text-xs text-zinc-400 animate-pulse">
            Verifying capacity availability and duration bounds...
          </div>
        ) : feasibility ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-center">
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">FEASIBILITY STATUS</div>
              <div
                className={`text-sm font-bold font-mono mt-1 ${
                  feasibility.status === "FEASIBLE"
                    ? "text-emerald-400"
                    : feasibility.status === "PARTIALLY_FEASIBLE"
                    ? "text-amber-400"
                    : "text-red-400"
                }`}
              >
                {feasibility.status}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">ALLOCATED STORED VOLUME</div>
              <div className="text-base font-bold font-mono text-white mt-0.5">
                {feasibility.stored_quantity_kg.toFixed(0)} kg
              </div>
              {feasibility.unstored_quantity_kg > 0 && (
                <div className="text-[10px] text-amber-400 font-mono mt-0.5">
                  Shortfall: {feasibility.unstored_quantity_kg.toFixed(0)} kg
                </div>
              )}
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">ESTIMATED HOLDING FEE</div>
              <div className="text-base font-bold font-mono text-amber-300 mt-0.5">
                ₹{feasibility.storage_cost.toFixed(2)}
              </div>
              <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
                ₹{activeFac?.cost_per_kg_day}/kg/day
              </div>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">CLIMATE SPECS</div>
              <div className="text-sm font-bold font-mono text-cyan-300 mt-0.5">
                {activeFac?.temperature_celsius != null ? `${activeFac.temperature_celsius}°C` : "Ambient"}
              </div>
              <div className="text-[10px] text-zinc-400 mt-0.5">
                {activeFac?.humidity_pct != null ? `${activeFac.humidity_pct}% RH` : "Vented"}
              </div>
            </div>
          </div>
        ) : null}

        {feasibility && feasibility.warnings.length > 0 && (
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-1 text-xs text-amber-300">
            {feasibility.warnings.map((w, i) => (
              <div key={i} className="flex items-center space-x-1.5">
                <span>⚠️</span>
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Decoupled Perishability Deterioration Trajectory */}
      <PerishabilityChart commodityId={selectedCommodityId} initialQuantityKg={storageQtyKg} />
    </div>
  );
};
