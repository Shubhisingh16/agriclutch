import React from "react";
import { Buyer } from "@/types/buyer";
import { BuyerProvenance } from "./BuyerProvenance";

interface BuyerTableProps {
  buyers: Buyer[];
  onSelectBuyerAudit: (buyer: Buyer) => void;
}

const TYPE_LABELS: Record<string, string> = {
  wholesaler: "Wholesaler (APMC)",
  processor: "Food Processor",
  retailer: "Retail Chain",
  aggregator: "FPO Aggregator",
  exporter: "Exporter",
  cooperative: "Cooperative (HAFED)",
};

export const BuyerTable: React.FC<BuyerTableProps> = ({ buyers, onSelectBuyerAudit }) => {
  if (buyers.length === 0) {
    return (
      <div className="p-8 text-center rounded-xl bg-zinc-900/30 border border-zinc-800 text-xs text-zinc-400 font-mono">
        No buyers matched the specified filter criteria.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
      <table className="w-full text-left text-xs text-zinc-300 font-sans">
        <thead className="bg-zinc-900/80 border-b border-zinc-800 text-[10px] font-mono uppercase text-zinc-400">
          <tr>
            <th className="py-3 px-4">Buyer Entity</th>
            <th className="py-3 px-4">Category</th>
            <th className="py-3 px-4">Procurement Hub</th>
            <th className="py-3 px-4">Data Provenance</th>
            <th className="py-3 px-4 text-right">Audit</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/60 font-mono text-[11px]">
          {buyers.map((buyer) => (
            <tr key={buyer.id} className="hover:bg-zinc-800/30 transition-colors">
              <td className="py-3.5 px-4">
                <div className="font-semibold text-white font-sans text-xs">{buyer.display_name}</div>
                <div className="text-[10px] text-zinc-400 font-mono mt-0.5">{buyer.id}</div>
              </td>
              <td className="py-3.5 px-4 font-sans text-xs">
                <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700 text-[11px]">
                  {TYPE_LABELS[buyer.buyer_type] || buyer.buyer_type}
                </span>
              </td>
              <td className="py-3.5 px-4">
                <div className="text-zinc-200">{buyer.location}</div>
                {buyer.latitude && buyer.longitude && (
                  <div className="text-[10px] text-zinc-400">
                    {buyer.latitude.toFixed(2)}°N, {buyer.longitude.toFixed(2)}°E
                  </div>
                )}
              </td>
              <td className="py-3.5 px-4">
                <BuyerProvenance
                  status={buyer.provenance_status}
                  isDemo={buyer.is_demo}
                  sourceName={buyer.source_name}
                  sourceReference={buyer.source_reference}
                />
              </td>
              <td className="py-3.5 px-4 text-right">
                <button
                  onClick={() => onSelectBuyerAudit(buyer)}
                  className="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-emerald-400 text-[11px] font-semibold border border-zinc-700 transition-colors"
                >
                  View Audit →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
