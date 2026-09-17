"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  NRVResponse,
  NRVMarketComparisonResponse,
  NRVTimeComparisonResponse,
  SensitivityResponse,
  EconomicAssumptionsResponse,
} from "@/lib/api/types";
import {
  getNRV,
  compareMarketNRV,
  compareTimeNRV,
  getNRVSensitivity,
  getEconomicAssumptions,
} from "@/lib/api/nrv";
import { NRVDistributionChart } from "./NRVDistributionChart";
import { CostBreakdown } from "./CostBreakdown";
import { MarketNRVComparison } from "./MarketNRVComparison";
import { TimeScenarioComparison } from "./TimeScenarioComparison";
import { SensitivityMatrix } from "./SensitivityMatrix";
import { AssumptionProvenance } from "./AssumptionProvenance";

interface NRVCardProps {
  selectedCrop?: string;
  selectedMarketId?: string;
}

export const NRVCard: React.FC<NRVCardProps> = ({
  selectedCrop = "Tomato",
  selectedMarketId = "chandigarh_grain",
}) => {
  // Input parameters
  const [crop, setCrop] = useState<string>(selectedCrop);
  const [marketId, setMarketId] = useState<string>(selectedMarketId);
  const [quantityValue, setQuantityValue] = useState<number>(50);
  const [quantityUnit, setQuantityUnit] = useState<string>("quintal");
  const [holdingDays, setHoldingDays] = useState<number>(0);
  const [storageType, setStorageType] = useState<string>("AMBIENT");
  const [qualityGrade, setQualityGrade] = useState<string>("GRADE_A");
  const [riskStance, setRiskStance] = useState<string>("EXPECTED");

  // Sub-tab selection
  const [activeSubTab, setActiveSubTab] = useState<
    "overview" | "breakdown" | "markets" | "times" | "sensitivity" | "assumptions"
  >("overview");

  // Data states
  const [nrvData, setNrvData] = useState<NRVResponse | null>(null);
  const [marketComparison, setMarketComparison] = useState<NRVMarketComparisonResponse | null>(null);
  const [timeComparison, setTimeComparison] = useState<NRVTimeComparisonResponse | null>(null);
  const [sensitivityData, setSensitivityData] = useState<SensitivityResponse | null>(null);
  const [assumptionsData, setAssumptionsData] = useState<EconomicAssumptionsResponse | null>(null);

  // Sensitivity axes
  const [sensVar1, setSensVar1] = useState<string>("price");
  const [sensVar2, setSensVar2] = useState<string>("transport");

  // Refresh trigger for retries
  const [refreshKey, setRefreshKey] = useState<number>(0);

  // Async states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Mandi options
  const markets = [
    { id: "chandigarh_grain", name: "Chandigarh (Grain)" },
    { id: "panchkula", name: "Panchkula" },
    { id: "kalka", name: "Kalka" },
    { id: "patiala", name: "Patiala" },
    { id: "azadpur", name: "Azadpur (Delhi)" },
  ];

  // Fetch NRV and auxiliary scenario data whenever parameters change
  useEffect(() => {
    let active = true;

    async function executeFetch() {
      try {
        const commodityId = crop.toLowerCase();

        // Primary NRV calculation
        const primaryRes = await getNRV({
          commodity_id: commodityId,
          market_id: marketId,
          quantity: quantityValue,
          unit: quantityUnit,
          storage_days: holdingDays,
          storage_type: storageType,
          quality_grade: qualityGrade,
          scenario_type: riskStance.toLowerCase(),
        });
        if (!active) return;
        setNrvData(primaryRes);
        setError(null);

        // Async fetch auxiliary scenario data based on active tab
        if (activeSubTab === "markets") {
          const mComp = await compareMarketNRV({
            commodity_id: commodityId,
            quantity: quantityValue,
            unit: quantityUnit,
            storage_days: holdingDays,
            storage_type: storageType,
            quality_grade: qualityGrade,
          });
          if (!active) return;
          setMarketComparison(mComp);
        } else if (activeSubTab === "times") {
          const tComp = await compareTimeNRV({
            commodity_id: commodityId,
            market_id: marketId,
            quantity: quantityValue,
            unit: quantityUnit,
            storage_type: storageType,
            quality_grade: qualityGrade,
          });
          if (!active) return;
          setTimeComparison(tComp);
        } else if (activeSubTab === "sensitivity") {
          const sMat = await getNRVSensitivity({
            commodity_id: commodityId,
            market_id: marketId,
            quantity: quantityValue,
            unit: quantityUnit,
            variable_x: sensVar1,
            variable_y: sensVar2,
            storage_days: holdingDays,
            storage_type: storageType,
            quality_grade: qualityGrade,
          });
          if (!active) return;
          setSensitivityData(sMat);
        } else if (activeSubTab === "assumptions") {
          const assump = await getEconomicAssumptions();
          if (!active) return;
          setAssumptionsData(assump);
        }
      } catch (err: unknown) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : "Failed to compute Net Realizable Value";
        setError(msg);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void executeFetch();

    return () => {
      active = false;
    };
  }, [
    crop,
    marketId,
    quantityValue,
    quantityUnit,
    holdingDays,
    storageType,
    qualityGrade,
    riskStance,
    activeSubTab,
    sensVar1,
    sensVar2,
    refreshKey,
  ]);

  const isDemo = nrvData?.provenance_items.some((p) => p.is_demo) ?? true;
  const grossP50 = nrvData?.gross_revenue_quantiles?.p50 ?? nrvData?.gross_revenue_quantiles?.["0.5"] ?? 0;
  const priceP50 = nrvData?.forecast_price_quantiles?.p50 ?? nrvData?.forecast_price_quantiles?.["0.5"] ?? 0;

  return (
    <div className="space-y-6">
      {/* Parameter Control Bar */}
      <div className="p-5 rounded-2xl bg-zinc-900/80 border border-zinc-800 shadow-lg space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>💰</span> Net Realizable Value (NRV) Engine
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Strict economic realization after freight, storage, handling, APMC cess, and decay loss.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
              STEP 11 VERIFIED
            </span>
            {isDemo && (
              <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
                DEMO ASSUMPTION
              </span>
            )}
          </div>
        </div>

        {/* Form Controls Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Commodity */}
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1">Commodity</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="Tomato">Tomato</option>
              <option value="Onion">Onion</option>
              <option value="Potato">Potato</option>
            </select>
          </div>

          {/* Mandi */}
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1">Target Mandi</label>
            <select
              value={marketId}
              onChange={(e) => setMarketId(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              {markets.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>

          {/* Quantity & Unit */}
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1">Quantity</label>
            <div className="flex gap-1">
              <input
                type="number"
                min="1"
                max="100000"
                value={quantityValue}
                onChange={(e) => setQuantityValue(Math.max(1, parseFloat(e.target.value) || 1))}
                className="w-2/3 bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
              />
              <select
                value={quantityUnit}
                onChange={(e) => setQuantityUnit(e.target.value)}
                className="w-1/3 bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
              >
                <option value="kg">kg</option>
                <option value="quintal">qtl</option>
                <option value="tonne">ton</option>
              </select>
            </div>
          </div>

          {/* Holding Days */}
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1">
              Holding (T+{holdingDays}d)
            </label>
            <select
              value={holdingDays}
              onChange={(e) => setHoldingDays(parseInt(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
            >
              <option value="0">0 days (Immediate)</option>
              <option value="3">3 days</option>
              <option value="7">7 days</option>
              <option value="14">14 days</option>
              <option value="28">28 days</option>
            </select>
          </div>

          {/* Storage Type */}
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1">Storage Type</label>
            <select
              value={storageType}
              onChange={(e) => setStorageType(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="AMBIENT">Ambient / Open</option>
              <option value="COLD_STORAGE">Cold Storage</option>
              <option value="ON_FARM_VENTILATED">On-Farm Ventilated</option>
              <option value="NONE">None</option>
            </select>
          </div>

          {/* Quality Grade */}
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 mb-1">Quality Grade</label>
            <select
              value={qualityGrade}
              onChange={(e) => setQualityGrade(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="GRADE_A">Grade A (100% FAQ)</option>
              <option value="GRADE_B">Grade B (90% FAQ)</option>
              <option value="GRADE_C">Grade C (75% FAQ)</option>
              <option value="REJECT">Reject (40% FAQ)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Sub-Tabs Navigation */}
      <div className="flex border-b border-zinc-800 gap-2 overflow-x-auto text-xs font-mono">
        {[
          { id: "overview", label: "📊 Overview & Spectrum" },
          { id: "breakdown", label: "🧾 Friction Deductions" },
          { id: "markets", label: "🌐 Market Comparison" },
          { id: "times", label: "⏳ Holding Trajectory" },
          { id: "sensitivity", label: "📉 2D Sensitivity Grid" },
          { id: "assumptions", label: "📜 Assumptions Audit" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id as typeof activeSubTab)}
            className={`px-4 py-2.5 font-medium transition-colors border-b-2 whitespace-nowrap ${
              activeSubTab === tab.id
                ? "text-emerald-400 border-emerald-500 bg-emerald-500/5"
                : "text-zinc-400 border-transparent hover:text-zinc-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading & Error States */}
      {loading && !nrvData && (
        <div className="p-12 text-center text-zinc-500 font-mono text-xs animate-pulse">
          Computing Net Realizable Value distributions across horizons...
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          <div className="font-semibold mb-1">Failed to calculate NRV:</div>
          <p className="font-mono">{error}</p>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="mt-3 px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 rounded font-mono text-xs transition-colors"
          >
            Retry Calculation
          </button>
        </div>
      )}

      {/* Main Tab Content */}
      {nrvData && !loading && (
        <div className="space-y-6">
          {/* Sub-Tab 1: Overview */}
          {activeSubTab === "overview" && (
            <div className="space-y-6">
              {/* Summary Metrics Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400">Gross Value (P50)</div>
                  <div className="text-lg font-bold text-white mt-1">
                    ₹{grossP50.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-500 mt-0.5">
                    Quoted: ₹{priceP50.toFixed(2)}/kg
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400">Total Deductions</div>
                  <div className="text-lg font-bold text-rose-400 mt-1">
                    -₹{nrvData.total_cost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-500 mt-0.5">
                    {grossP50 > 0 ? ((nrvData.total_cost / grossP50) * 100).toFixed(1) : "0.0"}% friction
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900/60 border border-emerald-500/30 bg-emerald-500/5">
                  <div className="text-[11px] font-mono text-emerald-400">Net Realizable (P50)</div>
                  <div className="text-lg font-bold text-emerald-300 mt-1">
                    ₹{nrvData.nrv_quantiles.p50.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-[11px] font-mono text-emerald-400 font-semibold mt-0.5">
                    ₹{nrvData.nrv_per_kg_quantiles.p50.toFixed(2)} / kg
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400">Break-Even Quoted</div>
                  <div className="text-lg font-bold text-amber-400 mt-1">
                    {nrvData.break_even.break_even_price !== null
                      ? `₹${nrvData.break_even.break_even_price.toFixed(2)}/kg`
                      : "N/A"}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-500 mt-0.5">
                    Zero-margin floor
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400">Effective Quantity</div>
                  <div className="text-lg font-bold text-zinc-200 mt-1">
                    {nrvData.loss.effective_quantity_kg.toFixed(0)} kg
                  </div>
                  <div className="text-[11px] font-mono text-zinc-500 mt-0.5">
                    Loss: {nrvData.loss.loss_rate_pct.toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Distribution Spectrum */}
              <NRVDistributionChart
                forecastQuantiles={nrvData.forecast_price_quantiles}
                grossRevenueQuantiles={nrvData.gross_revenue_quantiles}
                nrvQuantiles={nrvData.nrv_quantiles}
                nrvPerKgQuantiles={nrvData.nrv_per_kg_quantiles}
                totalCost={nrvData.total_cost}
              />

              {/* Compact Breakdown */}
              <CostBreakdown
                costBreakdown={nrvData.cost_breakdown}
                effectiveQuantityKg={nrvData.loss.effective_quantity_kg}
                initialQuantityKg={nrvData.quantity.normalized_quantity_kg}
              />
            </div>
          )}

          {/* Sub-Tab 2: Cost Breakdown */}
          {activeSubTab === "breakdown" && (
            <CostBreakdown
              costBreakdown={nrvData.cost_breakdown}
              effectiveQuantityKg={nrvData.loss.effective_quantity_kg}
              initialQuantityKg={nrvData.quantity.normalized_quantity_kg}
            />
          )}

          {/* Sub-Tab 3: Market Comparison */}
          {activeSubTab === "markets" && marketComparison && (
            <MarketNRVComparison comparison={marketComparison} />
          )}

          {/* Sub-Tab 4: Holding Trajectory */}
          {activeSubTab === "times" && timeComparison && (
            <TimeScenarioComparison comparison={timeComparison} />
          )}

          {/* Sub-Tab 5: Sensitivity */}
          {activeSubTab === "sensitivity" && sensitivityData && (
            <SensitivityMatrix
              sensitivity={sensitivityData}
              onVariableChange={(v1, v2) => {
                setSensVar1(v1);
                setSensVar2(v2);
              }}
            />
          )}

          {/* Sub-Tab 6: Assumptions */}
          {activeSubTab === "assumptions" && assumptionsData && (
            <AssumptionProvenance assumptions={assumptionsData} />
          )}

          {/* Disclaimer Footer */}
          <div className="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 font-mono">
            ℹ️ <span className="font-semibold text-zinc-300">Disclaimer:</span> {nrvData.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
