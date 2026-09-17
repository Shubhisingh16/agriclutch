"use client";

import React, { useState } from "react";
import { Market } from "@/lib/api/types";

interface MarketSelectorProps {
  markets: Market[];
  selectedMarketId: string | null;
  onSelectMarket: (marketId: string) => void;
  disabled?: boolean;
}

export const MarketSelector: React.FC<MarketSelectorProps> = ({
  markets,
  selectedMarketId,
  onSelectMarket,
  disabled = false,
}) => {
  const [stateFilter, setStateFilter] = useState<string>("all");

  const uniqueStates = Array.from(new Set(markets.map((m) => m.state))).sort();

  const filteredMarkets =
    stateFilter === "all"
      ? markets
      : markets.filter((m) => m.state === stateFilter);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-mono uppercase tracking-wider text-zinc-400">
          APMC Mandi Network
        </label>
        {/* State Filter Pills */}
        <div className="flex items-center space-x-1 text-[11px] font-mono">
          <button
            type="button"
            onClick={() => setStateFilter("all")}
            className={`px-2 py-0.5 rounded transition-colors ${
              stateFilter === "all"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            All States
          </button>
          {uniqueStates.map((state) => (
            <button
              key={state}
              type="button"
              onClick={() => setStateFilter(state)}
              className={`px-2 py-0.5 rounded transition-colors ${
                stateFilter === state
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {state}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {filteredMarkets.map((market) => {
          const isSelected = selectedMarketId === market.id;

          return (
            <button
              key={market.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelectMarket(market.id)}
              className={`p-3 rounded-xl border text-left transition-all relative ${
                isSelected
                  ? "bg-teal-500/10 border-teal-500/60 shadow-md shadow-teal-950/20 text-white ring-1 ring-teal-500/40"
                  : "bg-zinc-900/50 border-zinc-800/80 hover:bg-zinc-800/40 hover:border-zinc-700 text-zinc-300"
              } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-sm tracking-tight text-white">
                    {market.name}
                  </div>
                  <div className="text-[11px] text-zinc-400 mt-0.5">
                    {market.district}, {market.state}
                  </div>
                  <div className="text-[10px] font-mono text-zinc-500 mt-1">
                    APMC #{market.apmc_code}
                  </div>
                </div>

                {market.is_terminal_market ? (
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase">
                    Terminal
                  </span>
                ) : (
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700 uppercase">
                    Primary
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
