import React from "react";
import { ProvenanceStatus } from "@/types/buyer";

interface BuyerProvenanceProps {
  status: ProvenanceStatus;
  isDemo: boolean;
  sourceName?: string;
  sourceReference?: string | null;
  className?: string;
}

export const BuyerProvenance: React.FC<BuyerProvenanceProps> = ({
  status,
  isDemo,
  sourceName,
  sourceReference,
  className = "",
}) => {
  const isDemoStatus = isDemo || status === "DEMO";

  return (
    <div className={`inline-flex items-center space-x-1.5 text-xs font-mono ${className}`}>
      {isDemoStatus ? (
        <span
          data-testid="buyer-demo-badge"
          className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-semibold"
          title="Synthetic test fixture for demonstration and testing. Does not represent a live commercial purchase offer."
        >
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
          <span>DEMO BUYER DATA</span>
        </span>
      ) : status === "EMPIRICAL" ? (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          <span>AUDITED RECORD</span>
        </span>
      ) : (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700 text-[10px]">
          <span>{status}</span>
        </span>
      )}

      {sourceName && (
        <span className="text-[10px] text-zinc-400 hidden sm:inline" title={sourceReference || ""}>
          • {sourceName}
        </span>
      )}
    </div>
  );
};
