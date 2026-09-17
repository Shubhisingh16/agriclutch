"use client";

import React from "react";
import { SensitivityResponse } from "@/lib/api/types";

interface SensitivityMatrixProps {
  sensitivity: SensitivityResponse;
  onVariableChange?: (vx: string, vy: string) => void;
}

export const SensitivityMatrix: React.FC<SensitivityMatrixProps> = ({
  sensitivity,
  onVariableChange,
}) => {
  const getVariableName = (v: string) => {
    switch (v.toLowerCase()) {
      case "price":
        return "Market Quoted Price";
      case "transport":
        return "Freight / Transport Cost";
      case "storage":
        return "Storage Holding Rate";
      case "loss":
        return "Spoilage / Decay Rate";
      default:
        return v;
    }
  };

  // Base NRV is typically the center cell (index [1][1] for 3x3)
  const baseNRV =
    sensitivity.grid_nrv_p50.length > 1 && sensitivity.grid_nrv_p50[1].length > 1
      ? sensitivity.grid_nrv_p50[1][1]
      : sensitivity.grid_nrv_p50[0]?.[0] || 0;

  return (
    <div className="space-y-6">
      {/* Controls / Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">
            2D Orthogonal Sensitivity Matrix
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Evaluating Net Realizable Value robustness across {getVariableName(sensitivity.variable_x)} (rows) vs{" "}
            {getVariableName(sensitivity.variable_y)} (columns).
          </p>
        </div>

        <div className="flex items-center gap-3">
          {onVariableChange && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-zinc-400 font-mono">Axis X:</span>
              <select
                value={sensitivity.variable_x}
                onChange={(e) => onVariableChange(e.target.value, sensitivity.variable_y)}
                className="bg-zinc-800 text-white rounded px-2 py-1 border border-zinc-700 font-mono text-xs"
              >
                <option value="price">Price</option>
                <option value="transport">Transport</option>
                <option value="storage">Storage</option>
                <option value="loss">Loss Rate</option>
              </select>

              <span className="text-zinc-400 font-mono ml-2">Axis Y:</span>
              <select
                value={sensitivity.variable_y}
                onChange={(e) => onVariableChange(sensitivity.variable_x, e.target.value)}
                className="bg-zinc-800 text-white rounded px-2 py-1 border border-zinc-700 font-mono text-xs"
              >
                <option value="transport">Transport</option>
                <option value="price">Price</option>
                <option value="storage">Storage</option>
                <option value="loss">Loss Rate</option>
              </select>
            </div>
          )}

          {sensitivity.provenance?.is_demo && (
            <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
              DEMO ASSUMPTION
            </span>
          )}
        </div>
      </div>

      {/* 3x3 Matrix Grid Table */}
      <div className="rounded-xl border border-zinc-800 overflow-hidden bg-zinc-900/30">
        <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 flex justify-between items-center">
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
            Net Realizable Value Matrix (₹)
          </div>
          <div className="text-[11px] text-zinc-400 font-mono">
            Baseline NRV:{" "}
            <span className="font-bold text-white">
              ₹{baseNRV.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
            </span>
          </div>
        </div>

        <div className="p-4 overflow-x-auto">
          <table className="w-full text-center border-collapse text-xs">
            <thead>
              <tr>
                <th className="p-3 text-left font-mono text-zinc-400 border border-zinc-800 bg-zinc-900/50">
                  <div className="text-[11px] text-zinc-500">Row: {getVariableName(sensitivity.variable_x)}</div>
                  <div className="text-[11px] text-zinc-500">Col: {getVariableName(sensitivity.variable_y)}</div>
                </th>
                {sensitivity.levels_y.map((lvlY, j) => (
                  <th
                    key={`${lvlY}-${j}`}
                    className="p-3 font-mono border border-zinc-800 bg-zinc-900/60 text-zinc-300 font-semibold"
                  >
                    <div>{getVariableName(sensitivity.variable_y)}</div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">{lvlY}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sensitivity.grid_nrv_p50.map((row, i) => {
                const lvlX = sensitivity.levels_x[i] || `Level ${i}`;
                return (
                  <tr key={`${lvlX}-${i}`}>
                    <td className="p-3 text-left font-mono border border-zinc-800 bg-zinc-900/60 text-zinc-300 font-semibold">
                      <div>{getVariableName(sensitivity.variable_x)}</div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">{lvlX}</div>
                    </td>
                    {row.map((cellNrv, j) => {
                      const deltaFromBase = cellNrv - baseNRV;
                      const cellPerKg = sensitivity.grid_nrv_per_kg[i]?.[j] ?? 0;
                      const isCenter = i === 1 && j === 1;

                      return (
                        <td
                          key={j}
                          className={`p-4 border border-zinc-800 transition-colors ${
                            isCenter
                              ? "bg-zinc-800/60 ring-2 ring-emerald-500/40"
                              : deltaFromBase >= 0
                              ? "bg-emerald-950/20 hover:bg-emerald-950/30"
                              : "bg-rose-950/20 hover:bg-rose-950/30"
                          }`}
                        >
                          <div className="font-mono font-bold text-sm text-white">
                            ₹{cellNrv.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                          </div>
                          <div className="font-mono text-xs text-zinc-400 mt-0.5">
                            ₹{cellPerKg.toFixed(2)}/kg
                          </div>
                          <div
                            className={`font-mono text-[10px] mt-1 ${
                              isCenter
                                ? "text-zinc-400 font-semibold"
                                : deltaFromBase >= 0
                                ? "text-emerald-400 font-semibold"
                                : "text-rose-400 font-semibold"
                            }`}
                          >
                            {isCenter
                              ? "[Baseline]"
                              : `${deltaFromBase >= 0 ? "+" : ""}₹${deltaFromBase.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 font-mono">
        ℹ️ <span className="font-semibold text-zinc-300">Disclaimer:</span> {sensitivity.disclaimer}
      </div>
    </div>
  );
};
