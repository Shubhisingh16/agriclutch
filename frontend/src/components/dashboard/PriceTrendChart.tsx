"use client";

import React, { useState, useMemo } from "react";
import { PriceObservation } from "@/lib/api/types";

interface PriceTrendChartProps {
  observations: PriceObservation[];
  commodityName: string;
  marketName: string;
}

export const PriceTrendChart: React.FC<PriceTrendChartProps> = ({
  observations,
  commodityName,
  marketName,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Sort observations ascending by date for chronological rendering
  const sorted = useMemo(() => {
    return [...observations].sort(
      (a, b) => new Date(a.record_date).getTime() - new Date(b.record_date).getTime()
    );
  }, [observations]);

  // Chart dimensions
  const width = 800;
  const height = 300;
  const padding = { top: 20, right: 30, bottom: 40, left: 60 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Min and max bounds for Y axis
  const { minPrice, maxPrice } = useMemo(() => {
    if (sorted.length === 0) return { minPrice: 0, maxPrice: 50 };
    let min = Infinity;
    let max = -Infinity;
    for (const d of sorted) {
      if (d.normalized_min_price < min) min = d.normalized_min_price;
      if (d.normalized_max_price > max) max = d.normalized_max_price;
    }
    // Add padding to domain
    const margin = (max - min) * 0.15 || 5;
    return {
      minPrice: Math.max(0, Math.floor(min - margin)),
      maxPrice: Math.ceil(max + margin),
    };
  }, [sorted]);

  const priceRange = maxPrice - minPrice || 1;

  const getX = React.useCallback(
    (index: number) => {
      if (sorted.length <= 1) return padding.left + innerWidth / 2;
      return padding.left + (index / (sorted.length - 1)) * innerWidth;
    },
    [sorted.length, innerWidth, padding.left]
  );

  const getY = React.useCallback(
    (val: number) => {
      return padding.top + innerHeight - ((val - minPrice) / priceRange) * innerHeight;
    },
    [minPrice, priceRange, innerHeight, padding.top]
  );

  // Generate SVG path for modal price
  const modalPath = useMemo(() => {
    if (sorted.length === 0) return "";
    return sorted
      .map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(d.normalized_modal_price)}`)
      .join(" ");
  }, [sorted, getX, getY]);

  // Generate SVG polygon for min-max corridor
  const corridorPath = useMemo(() => {
    if (sorted.length < 2) return "";
    const topPoints = sorted.map((d, i) => `${getX(i)},${getY(d.normalized_max_price)}`);
    const bottomPoints = sorted
      .map((d, i) => `${getX(i)},${getY(d.normalized_min_price)}`)
      .reverse();
    return `M ${topPoints.join(" L ")} L ${bottomPoints.join(" L ")} Z`;
  }, [sorted, getX, getY]);

  // Y-axis ticks
  const yTicks = useMemo(() => {
    const count = 5;
    const step = priceRange / (count - 1);
    return Array.from({ length: count }, (_, i) => minPrice + i * step);
  }, [minPrice, priceRange]);

  const activeObs = hoveredIndex !== null ? sorted[hoveredIndex] : null;

  if (sorted.length === 0) {
    return (
      <div className="p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800/80 text-center space-y-2">
        <div className="text-zinc-600 text-3xl">📈</div>
        <h4 className="text-sm font-semibold text-zinc-300">No Time-Series Available</h4>
        <p className="text-xs text-zinc-400">
          No historical price points recorded for {commodityName} at {marketName}.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800/80 space-y-4">
      {/* Chart Title & Badges */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/60 pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-white tracking-tight">
              Historical APMC Price Trend
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
              Normalized INR/kg
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Daily recorded trading sessions for {commodityName} ({marketName})
          </p>
        </div>

        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-emerald-400">
            <span className="w-3 h-0.5 bg-emerald-400 rounded-full inline-block" />
            <span>Modal Rate</span>
          </div>
          <div className="flex items-center space-x-1.5 text-emerald-500/60">
            <span className="w-3 h-2 bg-emerald-500/20 border border-emerald-500/40 rounded inline-block" />
            <span>Min-Max Corridor</span>
          </div>
        </div>
      </div>

      {/* SVG Chart Canvas */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto select-none"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          {/* Y Axis Grid Lines and Ticks */}
          {yTicks.map((tick, i) => {
            const y = getY(tick);
            return (
              <g key={i} className="text-[11px] font-mono">
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#27272a"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill="#71717a"
                  className="text-[10px]"
                >
                  ₹{tick.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Min-Max Shaded Corridor */}
          {corridorPath && (
            <path
              d={corridorPath}
              fill="rgba(16, 185, 129, 0.08)"
              stroke="rgba(16, 185, 129, 0.25)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
          )}

          {/* Modal Price Line */}
          <path
            d={modalPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points and Hover Vertical Crosshair */}
          {sorted.map((d, i) => {
            const cx = getX(i);
            const cy = getY(d.normalized_modal_price);
            const isHovered = hoveredIndex === i;

            return (
              <g key={d.observation_id || i}>
                {/* Vertical Crosshair on Hover */}
                {isHovered && (
                  <line
                    x1={cx}
                    y1={padding.top}
                    x2={cx}
                    y2={height - padding.bottom}
                    stroke="#52525b"
                    strokeWidth="1"
                    strokeDasharray="3 3"
                  />
                )}

                {/* Visible Data Node */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : 4}
                  fill={isHovered ? "#34d399" : "#10b981"}
                  stroke="#09090b"
                  strokeWidth="2"
                  className="transition-all cursor-pointer"
                  onMouseEnter={() => setHoveredIndex(i)}
                />

                {/* Interactive Click/Touch Hit Target */}
                <rect
                  x={cx - 15}
                  y={padding.top}
                  width={30}
                  height={innerHeight}
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredIndex(i)}
                />

                {/* X Axis Date Labels */}
                <text
                  x={cx}
                  y={height - padding.bottom + 20}
                  textAnchor="middle"
                  fill={isHovered ? "#f4f4f5" : "#71717a"}
                  className="text-[10px] font-mono"
                >
                  {new Date(d.record_date).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                  })}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Overlay */}
        {activeObs && (
          <div className="mt-2 p-3 rounded-xl bg-zinc-950/90 border border-zinc-800 text-xs font-mono grid grid-cols-2 sm:grid-cols-4 gap-3 shadow-lg">
            <div>
              <div className="text-zinc-500 text-[10px]">TRADING DATE</div>
              <div className="text-zinc-200 font-semibold mt-0.5">
                {activeObs.record_date}
              </div>
            </div>
            <div>
              <div className="text-zinc-500 text-[10px]">NORMALIZED MODAL</div>
              <div className="text-emerald-400 font-bold mt-0.5">
                ₹{activeObs.normalized_modal_price.toFixed(2)} / kg
              </div>
            </div>
            <div>
              <div className="text-zinc-500 text-[10px]">SOURCE RATE</div>
              <div className="text-zinc-200 font-medium mt-0.5">
                ₹{activeObs.original_modal_price.toLocaleString("en-IN")}{" "}
                {activeObs.original_price_unit}
              </div>
            </div>
            <div>
              <div className="text-zinc-500 text-[10px]">RECORDED ARRIVALS</div>
              <div className="text-zinc-200 font-medium mt-0.5">
                {activeObs.arrival_tonnes} Tonnes
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Analytical Footnote */}
      <div className="pt-2 border-t border-zinc-800/60 flex flex-wrap items-center justify-between text-[10px] font-mono text-zinc-500">
        <div>
          <span>Note: Purely historical mandi observations.</span>{" "}
          <span className="text-zinc-400">Not a predictive forecast.</span>
        </div>
        <div>Observations Count: {sorted.length} Sessions</div>
      </div>
    </div>
  );
};
