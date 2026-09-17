"use client";

import React, { useState } from "react";
import { Market, PriceObservation } from "@/lib/api/types";

interface MarketMapProps {
  markets: Market[];
  selectedMarketId: string | null;
  marketLatestPrices: Map<string, PriceObservation>;
  onSelectMarket: (marketId: string) => void;
}

export const MarketMap: React.FC<MarketMapProps> = ({
  markets,
  selectedMarketId,
  marketLatestPrices,
  onSelectMarket,
}) => {
  const [hoveredMarketId, setHoveredMarketId] = useState<string | null>(null);

  // Filter markets with valid coordinates
  const validMarkets = markets.filter(
    (m) =>
      typeof m.latitude === "number" &&
      typeof m.longitude === "number" &&
      !isNaN(m.latitude) &&
      !isNaN(m.longitude)
  );

  if (validMarkets.length === 0) {
    return (
      <div className="p-8 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 text-center space-y-2">
        <div className="text-zinc-600 text-3xl">🗺️</div>
        <h4 className="text-sm font-semibold text-zinc-300">No Geospatial Coordinates</h4>
        <p className="text-xs text-zinc-400">
          Market coordinates are currently unavailable in the API.
        </p>
      </div>
    );
  }

  // Calculate dynamic coordinate bounds with padding
  const lats = validMarkets.map((m) => m.latitude);
  const lons = validMarkets.map((m) => m.longitude);
  const minLat = Math.min(...lats) - 0.25;
  const maxLat = Math.max(...lats) + 0.25;
  const minLon = Math.min(...lons) - 0.25;
  const maxLon = Math.max(...lons) + 0.25;

  const latRange = maxLat - minLat || 1;
  const lonRange = maxLon - minLon || 1;

  // SVG coordinate projection
  const svgWidth = 700;
  const svgHeight = 400;
  const padding = { top: 40, right: 60, bottom: 40, left: 60 };
  const innerW = svgWidth - padding.left - padding.right;
  const innerH = svgHeight - padding.top - padding.bottom;

  const projectX = (lon: number) => {
    return padding.left + ((lon - minLon) / lonRange) * innerW;
  };

  const projectY = (lat: number) => {
    // Invert latitude because SVG Y grows downwards, while latitude grows upwards (North)
    return padding.top + innerH - ((lat - minLat) / latRange) * innerH;
  };

  const hoveredMarket = validMarkets.find((m) => m.id === hoveredMarketId);
  const hoveredPrice = hoveredMarketId
    ? marketLatestPrices.get(hoveredMarketId)
    : null;

  return (
    <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800/80 space-y-4">
      {/* Map Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/60 pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-white tracking-tight">
              Regional Mandi Corridor Map
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              WGS84 Coordinates
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Geographic spatial network of APMC mandis (Click a node to select)
          </p>
        </div>

        <div className="text-xs font-mono text-zinc-500">
          Showing {validMarkets.length} Mandi Nodes
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div className="relative w-full overflow-hidden bg-zinc-950/80 rounded-xl border border-zinc-800/80 p-2">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto select-none"
          onMouseLeave={() => setHoveredMarketId(null)}
        >
          {/* Subtle Grid Background */}
          {Array.from({ length: 5 }).map((_, i) => (
            <line
              key={`h-${i}`}
              x1={padding.left}
              y1={padding.top + (i * innerH) / 4}
              x2={svgWidth - padding.right}
              y2={padding.top + (i * innerH) / 4}
              stroke="#18181b"
              strokeDasharray="2 4"
            />
          ))}
          {Array.from({ length: 5 }).map((_, i) => (
            <line
              key={`v-${i}`}
              x1={padding.left + (i * innerW) / 4}
              y1={padding.top}
              x2={padding.left + (i * innerW) / 4}
              y2={svgHeight - padding.bottom}
              stroke="#18181b"
              strokeDasharray="2 4"
            />
          ))}

          {/* Regional Corridor Transit Connectors */}
          {validMarkets.map((m1, i) => {
            const x1 = projectX(m1.longitude);
            const y1 = projectY(m1.latitude);

            return validMarkets.slice(i + 1).map((m2) => {
              const x2 = projectX(m2.longitude);
              const y2 = projectY(m2.latitude);

              return (
                <line
                  key={`${m1.id}-${m2.id}`}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#27272a"
                  strokeWidth="1"
                  strokeDasharray="4 6"
                />
              );
            });
          })}

          {/* Mandi Geospatial Nodes */}
          {validMarkets.map((m) => {
            const x = projectX(m.longitude);
            const y = projectY(m.latitude);
            const isSelected = m.id === selectedMarketId;
            const isHovered = m.id === hoveredMarketId;
            const obs = marketLatestPrices.get(m.id);

            return (
              <g
                key={m.id}
                className="cursor-pointer transition-all"
                onClick={() => onSelectMarket(m.id)}
                onMouseEnter={() => setHoveredMarketId(m.id)}
              >
                {/* Outer Glow Pulse for Selected / Terminal Mandi */}
                {isSelected && (
                  <circle
                    cx={x}
                    cy={y}
                    r="14"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="1.5"
                    strokeDasharray="2 2"
                    className="animate-spin origin-center"
                  />
                )}

                {/* Node Circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={isSelected ? 8 : isHovered ? 7 : 5}
                  fill={
                    isSelected
                      ? "#10b981"
                      : m.is_terminal_market
                      ? "#f59e0b"
                      : isHovered
                      ? "#38bdf8"
                      : "#3f3f46"
                  }
                  stroke="#09090b"
                  strokeWidth="2"
                />

                {/* Mandi Label */}
                <text
                  x={x}
                  y={y - 12}
                  textAnchor="middle"
                  fill={isSelected ? "#34d399" : isHovered ? "#f4f4f5" : "#a1a1aa"}
                  className="text-[11px] font-mono font-semibold"
                >
                  {m.name.split(" ")[0]}
                </text>

                {/* Price Label Badge */}
                {obs && (
                  <text
                    x={x}
                    y={y + 18}
                    textAnchor="middle"
                    fill={isSelected ? "#10b981" : "#71717a"}
                    className="text-[9px] font-mono font-bold"
                  >
                    ₹{obs.normalized_modal_price.toFixed(1)}/kg
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Details Card */}
        {hoveredMarket && (
          <div className="absolute top-4 right-4 p-3 rounded-xl bg-zinc-950/95 border border-zinc-700 shadow-xl text-xs font-mono max-w-xs pointer-events-none">
            <div className="font-bold text-white flex items-center justify-between">
              <span>{hoveredMarket.name}</span>
              {hoveredMarket.is_terminal_market && (
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Terminal
                </span>
              )}
            </div>
            <div className="text-[11px] text-zinc-400 mt-0.5">
              {hoveredMarket.district}, {hoveredMarket.state}
            </div>
            <div className="text-[10px] text-zinc-500 mt-1">
              Coords: {hoveredMarket.latitude.toFixed(4)}°N, {hoveredMarket.longitude.toFixed(4)}°E
            </div>
            {hoveredPrice ? (
              <div className="mt-2 pt-2 border-t border-zinc-800 flex items-center justify-between">
                <span className="text-zinc-400">Modal Rate:</span>
                <span className="font-bold text-emerald-400">
                  ₹{hoveredPrice.normalized_modal_price.toFixed(2)}/kg
                </span>
              </div>
            ) : (
              <div className="mt-2 pt-2 border-t border-zinc-800 text-zinc-500 text-[10px]">
                No recorded price for selection
              </div>
            )}
          </div>
        )}
      </div>

      {/* Map Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-[10px] font-mono text-zinc-500 pt-1">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            <span>Selected Mandi</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            <span>Terminal Market (Azadpur)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-600 inline-block" />
            <span>Primary APMC</span>
          </div>
        </div>
        <div>Projection: WGS84 Geodetic Coordinates</div>
      </div>
    </div>
  );
};
