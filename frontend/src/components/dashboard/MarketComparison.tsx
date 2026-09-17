"use client";

import React from "react";
import { Market, PriceObservation } from "@/lib/api/types";

interface MarketComparisonProps {
  commodityName: string;
  referenceMarketId: string;
  markets: Market[];
  marketLatestPrices: Map<string, PriceObservation>;
  onSelectMarket: (marketId: string) => void;
}

export const MarketComparison: React.FC<MarketComparisonProps> = ({
  commodityName,
  referenceMarketId,
  markets,
  marketLatestPrices,
  onSelectMarket,
}) => {
  const refObservation = marketLatestPrices.get(referenceMarketId);
  const refPrice = refObservation?.normalized_modal_price ?? null;

  return (
    <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800/80 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/60 pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-white tracking-tight">
              Regional Mandi Price Dispersion
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/30">
              Cross-Market
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Comparative modal rates for {commodityName} across reporting APMC mandis
          </p>
        </div>

        {refObservation && (
          <div className="text-xs font-mono text-zinc-400">
            Baseline:{" "}
            <span className="text-emerald-400 font-semibold">
              ₹{refPrice?.toFixed(2)}/kg
            </span>{" "}
            ({markets.find((m) => m.id === referenceMarketId)?.name})
          </div>
        )}
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-zinc-800 text-[11px] text-zinc-500 uppercase tracking-wider">
              <th className="py-2.5 px-3">Mandi / District</th>
              <th className="py-2.5 px-3">State</th>
              <th className="py-2.5 px-3 text-right">Modal Rate</th>
              <th className="py-2.5 px-3 text-right">Source Rate</th>
              <th className="py-2.5 px-3 text-right">Arrivals</th>
              <th className="py-2.5 px-3 text-right">Trading Date</th>
              <th className="py-2.5 px-3 text-right">Delta vs Selected</th>
              <th className="py-2.5 px-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {markets.map((m) => {
              const obs = marketLatestPrices.get(m.id);
              const isSelected = m.id === referenceMarketId;
              const hasPrice = obs !== undefined;
              const currentPrice = obs?.normalized_modal_price ?? 0;
              const delta =
                refPrice !== null && hasPrice ? currentPrice - refPrice : null;
              const deltaPct =
                refPrice && delta !== null ? (delta / refPrice) * 100 : null;

              return (
                <tr
                  key={m.id}
                  className={`transition-colors ${
                    isSelected
                      ? "bg-emerald-500/10 text-white font-medium"
                      : "hover:bg-zinc-800/30 text-zinc-300"
                  }`}
                >
                  {/* Mandi Name & APMC Code */}
                  <td className="py-3 px-3">
                    <div className="flex items-center space-x-1.5">
                      <span className="font-semibold text-white">{m.name}</span>
                      {m.is_terminal_market && (
                        <span className="text-[9px] px-1 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                          T
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-zinc-500 mt-0.5">
                      {m.district} • APMC #{m.apmc_code}
                    </div>
                  </td>

                  {/* State */}
                  <td className="py-3 px-3 text-zinc-400">{m.state}</td>

                  {/* Modal Price */}
                  <td className="py-3 px-3 text-right">
                    {hasPrice ? (
                      <span className="font-bold text-white text-sm">
                        ₹{obs.normalized_modal_price.toFixed(2)}
                        <span className="text-[10px] text-zinc-500 font-normal">
                          /kg
                        </span>
                      </span>
                    ) : (
                      <span className="text-zinc-600">No data</span>
                    )}
                  </td>

                  {/* Source Rate */}
                  <td className="py-3 px-3 text-right text-zinc-400 text-[11px]">
                    {hasPrice
                      ? `₹${obs.original_modal_price.toLocaleString("en-IN")}`
                      : "—"}
                  </td>

                  {/* Arrivals */}
                  <td className="py-3 px-3 text-right text-zinc-400">
                    {hasPrice ? `${obs.arrival_tonnes} T` : "—"}
                  </td>

                  {/* Trading Date */}
                  <td className="py-3 px-3 text-right text-zinc-500 text-[10px]">
                    {hasPrice ? obs.record_date : "—"}
                  </td>

                  {/* Delta */}
                  <td className="py-3 px-3 text-right">
                    {isSelected ? (
                      <span className="text-zinc-500 text-[11px]">— Reference —</span>
                    ) : delta !== null ? (
                      <span
                        className={`font-semibold text-xs ${
                          delta > 0
                            ? "text-emerald-400"
                            : delta < 0
                            ? "text-rose-400"
                            : "text-zinc-400"
                        }`}
                      >
                        {delta > 0 ? `+₹${delta.toFixed(2)}` : `-₹${Math.abs(delta).toFixed(2)}`}{" "}
                        <span className="text-[10px] opacity-80">
                          ({delta > 0 ? "+" : ""}
                          {deltaPct?.toFixed(1)}%)
                        </span>
                      </span>
                    ) : (
                      <span className="text-zinc-600">—</span>
                    )}
                  </td>

                  {/* Action */}
                  <td className="py-3 px-3 text-center">
                    {!isSelected && (
                      <button
                        type="button"
                        onClick={() => onSelectMarket(m.id)}
                        className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-[10px] border border-zinc-700 transition-colors"
                      >
                        Select
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Disclaimers & Notes */}
      <div className="pt-2 border-t border-zinc-800/60 text-[10px] font-mono text-zinc-500">
        * Raw mandi price dispersion. Does not account for haulage freight, storage, or net
        realization deductions. See the Optimal Selling Plan module for net realizable value (NRV)
        calculations.
      </div>
    </div>
  );
};
