"use client";

import React from "react";
import { Commodity, Market, PriceObservation } from "@/lib/api/types";
import { FreshnessBadge } from "./FreshnessBadge";

interface MarketOverviewProps {
  commodity: Commodity | null;
  market: Market | null;
  latestObservation: PriceObservation | null;
  dataSourceHeader?: string | null;
  dataMode?: "DEMO" | "DATABASE" | null;
  retrievedAt: string | null;
}

export const MarketOverview: React.FC<MarketOverviewProps> = ({
  commodity,
  market,
  latestObservation,
  dataSourceHeader,
  dataMode,
  retrievedAt,
}) => {
  if (!commodity || !market) {
    return null;
  }

  const hasData = latestObservation !== null;

  return (
    <div className="rounded-2xl bg-gradient-to-br from-zinc-900 via-zinc-900/90 to-emerald-950/20 border border-zinc-800/90 p-6 shadow-xl space-y-6">
      {/* Top Header & Freshness */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-zinc-800/70 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 uppercase tracking-wider">
            <span>Market Intelligence</span>
            <span>•</span>
            <span>APMC Physical Trading</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-1 flex items-center space-x-2">
            <span>
              {commodity.name} at {market.name}
            </span>
            {commodity.hindi_name && (
              <span className="text-base font-normal text-zinc-400">
                ({commodity.hindi_name})
              </span>
            )}
          </h2>
          <div className="text-xs text-zinc-400 mt-0.5">
            {market.district}, {market.state} • APMC Code: #{market.apmc_code}
            {market.is_terminal_market && " (Terminal Market)"}
          </div>
        </div>

        <FreshnessBadge
          observationDate={latestObservation?.record_date || null}
          retrievedAt={retrievedAt}
          sourceName={latestObservation?.source_name}
          dataSourceHeader={dataSourceHeader}
          dataMode={dataMode}
        />
      </div>

      {/* Metrics Row */}
      {hasData ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Canonical Modal Price */}
          <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
              Normalized Modal Price
            </div>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                ₹{latestObservation.normalized_modal_price.toFixed(2)}
              </span>
              <span className="text-xs font-mono text-zinc-400">/ kg</span>
            </div>
            <div className="mt-1.5 text-[11px] text-zinc-400 font-mono">
              Source Rate:{" "}
              <strong className="text-zinc-200">
                ₹{latestObservation.original_modal_price.toLocaleString("en-IN")}{" "}
                {latestObservation.original_price_unit}
              </strong>
            </div>
          </div>

          {/* Card 2: Trading Range Corridor */}
          <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
              Session Price Corridor
            </div>
            <div className="mt-1 flex items-baseline space-x-1.5 text-lg font-bold text-white">
              <span>₹{latestObservation.normalized_min_price.toFixed(2)}</span>
              <span className="text-zinc-500 font-normal text-sm">–</span>
              <span>₹{latestObservation.normalized_max_price.toFixed(2)}</span>
              <span className="text-xs font-mono text-zinc-400">/ kg</span>
            </div>
            <div className="mt-1.5 text-[11px] text-zinc-400 font-mono">
              Spread: ₹
              {(
                latestObservation.normalized_max_price -
                latestObservation.normalized_min_price
              ).toFixed(2)}
              /kg
            </div>
          </div>

          {/* Card 3: Daily Arrivals */}
          <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
              Recorded Daily Arrivals
            </div>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-white">
                {latestObservation.arrival_tonnes.toLocaleString("en-IN")}
              </span>
              <span className="text-xs font-mono text-zinc-400">Tonnes</span>
            </div>
            <div className="mt-1.5 text-[11px] text-zinc-400 font-mono">
              Grade: {latestObservation.grade} • Cultivar: {latestObservation.variety}
            </div>
          </div>

          {/* Card 4: Shelf-Life & Spoilage Constant */}
          <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80">
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
              Crop Holding Constraint
            </div>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-amber-400">
                {commodity.max_ambient_holding_days}
              </span>
              <span className="text-xs font-mono text-zinc-400">Days Ambient</span>
            </div>
            <div className="mt-1.5 text-[11px] text-zinc-400 font-mono">
              Decay Delta: {(commodity.default_spoilage_rate * 100).toFixed(1)}%/day
            </div>
          </div>
        </div>
      ) : (
        <div className="p-6 rounded-xl bg-zinc-950/40 border border-zinc-800/60 text-center">
          <p className="text-xs font-mono text-zinc-400">
            No price observations reported for {commodity.name} at {market.name}.
          </p>
        </div>
      )}
    </div>
  );
};
