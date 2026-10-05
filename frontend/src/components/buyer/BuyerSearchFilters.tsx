import React from "react";
import { BuyerType } from "@/types/buyer";

interface BuyerSearchFiltersProps {
  selectedType: string;
  onSelectType: (type: string) => void;
  locationFilter: string;
  onChangeLocation: (location: string) => void;
  maxDistanceKm: number | null;
  onChangeMaxDistance: (dist: number | null) => void;
}

const BUYER_TYPES: { id: string; label: string }[] = [
  { id: "ALL", label: "All Buyer Types" },
  { id: "wholesaler", label: "Wholesalers (APMC)" },
  { id: "processor", label: "Food Processors" },
  { id: "retailer", label: "Modern Retail Chains" },
  { id: "aggregator", label: "FPO Aggregators" },
  { id: "exporter", label: "Exporters" },
  { id: "cooperative", label: "State Cooperatives" },
];

export const BuyerSearchFilters: React.FC<BuyerSearchFiltersProps> = ({
  selectedType,
  onSelectType,
  locationFilter,
  onChangeLocation,
  maxDistanceKm,
  onChangeMaxDistance,
}) => {
  return (
    <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Type Selector Pills */}
        <div className="flex flex-wrap gap-1.5">
          {BUYER_TYPES.map((bt) => {
            const isActive = selectedType === bt.id;
            return (
              <button
                key={bt.id}
                onClick={() => onSelectType(bt.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                    : "bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 border border-transparent"
                }`}
              >
                {bt.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-zinc-800/60">
        {/* Location Substring Filter */}
        <div>
          <label className="block text-[11px] font-mono text-zinc-400 mb-1">
            LOCATION / CORRIDOR FILTER:
          </label>
          <input
            type="text"
            placeholder="e.g. Chandigarh, Panchkula, Sonipat, Patiala..."
            value={locationFilter}
            onChange={(e) => onChangeLocation(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-emerald-500/50"
          />
        </div>

        {/* Max Distance Radius */}
        <div>
          <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 mb-1">
            <span>MAX TRANSIT RADIUS:</span>
            <span className="text-emerald-400 font-semibold">
              {maxDistanceKm ? `${maxDistanceKm} km` : "No limit (All India)"}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="range"
              min="10"
              max="300"
              step="10"
              value={maxDistanceKm || 300}
              onChange={(e) => {
                const val = Number(e.target.value);
                onChangeMaxDistance(val >= 300 ? null : val);
              }}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            {maxDistanceKm !== null && (
              <button
                onClick={() => onChangeMaxDistance(null)}
                className="text-[10px] text-zinc-400 hover:text-zinc-200 underline font-mono shrink-0"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
