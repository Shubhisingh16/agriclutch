"use client";

import React, { useState, useEffect } from "react";
import { getPerishabilityTrajectory } from "@/lib/api/logistics";
import { PerishabilityTrajectory } from "@/types/logistics";
import { AssumptionBadge } from "./AssumptionBadge";

interface PerishabilityChartProps {
  commodityId: string;
  initialQuantityKg?: number;
}

export const PerishabilityChart: React.FC<PerishabilityChartProps> = ({
  commodityId,
  initialQuantityKg = 2500,
}) => {
  const [ambientTraj, setAmbientTraj] = useState<PerishabilityTrajectory | null>(null);
  const [coldTraj, setColdTraj] = useState<PerishabilityTrajectory | null>(null);
  const [days, setDays] = useState<number>(7);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      setLoading(true);
      try {
        const [amb, cld] = await Promise.all([
          getPerishabilityTrajectory({
            commodity_id: commodityId,
            storage_type: "AMBIENT",
            initial_quantity_kg: initialQuantityKg,
            duration_days: days,
          }),
          getPerishabilityTrajectory({
            commodity_id: commodityId,
            storage_type: "COLD",
            initial_quantity_kg: initialQuantityKg,
            duration_days: days,
          }),
        ]);
        if (!isMounted) return;
        setAmbientTraj(amb);
        setColdTraj(cld);
      } catch {
        // Handled silently with fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [commodityId, initialQuantityKg, days]);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
        <div className="flex items-center space-x-2">
          <span className="text-xl">📉</span>
          <div>
            <h4 className="text-sm font-bold text-zinc-100">
              Decoupled Crop Deterioration & Shelf-Life Model
            </h4>
            <p className="text-[11px] text-zinc-400">
              Models physical mass shrinkage S(t) = e^(-δ·t) and quality grade discount F(t) = F₀·e^(-β·t)
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-zinc-300">
            <span className="font-mono text-zinc-400">Horizon:</span>
            {[3, 7, 14, 21].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
                  days === d
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <AssumptionBadge status="DEMO_ASSUMPTION" isDemo={true} />
        </div>
      </div>

      {/* Mathematical Specification Bar */}
      <div className="p-3 rounded-lg bg-zinc-950/70 border border-zinc-800/60 font-mono text-[11px] flex flex-wrap items-center justify-between gap-2">
        <div className="text-zinc-300">
          <span className="text-emerald-400 font-bold">Physical Survival:</span> Q_eff(t) = Q₀ · exp(-δ · t)
          <span className="mx-2 text-zinc-600">|</span>
          <span className="text-blue-400 font-bold">Quality Factor:</span> F_qual(t) = F₀ · exp(-β · t)
        </div>
        <div className="text-zinc-400 text-[10px]">
          Commodity: <span className="uppercase text-zinc-200 font-bold">{commodityId}</span>
        </div>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-zinc-400 animate-pulse">
          Computing non-linear decay trajectories...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Ambient Holding */}
          <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/70 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-xs font-bold text-amber-400 flex items-center space-x-1.5">
                <span>☀️</span>
                <span>Ambient Farm Holding</span>
              </div>
              <span className="text-[10px] font-mono text-zinc-400">
                δ = {ambientTraj?.model_spec?.decay_parameter_delta ?? 0.035}/day
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <div className="text-[10px] text-zinc-400">FINAL MASS</div>
                <div className="text-sm font-bold font-mono text-zinc-100 mt-0.5">
                  {ambientTraj?.final_quantity_kg != null ? `${ambientTraj.final_quantity_kg.toFixed(0)} kg` : "N/A"}
                </div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <div className="text-[10px] text-zinc-400">MASS LOSS</div>
                <div className="text-sm font-bold font-mono text-red-400 mt-0.5">
                  {ambientTraj?.final_quantity_kg != null
                    ? `-${(initialQuantityKg - ambientTraj.final_quantity_kg).toFixed(0)} kg`
                    : "N/A"}
                </div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <div className="text-[10px] text-zinc-400">QUALITY INDEX</div>
                <div className="text-sm font-bold font-mono text-amber-300 mt-0.5">
                  {ambientTraj?.final_quality_factor != null
                    ? `${(ambientTraj.final_quality_factor * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>
            </div>

            {/* Daily timeline table */}
            <div className="overflow-x-auto max-h-48 overflow-y-auto border border-zinc-800/60 rounded">
              <table className="w-full text-left text-[11px] font-mono">
                <thead className="bg-zinc-900 text-zinc-400 sticky top-0">
                  <tr>
                    <th className="p-1.5">Day</th>
                    <th className="p-1.5">Quantity</th>
                    <th className="p-1.5">Loss</th>
                    <th className="p-1.5">Quality</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                  {ambientTraj?.trajectory.map((pt) => (
                    <tr key={pt.day} className="hover:bg-zinc-900/40">
                      <td className="p-1.5 text-zinc-400">Day {pt.day}</td>
                      <td className="p-1.5">{pt.quantity_kg.toFixed(0)} kg</td>
                      <td className="p-1.5 text-red-400">-{pt.quantity_loss_kg.toFixed(0)} kg</td>
                      <td className="p-1.5 text-amber-300">{(pt.quality_factor * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cold Chain Holding */}
          <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/70 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-xs font-bold text-cyan-400 flex items-center space-x-1.5">
                <span>❄️</span>
                <span>Cold Chain Storage Hub</span>
              </div>
              <span className="text-[10px] font-mono text-zinc-400">
                δ = {coldTraj?.model_spec?.decay_parameter_delta ?? 0.008}/day
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <div className="text-[10px] text-zinc-400">FINAL MASS</div>
                <div className="text-sm font-bold font-mono text-zinc-100 mt-0.5">
                  {coldTraj?.final_quantity_kg != null ? `${coldTraj.final_quantity_kg.toFixed(0)} kg` : "N/A"}
                </div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <div className="text-[10px] text-zinc-400">MASS LOSS</div>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                  {coldTraj?.final_quantity_kg != null
                    ? `-${(initialQuantityKg - coldTraj.final_quantity_kg).toFixed(0)} kg`
                    : "N/A"}
                </div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <div className="text-[10px] text-zinc-400">QUALITY INDEX</div>
                <div className="text-sm font-bold font-mono text-cyan-300 mt-0.5">
                  {coldTraj?.final_quality_factor != null
                    ? `${(coldTraj.final_quality_factor * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>
            </div>

            {/* Daily timeline table */}
            <div className="overflow-x-auto max-h-48 overflow-y-auto border border-zinc-800/60 rounded">
              <table className="w-full text-left text-[11px] font-mono">
                <thead className="bg-zinc-900 text-zinc-400 sticky top-0">
                  <tr>
                    <th className="p-1.5">Day</th>
                    <th className="p-1.5">Quantity</th>
                    <th className="p-1.5">Loss</th>
                    <th className="p-1.5">Quality</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                  {coldTraj?.trajectory.map((pt) => (
                    <tr key={pt.day} className="hover:bg-zinc-900/40">
                      <td className="p-1.5 text-zinc-400">Day {pt.day}</td>
                      <td className="p-1.5">{pt.quantity_kg.toFixed(0)} kg</td>
                      <td className="p-1.5 text-emerald-400">-{pt.quantity_loss_kg.toFixed(0)} kg</td>
                      <td className="p-1.5 text-cyan-300">{(pt.quality_factor * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
