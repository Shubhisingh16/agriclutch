"use client";

import React from "react";
import { Commodity } from "@/lib/api/types";

interface CommoditySelectorProps {
  commodities: Commodity[];
  selectedCommodityId: string | null;
  onSelectCommodity: (commodityId: string) => void;
  disabled?: boolean;
}

export const CommoditySelector: React.FC<CommoditySelectorProps> = ({
  commodities,
  selectedCommodityId,
  onSelectCommodity,
  disabled = false,
}) => {
  const getCropEmoji = (name: string): string => {
    const lower = name.toLowerCase();
    if (lower.includes("tomato")) return "🍅";
    if (lower.includes("onion")) return "🧅";
    if (lower.includes("potato")) return "🥔";
    if (lower.includes("wheat") || lower.includes("paddy")) return "🌾";
    return "🌱";
  };

  const getCategoryColor = (category: string): string => {
    switch (category) {
      case "perishable":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      case "semi_perishable":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "storable":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-mono uppercase tracking-wider text-zinc-400">
          Target Crop Selection
        </label>
        <span className="text-[10px] font-mono text-zinc-500">
          {commodities.length} Registered Crops
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {commodities.map((comm) => {
          const isSelected = selectedCommodityId === comm.id;
          const emoji = getCropEmoji(comm.name);
          const categoryBadge = getCategoryColor(comm.category);

          return (
            <button
              key={comm.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelectCommodity(comm.id)}
              className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden ${
                isSelected
                  ? "bg-emerald-500/10 border-emerald-500/60 shadow-md shadow-emerald-950/20 text-white ring-1 ring-emerald-500/40"
                  : "bg-zinc-900/50 border-zinc-800/80 hover:bg-zinc-800/40 hover:border-zinc-700 text-zinc-300"
              } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xl">{emoji}</span>
                  <div>
                    <div className="font-semibold text-sm tracking-tight flex items-center space-x-1.5">
                      <span>{comm.name}</span>
                      {comm.hindi_name && (
                        <span className="text-xs text-zinc-400 font-normal">
                          ({comm.hindi_name})
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] font-mono text-zinc-400 mt-0.5">
                      Shelf-life: {comm.max_ambient_holding_days}d safe
                    </div>
                  </div>
                </div>

                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase ${categoryBadge}`}
                >
                  {comm.category.replace("_", "-")}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
