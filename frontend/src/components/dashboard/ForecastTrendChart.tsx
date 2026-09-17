"use client";

import React, { useState, useMemo } from "react";
import { ForecastPoint, PriceObservation } from "@/lib/api/types";

interface ForecastTrendChartProps {
  observations: PriceObservation[];
  forecastPoints: ForecastPoint[];
  originDate: string;
  commodityName: string;
  marketName: string;
  modelName: string;
}

export const ForecastTrendChart: React.FC<ForecastTrendChartProps> = ({
  observations,
  forecastPoints,
  originDate,
  commodityName,
  marketName,
  modelName,
}) => {
  const [hoveredStep, setHoveredStep] = useState<{
    type: "history" | "forecast";
    index: number;
  } | null>(null);

  // Filter and sort historical observations ascending
  const sortedHistory = useMemo(() => {
    return [...observations]
      .sort((a, b) => new Date(a.record_date).getTime() - new Date(b.record_date).getTime())
      .slice(-30); // Show recent 30 context points for visual balance
  }, [observations]);

  // Total points across timeline
  const totalCount = sortedHistory.length + forecastPoints.length;

  // Chart dimensions
  const width = 840;
  const height = 320;
  const padding = { top: 25, right: 35, bottom: 45, left: 60 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Min and max bounds for Y axis across history and forecast
  const { minPrice, maxPrice } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;

    for (const d of sortedHistory) {
      if (d.normalized_min_price < min) min = d.normalized_min_price;
      if (d.normalized_max_price > max) max = d.normalized_max_price;
    }
    for (const fp of forecastPoints) {
      if (fp.q10 < min) min = fp.q10;
      if (fp.q90 > max) max = fp.q90;
    }

    if (min === Infinity) min = 20;
    if (max === -Infinity) max = 40;

    const margin = (max - min) * 0.15 || 4;
    return {
      minPrice: Math.max(0, Math.floor(min - margin)),
      maxPrice: Math.ceil(max + margin),
    };
  }, [sortedHistory, forecastPoints]);

  const priceRange = maxPrice - minPrice || 1;

  const getX = React.useCallback(
    (globalIndex: number) => {
      if (totalCount <= 1) return padding.left + innerWidth / 2;
      return padding.left + (globalIndex / (totalCount - 1)) * innerWidth;
    },
    [totalCount, innerWidth, padding.left]
  );

  const getY = React.useCallback(
    (val: number) => {
      return padding.top + innerHeight - ((val - minPrice) / priceRange) * innerHeight;
    },
    [minPrice, priceRange, innerHeight, padding.top]
  );

  // Boundary index between history and forecast
  const originIndex = Math.max(0, sortedHistory.length - 1);
  const originX = getX(originIndex);

  // Historical path
  const historyPath = useMemo(() => {
    if (sortedHistory.length === 0) return "";
    return sortedHistory
      .map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(d.normalized_modal_price)}`)
      .join(" ");
  }, [sortedHistory, getX, getY]);

  // Forecast median path (connecting from origin point to first forecast step)
  const forecastPath = useMemo(() => {
    if (forecastPoints.length === 0) return "";
    const lastHistPrice = sortedHistory.length > 0 ? sortedHistory[sortedHistory.length - 1].normalized_modal_price : forecastPoints[0].q50;
    const pts = [`M ${originX} ${getY(lastHistPrice)}`];
    forecastPoints.forEach((fp, i) => {
      const idx = sortedHistory.length + i;
      pts.push(`L ${getX(idx)} ${getY(fp.q50)}`);
    });
    return pts.join(" ");
  }, [forecastPoints, sortedHistory, originX, getX, getY]);

  // Forecast 80% corridor (P10 to P90)
  const corridor80Path = useMemo(() => {
    if (forecastPoints.length === 0) return "";
    const lastHistPrice = sortedHistory.length > 0 ? sortedHistory[sortedHistory.length - 1].normalized_modal_price : forecastPoints[0].q50;
    const topPts = [`${originX},${getY(lastHistPrice)}`];
    const bottomPts = [`${originX},${getY(lastHistPrice)}`];

    forecastPoints.forEach((fp, i) => {
      const idx = sortedHistory.length + i;
      topPts.push(`${getX(idx)},${getY(fp.q90)}`);
      bottomPts.push(`${getX(idx)},${getY(fp.q10)}`);
    });

    return `M ${topPts.join(" L ")} L ${bottomPts.reverse().join(" L ")} Z`;
  }, [forecastPoints, sortedHistory, originX, getX, getY]);

  // Forecast 60% corridor (P20 to P80)
  const corridor60Path = useMemo(() => {
    if (forecastPoints.length === 0) return "";
    const lastHistPrice = sortedHistory.length > 0 ? sortedHistory[sortedHistory.length - 1].normalized_modal_price : forecastPoints[0].q50;
    const topPts = [`${originX},${getY(lastHistPrice)}`];
    const bottomPts = [`${originX},${getY(lastHistPrice)}`];

    forecastPoints.forEach((fp, i) => {
      const idx = sortedHistory.length + i;
      topPts.push(`${getX(idx)},${getY(fp.q80)}`);
      bottomPts.push(`${getX(idx)},${getY(fp.q20)}`);
    });

    return `M ${topPts.join(" L ")} L ${bottomPts.reverse().join(" L ")} Z`;
  }, [forecastPoints, sortedHistory, originX, getX, getY]);

  // Y-axis ticks
  const yTicks = useMemo(() => {
    const count = 5;
    const step = priceRange / (count - 1);
    return Array.from({ length: count }, (_, i) => minPrice + i * step);
  }, [minPrice, priceRange]);

  const activeData = useMemo(() => {
    if (!hoveredStep) return null;
    if (hoveredStep.type === "history") {
      const obs = sortedHistory[hoveredStep.index];
      if (!obs) return null;
      return {
        type: "history" as const,
        date: obs.record_date,
        price: obs.normalized_modal_price,
        min: obs.normalized_min_price,
        max: obs.normalized_max_price,
        arrival: obs.arrival_tonnes,
      };
    } else {
      const fp = forecastPoints[hoveredStep.index];
      if (!fp) return null;
      return {
        type: "forecast" as const,
        date: fp.date,
        median: fp.q50,
        q10: fp.q10,
        q20: fp.q20,
        q80: fp.q80,
        q90: fp.q90,
      };
    }
  }, [hoveredStep, sortedHistory, forecastPoints]);

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 backdrop-blur-md shadow-xl">
      {/* Header & Meta */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-zinc-800/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-500 animate-pulse" />
            <h3 className="text-base font-bold text-zinc-100">
              Probabilistic Price Forecast — {commodityName}
            </h3>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Physical Origin ({originDate}) &bull; Mandi: {marketName} &bull; Engine:{" "}
            <span className="font-semibold text-purple-400">{modelName}</span>
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-3.5 h-0.5 bg-emerald-400 rounded-full" />
            <span>Historical Rate</span>
          </div>
          <div className="flex items-center gap-1.5 text-purple-400">
            <span className="w-3.5 h-0.5 bg-purple-400 border-b-2 border-dashed border-purple-400" />
            <span>P50 Median Forecast</span>
          </div>
          <div className="flex items-center gap-1.5 text-purple-300/80">
            <span className="w-3 h-3 rounded bg-purple-500/25 border border-purple-500/40" />
            <span>80% Prediction Corridor (P10–P90)</span>
          </div>
        </div>
      </div>

      {/* SVG Time Series Visualizer */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto select-none"
          style={{ minWidth: "600px" }}
        >
          {/* Horizontal Grid lines */}
          {yTicks.map((val, idx) => (
            <g key={idx} className="text-zinc-800">
              <line
                x1={padding.left}
                y1={getY(val)}
                x2={width - padding.right}
                y2={getY(val)}
                stroke="currentColor"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
              <text
                x={padding.left - 10}
                y={getY(val) + 4}
                fill="#71717a"
                fontSize="11"
                textAnchor="end"
                fontFamily="monospace"
              >
                ₹{val.toFixed(0)}
              </text>
            </g>
          ))}

          {/* 80% Corridor (P10 - P90) */}
          <path d={corridor80Path} fill="rgba(168, 85, 247, 0.12)" />

          {/* 60% Corridor (P20 - P80) */}
          <path d={corridor60Path} fill="rgba(168, 85, 247, 0.22)" />

          {/* Origin Vertical Separator */}
          <line
            x1={originX}
            y1={padding.top}
            x2={originX}
            y2={padding.top + innerHeight}
            stroke="#a855f7"
            strokeWidth="1.5"
            strokeDasharray="3 3"
          />
          <text
            x={originX}
            y={padding.top - 6}
            fill="#c084fc"
            fontSize="10"
            textAnchor="middle"
            fontWeight="bold"
          >
            Origin ({originDate})
          </text>

          {/* Historical Observations Line */}
          <path
            d={historyPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Forecast Line (Dashed) */}
          <path
            d={forecastPath}
            fill="none"
            stroke="#c084fc"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Historical Interactive Points */}
          {sortedHistory.map((d, i) => (
            <circle
              key={`h-${i}`}
              cx={getX(i)}
              cy={getY(d.normalized_modal_price)}
              r={hoveredStep?.type === "history" && hoveredStep.index === i ? 5.5 : 3}
              fill={hoveredStep?.type === "history" && hoveredStep.index === i ? "#34d399" : "#10b981"}
              stroke="#09090b"
              strokeWidth="2"
              className="cursor-pointer transition-all duration-150"
              onMouseEnter={() => setHoveredStep({ type: "history", index: i })}
              onMouseLeave={() => setHoveredStep(null)}
            />
          ))}

          {/* Forecast Interactive Points */}
          {forecastPoints.map((fp, i) => {
            const idx = sortedHistory.length + i;
            const isHovered = hoveredStep?.type === "forecast" && hoveredStep.index === i;
            return (
              <g key={`f-${i}`}>
                {/* Vertical spread bar P10 - P90 */}
                <line
                  x1={getX(idx)}
                  y1={getY(fp.q10)}
                  x2={getX(idx)}
                  y2={getY(fp.q90)}
                  stroke="#a855f7"
                  strokeWidth={isHovered ? 2.5 : 1.5}
                  strokeOpacity={isHovered ? 0.9 : 0.6}
                />
                {/* Median dot */}
                <circle
                  cx={getX(idx)}
                  cy={getY(fp.q50)}
                  r={isHovered ? 5.5 : 3.5}
                  fill={isHovered ? "#f472b6" : "#c084fc"}
                  stroke="#09090b"
                  strokeWidth="2"
                  className="cursor-pointer transition-all duration-150"
                  onMouseEnter={() => setHoveredStep({ type: "forecast", index: i })}
                  onMouseLeave={() => setHoveredStep(null)}
                />
              </g>
            );
          })}
        </svg>
      </div>

      {/* Hover Information Display */}
      <div className="mt-3 min-h-[50px] p-3 rounded-xl bg-zinc-950/80 border border-zinc-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        {activeData ? (
          activeData.type === "history" ? (
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <span className="text-zinc-500 font-mono">Date: </span>
                <span className="font-semibold text-zinc-200">{activeData.date}</span>
              </div>
              <div>
                <span className="text-zinc-500">Actual Modal: </span>
                <span className="font-bold text-emerald-400 font-mono">₹{activeData.price.toFixed(2)}/kg</span>
              </div>
              <div>
                <span className="text-zinc-500">Day Range: </span>
                <span className="text-zinc-300 font-mono">₹{activeData.min.toFixed(2)} – ₹{activeData.max.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-zinc-500">Arrival: </span>
                <span className="text-zinc-300 font-mono">{activeData.arrival.toFixed(1)} T</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <span className="text-zinc-500 font-mono">Forecast Date: </span>
                <span className="font-semibold text-purple-300">{activeData.date}</span>
              </div>
              <div>
                <span className="text-zinc-500">Median (P50): </span>
                <span className="font-bold text-purple-400 font-mono text-sm">₹{activeData.median.toFixed(2)}/kg</span>
              </div>
              <div>
                <span className="text-zinc-500">80% Corridor: </span>
                <span className="text-zinc-300 font-mono">[P10: ₹{activeData.q10.toFixed(2)} – P90: ₹{activeData.q90.toFixed(2)}]</span>
              </div>
              <div>
                <span className="text-zinc-500">60% Corridor: </span>
                <span className="text-zinc-300 font-mono">[P20: ₹{activeData.q20.toFixed(2)} – P80: ₹{activeData.q80.toFixed(2)}]</span>
              </div>
            </div>
          )
        ) : (
          <div className="text-zinc-500 flex items-center gap-2">
            <span className="text-sm">👆</span> Hover across historical points or forecast steps to inspect precise quantile values and uncertainty bands.
          </div>
        )}

        <div className="text-[11px] text-amber-400/90 font-medium px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20">
          ⚠️ Model forecast — not a guaranteed price.
        </div>
      </div>
    </div>
  );
};
