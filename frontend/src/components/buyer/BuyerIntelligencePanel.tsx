"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Buyer, CompatibilityMatch, FarmerSupply } from "@/types/buyer";
import { evaluateBuyerMatching, getBuyers, getSampleSupplies } from "@/lib/api/buyers";
import { CompatibilityPanel } from "./CompatibilityPanel";
import { DemandAggregationPanel } from "./DemandAggregationPanel";
import { BuyerSearchFilters } from "./BuyerSearchFilters";
import { BuyerTable } from "./BuyerTable";
import { BuyerReliabilityModal } from "./BuyerReliabilityModal";

interface BuyerIntelligencePanelProps {
  selectedCommodityId: string;
}

export const BuyerIntelligencePanel: React.FC<BuyerIntelligencePanelProps> = ({
  selectedCommodityId,
}) => {
  const [subTab, setSubTab] = useState<"matching" | "demand" | "directory">("matching");

  // Matching state
  const [sampleSupplies, setSampleSupplies] = useState<FarmerSupply[]>([]);
  const [currentSupply, setCurrentSupply] = useState<FarmerSupply | null>(null);
  const [matches, setMatches] = useState<CompatibilityMatch[]>([]);
  const [matchingLoading, setMatchingLoading] = useState<boolean>(false);

  // Directory filter state
  const [buyers, setBuyers] = useState<Buyer[]>([]);
  const [directoryLoading, setDirectoryLoading] = useState<boolean>(false);
  const [directoryError, setDirectoryError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [locationFilter, setLocationFilter] = useState<string>("");
  const [maxDistanceKm, setMaxDistanceKm] = useState<number | null>(null);

  // Audit modal state
  const [selectedAuditBuyer, setSelectedAuditBuyer] = useState<{ id: string; name: string } | null>(null);

  // 1. Fetch sample supplies and trigger matching on commodity change
  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const supplies = await getSampleSupplies(selectedCommodityId);
        if (!isMounted) return;
        setSampleSupplies(supplies);
        const initialSupply = supplies.length > 0 ? supplies[0] : null;
        setCurrentSupply(initialSupply);

        if (initialSupply) {
          const matchRes = await evaluateBuyerMatching(initialSupply);
          if (!isMounted) return;
          setMatches(matchRes.matches);
        } else {
          setMatches([]);
        }
      } catch {
        if (!isMounted) return;
        setMatches([]);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [selectedCommodityId]);

  // 2. Fetch buyers for directory
  const handleReloadBuyers = async () => {
    setDirectoryLoading(true);
    setDirectoryError(null);
    try {
      const data = await getBuyers({
        commodity_id: selectedCommodityId,
        buyer_type: selectedType === "ALL" ? undefined : selectedType,
        location: locationFilter || undefined,
      });
      setBuyers(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load buyer directory.";
      setDirectoryError(msg);
    } finally {
      setDirectoryLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const data = await getBuyers({
          commodity_id: selectedCommodityId,
          buyer_type: selectedType === "ALL" ? undefined : selectedType,
          location: locationFilter || undefined,
        });
        if (!isMounted) return;
        setBuyers(data);
        setDirectoryLoading(false);
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : "Failed to load buyer directory.";
        setDirectoryError(msg);
        setDirectoryLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [selectedCommodityId, selectedType, locationFilter]);

  // 3. User updates supply parameters
  const handleSupplyChange = async (newSupply: FarmerSupply) => {
    setCurrentSupply(newSupply);
    setMatchingLoading(true);
    try {
      const matchRes = await evaluateBuyerMatching(newSupply);
      setMatches(matchRes.matches);
    } catch {
      setMatches([]);
    } finally {
      setMatchingLoading(false);
    }
  };

  // 4. Handle audit trigger
  const handleSelectAudit = (buyerId: string, buyerName: string) => {
    setSelectedAuditBuyer({ id: buyerId, name: buyerName });
  };

  return (
    <div className="space-y-6">
      {/* Master Subsystem Header */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 uppercase tracking-wider mb-1">
              <span>Step 12</span>
              <span>•</span>
              <span>Buyer Matching & Demand Aggregation Engine</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Commercial Buyer Intelligence & Demand Depth
            </h1>
            <p className="text-xs text-zinc-400 mt-1 max-w-3xl leading-relaxed">
              Provides auditable buyer candidate matching, empirical transaction reliability audits,
              and regional demand depth across the Chandigarh-Punjab-Haryana-Delhi corridor.
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-zinc-950 p-1.5 rounded-xl border border-zinc-800 shrink-0 self-start md:self-auto">
            <button
              onClick={() => setSubTab("matching")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all ${
                subTab === "matching"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              🎯 Lot Matching
            </button>
            <button
              onClick={() => setSubTab("demand")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all ${
                subTab === "demand"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              📊 Regional Demand Depth
            </button>
            <button
              onClick={() => setSubTab("directory")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all ${
                subTab === "directory"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              🏢 Buyer Directory & Audits
            </button>
          </div>
        </div>

        {/* Strict Non-Normative Governance Notice */}
        <div className="mt-4 p-3.5 rounded-xl border border-zinc-800 bg-zinc-950/60 flex items-start space-x-3 text-xs text-zinc-400">
          <span className="text-emerald-400 text-sm mt-0.5 font-bold">ℹ️</span>
          <div className="leading-relaxed">
            <span className="font-semibold text-zinc-300 font-mono">NON-NORMATIVE DATA CONTRACT: </span>
            Step 12 evaluates strict physical, temporal, and spatial compatibility against registered procurement orders.
            This subsystem does not rank, select winners, or issue selling advice. All compatibility outputs serve as structured inputs for downstream decision optimization.
          </div>
        </div>
      </div>

      {/* Sub-tab views */}
      {subTab === "matching" && currentSupply && (
        <CompatibilityPanel
          matches={matches}
          supply={currentSupply}
          onChangeSupply={handleSupplyChange}
          onSelectBuyerAudit={handleSelectAudit}
          loading={matchingLoading}
          sampleSupplies={sampleSupplies}
        />
      )}

      {subTab === "demand" && (
        <DemandAggregationPanel commodityId={selectedCommodityId} />
      )}

      {subTab === "directory" && (
        <div className="space-y-6">
          <BuyerSearchFilters
            selectedType={selectedType}
            onSelectType={(type) => setSelectedType(type)}
            locationFilter={locationFilter}
            onChangeLocation={(loc) => setLocationFilter(loc)}
            maxDistanceKm={maxDistanceKm}
            onChangeMaxDistance={(dist) => setMaxDistanceKm(dist)}
          />

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-zinc-200">
                  Registered Buyer Profiles ({buyers.length})
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Demo entities representing retail, food processing, export, and wholesale archetypes.
                </p>
              </div>
            </div>

            {directoryError ? (
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-center space-y-2">
                <p className="text-xs font-mono text-rose-400 uppercase">Directory Retrieval Failure</p>
                <p className="text-sm text-zinc-300">{directoryError}</p>
                <button
                  onClick={handleReloadBuyers}
                  className="mt-2 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-xs font-medium text-white transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : directoryLoading ? (
              <div className="p-12 text-center space-y-2">
                <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                <p className="text-xs font-mono text-zinc-400">Loading demo buyer directory...</p>
              </div>
            ) : (
              <BuyerTable
                buyers={buyers}
                onSelectBuyerAudit={(buyer) => handleSelectAudit(buyer.id, buyer.display_name)}
              />
            )}
          </div>
        </div>
      )}

      {/* Empirical Reliability Audit Modal */}
      {selectedAuditBuyer && (
        <BuyerReliabilityModal
          buyerId={selectedAuditBuyer.id}
          buyerName={selectedAuditBuyer.name}
          onClose={() => setSelectedAuditBuyer(null)}
        />
      )}
    </div>
  );
};
