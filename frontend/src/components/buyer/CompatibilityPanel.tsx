import React, { useState } from "react";
import { CompatibilityMatch, FarmerSupply } from "@/types/buyer";
import { BuyerProvenance } from "./BuyerProvenance";

interface CompatibilityPanelProps {
  matches: CompatibilityMatch[];
  supply: FarmerSupply;
  onChangeSupply: (newSupply: FarmerSupply) => void;
  onSelectBuyerAudit: (buyerId: string, buyerName: string) => void;
  loading: boolean;
  sampleSupplies: FarmerSupply[];
}

export const CompatibilityPanel: React.FC<CompatibilityPanelProps> = ({
  matches,
  supply,
  onChangeSupply,
  onSelectBuyerAudit,
  loading,
  sampleSupplies,
}) => {
  const [filterCompatibleOnly, setFilterCompatibleOnly] = useState<boolean>(false);

  const displayedMatches = filterCompatibleOnly
    ? matches.filter((m) => m.is_compatible)
    : matches;

  return (
    <div className="space-y-6">
      {/* Strict Anti-Recommendation Governance Banner */}
      <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 space-y-2">
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="font-bold text-white uppercase tracking-wider">
            Descriptive Candidate Matching Engine
          </span>
          <span className="text-zinc-500">•</span>
          <span className="text-zinc-400">SIH26132 Step 12</span>
        </div>
        <p className="text-xs text-zinc-300 leading-relaxed font-sans">
          Evaluates multi-attribute physical and temporal feasibility against registered buyer specifications.
          Contains <strong className="text-white">zero normative ranking, winning scores, or SELL/HOLD advice</strong>.
          Realization costing and optimal allocation are handled downstream in Steps 13 and 14.
        </p>
      </div>

      {/* Produce Lot Configuration & Presets */}
      <div className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
          <div>
            <div className="text-xs font-mono font-semibold text-zinc-200">PRODUCE LOT SPECIFICATION</div>
            <div className="text-[11px] text-zinc-400">Configure harvest lot attributes for constraint evaluation</div>
          </div>

          {/* Sample Preset Buttons */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] font-mono text-zinc-400 mr-1">DEMO PRESETS:</span>
            {sampleSupplies.map((s) => (
              <button
                key={s.id}
                onClick={() => onChangeSupply(s)}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition-all ${
                  supply.id === s.id
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-transparent"
                }`}
              >
                {s.commodity_id.toUpperCase()} ({s.quantity_kg}kg, {s.quality_grade})
              </button>
            ))}
          </div>
        </div>

        {/* Lot Attributes Input Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 gap-3.5 text-xs font-mono">
          <div>
            <label className="text-[10px] text-zinc-400 block mb-1">COMMODITY</label>
            <input
              type="text"
              value={supply.commodity_id.toUpperCase()}
              disabled
              className="w-full px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-300"
            />
          </div>

          <div>
            <label className="text-[10px] text-zinc-400 block mb-1">AVAILABLE QUANTITY (KG)</label>
            <input
              type="number"
              value={supply.quantity_kg}
              onChange={(e) =>
                onChangeSupply({ ...supply, quantity_kg: Math.max(1, Number(e.target.value)) })
              }
              className="w-full px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-200 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          <div>
            <label className="text-[10px] text-zinc-400 block mb-1">QUALITY GRADE</label>
            <select
              value={supply.quality_grade}
              onChange={(e) => onChangeSupply({ ...supply, quality_grade: e.target.value })}
              className="w-full px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-200 focus:outline-none focus:border-emerald-500/50"
            >
              <option value="GRADE_A">Grade A (Premium)</option>
              <option value="GRADE_B">Grade B (Standard)</option>
              <option value="GRADE_C">Grade C (Processing)</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] text-zinc-400 block mb-1">ORIGIN FARMGATE</label>
            <input
              type="text"
              value={supply.origin_location}
              onChange={(e) => onChangeSupply({ ...supply, origin_location: e.target.value })}
              className="w-full px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-200 focus:outline-none focus:border-emerald-500/50"
            />
          </div>
        </div>
      </div>

      {/* Matching Results Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="text-zinc-400">
            EVALUATED: <strong className="text-zinc-200">{matches.length}</strong> requirements
          </span>
          <span className="text-zinc-600">|</span>
          <span className="text-emerald-400 font-semibold">
            {matches.filter((m) => m.is_compatible).length} Fully Compatible
          </span>
        </div>

        <label className="inline-flex items-center space-x-2 text-xs font-mono text-zinc-300 cursor-pointer">
          <input
            type="checkbox"
            checked={filterCompatibleOnly}
            onChange={(e) => setFilterCompatibleOnly(e.target.checked)}
            className="rounded bg-zinc-800 border-zinc-700 text-emerald-500 focus:ring-0"
          />
          <span>Show compatible options only</span>
        </label>
      </div>

      {/* Candidate Cards Grid */}
      {loading ? (
        <div className="py-16 text-center text-xs font-mono text-zinc-400 animate-pulse">
          Evaluating multi-dimensional bipartite constraints...
        </div>
      ) : displayedMatches.length === 0 ? (
        <div className="p-8 text-center rounded-xl bg-zinc-900/30 border border-zinc-800 text-xs text-zinc-400 font-mono">
          No buyer requirements met the compatibility criteria for this produce lot.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {displayedMatches.map((match) => {
            return (
              <div
                key={match.requirement_id}
                className={`p-5 rounded-2xl border transition-all ${
                  match.is_compatible
                    ? "bg-zinc-900/80 border-emerald-500/30 shadow-md"
                    : "bg-zinc-900/40 border-zinc-800/80 opacity-80"
                }`}
              >
                {/* Card Header */}
                <div className="flex items-start justify-between gap-2 border-b border-zinc-800/60 pb-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white text-sm">{match.buyer_name}</span>
                      <span
                        className={`text-[9px] font-mono px-2 py-0.5 rounded font-semibold ${
                          match.is_compatible
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        }`}
                      >
                        {match.is_compatible ? "COMPATIBLE" : "INCOMPATIBLE"}
                      </span>
                    </div>
                    <div className="text-[10px] text-zinc-400 font-mono mt-0.5">
                      Spec ID: {match.requirement_id}
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectBuyerAudit(match.buyer_id, match.buyer_name)}
                    className="text-[10px] font-mono text-emerald-400 hover:text-emerald-300 underline shrink-0"
                  >
                    Audit Log →
                  </button>
                </div>

                {/* Constraint Assessment Pills */}
                <div className="grid grid-cols-3 gap-2 py-3.5 border-b border-zinc-800/60 text-[11px] font-mono">
                  <div className="p-2 rounded-lg bg-zinc-950/60 border border-zinc-800">
                    <div className="text-zinc-500 text-[10px]">QUALITY</div>
                    <div className="flex items-center space-x-1 mt-0.5">
                      <span>{match.quality_match ? "✓" : "✗"}</span>
                      <span className={match.quality_match ? "text-emerald-400" : "text-amber-400"}>
                        {match.preferred_grade}
                      </span>
                    </div>
                  </div>

                  <div className="p-2 rounded-lg bg-zinc-950/60 border border-zinc-800">
                    <div className="text-zinc-500 text-[10px]">CAPACITY</div>
                    <div className="flex items-center space-x-1 mt-0.5">
                      <span>{match.compatible_quantity_kg > 0 ? "✓" : "✗"}</span>
                      <span className="text-zinc-200">
                        {match.compatible_quantity_kg} kg
                      </span>
                    </div>
                  </div>

                  <div className="p-2 rounded-lg bg-zinc-950/60 border border-zinc-800">
                    <div className="text-zinc-500 text-[10px]">DISTANCE</div>
                    <div className="flex items-center space-x-1 mt-0.5">
                      <span>📍</span>
                      <span className="text-zinc-200">
                        {match.distance_km !== null && match.distance_km !== undefined
                          ? `${match.distance_km} km`
                          : "Unknown"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Commercial Terms */}
                <div className="py-3 border-b border-zinc-800/60 space-y-1.5 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-400">Baseline Quote:</span>
                    <span className="font-bold text-emerald-400">
                      {match.quoted_price ? `₹${match.quoted_price.toFixed(2)}/kg` : "Negotiable"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-zinc-500">Delivery Mode:</span>
                    <span className="text-zinc-300">{match.delivery_mode.replace("_", " ")}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-zinc-500">Payment Terms:</span>
                    <span className="text-zinc-300">{match.payment_terms.replace("_", " ")}</span>
                  </div>
                </div>

                {/* Factual Additive Explanations */}
                <div className="pt-3 space-y-1 text-[11px] text-zinc-400 font-sans">
                  <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider">
                    EVALUATION RATIONALE:
                  </div>
                  <ul className="space-y-0.5 list-disc list-inside">
                    {match.explanations.map((exp, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {exp}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Card Footer Provenance */}
                <div className="mt-4 pt-2.5 border-t border-zinc-800/40 flex items-center justify-between">
                  <BuyerProvenance status={match.provenance_status} isDemo={match.is_demo} />
                  <span className="text-[10px] font-mono text-zinc-500">
                    Overlap: {match.overlap_days} days
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
