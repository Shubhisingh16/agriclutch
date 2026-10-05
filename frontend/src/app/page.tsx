"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Commodity, Market, PriceObservation } from "@/lib/api/types";
import { getCommodities } from "@/lib/api/commodities";
import { getMarkets } from "@/lib/api/markets";
import { getPrices } from "@/lib/api/prices";
import { CommoditySelector } from "@/components/dashboard/CommoditySelector";
import { MarketSelector } from "@/components/dashboard/MarketSelector";
import { MarketOverview } from "@/components/dashboard/MarketOverview";
import { PriceTrendChart } from "@/components/dashboard/PriceTrendChart";
import { MarketComparison } from "@/components/dashboard/MarketComparison";
import { DataQualityPanel } from "@/components/dashboard/DataQualityPanel";
import { MarketMap } from "@/components/dashboard/MarketMap";
import { ForecastCard } from "@/components/dashboard/ForecastCard";
import { NRVCard } from "@/components/dashboard/NRVCard";
import { BuyerIntelligencePanel } from "@/components/buyer/BuyerIntelligencePanel";
import { LogisticsPanel } from "@/components/logistics/LogisticsPanel";
import { StoragePanel } from "@/components/logistics/StoragePanel";
import { LoadingState, EmptyState, ErrorState } from "@/components/dashboard/StatusState";

interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  data_mode?: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [apiHealth, setApiHealth] = useState<SystemHealth | null>(null);
  const [dbStatus, setDbStatus] = useState<string>("probing");

  // Domain state
  const [commodities, setCommodities] = useState<Commodity[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [selectedCommodityId, setSelectedCommodityId] = useState<string | null>(null);
  const [selectedMarketId, setSelectedMarketId] = useState<string | null>(null);

  // Observations state
  const [prices, setPrices] = useState<PriceObservation[]>([]);
  const [allCommodityPrices, setAllCommodityPrices] = useState<PriceObservation[]>([]);
  const [dataSourceHeader, setDataSourceHeader] = useState<string | null>(null);
  const [dataMode, setDataMode] = useState<"DEMO" | "DATABASE" | null>(null);
  const [retrievedAt, setRetrievedAt] = useState<string | null>(null);

  // Status flags
  const [initLoading, setInitLoading] = useState<boolean>(true);
  const [pricesLoading, setPricesLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Initial master data fetch (Commodities + Mandis + System Probes)
  const initMasterData = useCallback(() => {
    setInitLoading(true);
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Health probes
    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then((data: SystemHealth) => {
        setApiHealth(data);
        if (data.data_mode?.toLowerCase() === "demo") {
          setDataMode("DEMO");
        } else if (data.data_mode?.toLowerCase() === "database") {
          setDataMode("DATABASE");
        }
      })
      .catch(() => {
        setApiHealth({
          status: "offline_fallback",
          service: "agriclutch-api",
          version: "0.1.0",
          environment: "demo_offline",
          data_mode: "demo",
        });
        setDataMode("DEMO");
      });

    fetch(`${apiUrl}/health/db`)
      .then((res) => {
        if (res.ok) setDbStatus("connected");
        else setDbStatus("standby_seed");
      })
      .catch(() => setDbStatus("standby_seed"));

    Promise.all([getCommodities(), getMarkets()])
      .then(([fetchedCommodities, fetchedMarkets]) => {
        setCommodities(fetchedCommodities);
        setMarkets(fetchedMarkets);

        if (fetchedCommodities.length > 0) {
          const defaultCrop =
            fetchedCommodities.find((c) => c.id === "tomato") || fetchedCommodities[0];
          setSelectedCommodityId(defaultCrop.id);
        }

        if (fetchedMarkets.length > 0) {
          const defaultMandi =
            fetchedMarkets.find((m) => m.id === "mandi_ch_49") || fetchedMarkets[0];
          setSelectedMarketId(defaultMandi.id);
        }
      })
      .catch((err: unknown) => {
        const msg =
          err instanceof Error ? err.message : "Failed to load master agricultural records.";
        setError(msg);
      })
      .finally(() => {
        setInitLoading(false);
      });
  }, []);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Health probes
    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then((data: SystemHealth) => {
        setApiHealth(data);
        if (data.data_mode?.toLowerCase() === "demo") {
          setDataMode("DEMO");
        } else if (data.data_mode?.toLowerCase() === "database") {
          setDataMode("DATABASE");
        }
      })
      .catch(() => {
        setApiHealth({
          status: "offline_fallback",
          service: "agriclutch-api",
          version: "0.1.0",
          environment: "demo_offline",
          data_mode: "demo",
        });
        setDataMode("DEMO");
      });

    fetch(`${apiUrl}/health/db`)
      .then((res) => {
        if (res.ok) setDbStatus("connected");
        else setDbStatus("standby_seed");
      })
      .catch(() => setDbStatus("standby_seed"));

    let isCancelled = false;

    Promise.all([getCommodities(), getMarkets()])
      .then(([fetchedCommodities, fetchedMarkets]) => {
        if (isCancelled) return;
        setCommodities(fetchedCommodities);
        setMarkets(fetchedMarkets);

        if (fetchedCommodities.length > 0) {
          const defaultCrop =
            fetchedCommodities.find((c) => c.id === "tomato") || fetchedCommodities[0];
          setSelectedCommodityId(defaultCrop.id);
        }

        if (fetchedMarkets.length > 0) {
          const defaultMandi =
            fetchedMarkets.find((m) => m.id === "mandi_ch_49") || fetchedMarkets[0];
          setSelectedMarketId(defaultMandi.id);
        }
      })
      .catch((err: unknown) => {
        if (isCancelled) return;
        const msg =
          err instanceof Error ? err.message : "Failed to load master agricultural records.";
        setError(msg);
      })
      .finally(() => {
        if (!isCancelled) {
          setInitLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  // 2. Fetch price observations when selected commodity or market changes
  useEffect(() => {
    if (!selectedCommodityId || !selectedMarketId) return;

    let isCancelled = false;

    const selectedReq = getPrices({
      commodity: selectedCommodityId,
      market: selectedMarketId,
      limit: 100,
    });

    const allReq = getPrices({
      commodity: selectedCommodityId,
      limit: 100,
    });

    Promise.all([selectedReq, allReq])
      .then(([selectedRes, allRes]) => {
        if (isCancelled) return;
        setPrices(selectedRes.data);
        setAllCommodityPrices(allRes.data);
        setDataSourceHeader(selectedRes.dataSource || allRes.dataSource);
        const resolvedMode = selectedRes.dataMode || allRes.dataMode;
        if (resolvedMode) {
          setDataMode(resolvedMode);
        }
        setRetrievedAt(selectedRes.retrievedAt);
      })
      .catch((err: unknown) => {
        if (isCancelled) return;
        console.error("Failed to load price observations:", err);
      })
      .finally(() => {
        if (!isCancelled) {
          setPricesLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [selectedCommodityId, selectedMarketId]);

  // Derived entities
  const activeCommodity = useMemo(
    () => commodities.find((c) => c.id === selectedCommodityId) || null,
    [commodities, selectedCommodityId]
  );

  const activeMarket = useMemo(
    () => markets.find((m) => m.id === selectedMarketId) || null,
    [markets, selectedMarketId]
  );

  // Latest observation for the selected commodity & market
  const latestObservation = useMemo(() => {
    if (prices.length === 0) return null;
    return [...prices].sort(
      (a, b) => new Date(b.record_date).getTime() - new Date(a.record_date).getTime()
    )[0];
  }, [prices]);

  // Map of market ID -> latest price observation for selected commodity
  const marketLatestPrices = useMemo(() => {
    const map = new Map<string, PriceObservation>();
    // Group by market_id and keep newest observation
    for (const obs of allCommodityPrices) {
      const existing = map.get(obs.market_id);
      if (
        !existing ||
        new Date(obs.record_date).getTime() > new Date(existing.record_date).getTime()
      ) {
        map.set(obs.market_id, obs);
      }
    }
    return map;
  }, [allCommodityPrices]);

  // Canonical data mode distinction
  const isDemoMode = useMemo(() => {
    if (dataMode === "DEMO") return true;
    if (dataSourceHeader === "SYNTHETIC_TEST_FIXTURE" || dataSourceHeader === "DEMO_BENCHMARK_SEED") return true;
    if (prices.some((p) => p.source_name.toUpperCase().includes("SYNTHETIC") || p.source_name.toUpperCase().includes("DEMO"))) return true;
    return false;
  }, [dataMode, dataSourceHeader, prices]);

  const navItems = [
    { id: "dashboard", label: "Market Intelligence", icon: "📊", badge: "Active" },
    { id: "forecast", label: "Price Forecast", icon: "🔮", badge: "P10/50/90" },
    { id: "nrv", label: "Net Realizable Value", icon: "💰", badge: "NRV Engine" },
    { id: "buyers", label: "Buyer Intelligence", icon: "🤝", badge: "Demand" },
    { id: "plan", label: "Optimal Selling Plan", icon: "🎯", badge: "Solver" },
    { id: "simulator", label: "What-If Simulator", icon: "🧪", badge: "Risk" },
    { id: "logistics", label: "Logistics & Routing", icon: "🚛", badge: "Freight" },
    { id: "storage", label: "Storage & Shelf-Life", icon: "❄️", badge: "Decay" },
    { id: "fpo", label: "FPO Aggregation", icon: "👥", badge: "Bulk" },
    { id: "observatory", label: "Model Observatory", icon: "🔭", badge: "Audit" },
  ];

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-72 border-r border-zinc-800/80 bg-zinc-900/50 flex flex-col shrink-0">
        {/* Brand Header */}
        <div className="p-5 border-b border-zinc-800/80">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-black text-xl text-zinc-950 shadow-lg shadow-emerald-500/20">
              ⚡
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-white">AgriClutch</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  v0.1.0
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 font-medium leading-none mt-1">
                Market Intelligence & Selling Optimization
              </p>
            </div>
          </div>
        </div>

        {/* Problem Statement Tag */}
        <div className="px-5 py-3 bg-zinc-900/80 border-b border-zinc-800/60">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-zinc-400">PROBLEM STATEMENT</span>
            <span className="text-emerald-400 font-semibold">SIH26132</span>
          </div>
          <p className="text-[11px] text-zinc-400 mt-1">
            Strengthening Market Linkages & Price Discovery for Farmers
          </p>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <div className="px-3 py-1.5 text-[10px] font-mono tracking-wider uppercase text-zinc-400">
            Platform Modules
          </div>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <span className="text-base">{item.icon}</span>
                  <span className="truncate">{item.label}</span>
                </div>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                    isActive
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {item.badge}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Sidebar System Readiness Footer */}
        <div className="p-4 border-t border-zinc-800/80 bg-zinc-900/40 text-xs font-mono space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-zinc-400">API Service:</span>
            <span
              className={`font-semibold ${
                apiHealth?.status === "ok" ? "text-emerald-400" : "text-amber-400"
              }`}
            >
              {apiHealth ? apiHealth.status : "Connecting..."}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-zinc-400">Database:</span>
            <span
              className={`font-semibold ${
                dbStatus === "connected"
                  ? "text-emerald-400"
                  : "text-amber-400"
              }`}
            >
              {dbStatus}
            </span>
          </div>
          <div className="pt-2 border-t border-zinc-800/60 flex items-center space-x-1.5 text-[10px] text-zinc-400">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Clean-Room Data Contract</span>
          </div>
        </div>
      </aside>

      {/* Main Operational Canvas */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Intelligence Bar */}
        <header className="h-16 border-b border-zinc-800/80 bg-zinc-900/30 px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="text-zinc-400">ACTIVE COMMODITY:</span>
              <span className="px-2.5 py-1 rounded bg-zinc-800 text-emerald-400 font-semibold border border-zinc-700">
                {activeCommodity ? `${activeCommodity.name} (${activeCommodity.hindi_name || ""})` : "Selecting..."}
              </span>
            </div>
            <div className="hidden sm:flex items-center space-x-2 text-xs font-mono">
              <span className="text-zinc-500">MANDI:</span>
              <span className="px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-300 border border-zinc-700">
                {activeMarket ? activeMarket.name : "..."}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full font-mono text-xs border ${
                isDemoMode
                  ? "bg-amber-500/10 border-amber-500/40 text-amber-400"
                  : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${isDemoMode ? "bg-amber-400" : "bg-emerald-400"}`} />
              <span>
                {isDemoMode
                  ? "DEMO DATA — Synthetic test fixture"
                  : "Historical APMC Records"}
              </span>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium border border-zinc-700 transition-colors"
            >
              API Docs ↗
            </a>
          </div>
        </header>

        {/* Content Body */}
        <div className="p-8 max-w-7xl w-full mx-auto space-y-8">
          {/* Prominent Demo Mode vs Historical Database Disclosure Banner */}
          {isDemoMode ? (
            <div
              data-testid="demo-mode-banner"
              className="rounded-2xl border border-amber-500/50 bg-amber-500/10 p-5 shadow-lg backdrop-blur-sm"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start space-x-3.5">
                  <span className="text-2xl mt-0.5">⚠️</span>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-bold font-mono tracking-wide text-amber-300 uppercase">
                        DEMO DATA — Synthetic test fixture
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-200 border border-amber-500/30">
                        OFFLINE DEMO
                      </span>
                    </div>
                    <p className="text-xs text-amber-200/90 font-sans mt-1 max-w-3xl leading-relaxed">
                      These values are synthetic test observations used for offline benchmarking and interface testing.
                      They do not represent current, live, or empirical agricultural market transactions.
                    </p>
                  </div>
                </div>
                <div className="shrink-0 flex flex-col sm:items-end text-right font-mono text-[11px] text-amber-400 bg-amber-950/40 p-2.5 rounded-xl border border-amber-500/20">
                  <div>
                    Fixture Loaded:{" "}
                    <span className="font-semibold text-white">
                      {retrievedAt ? new Date(retrievedAt).toLocaleTimeString("en-IN") : "Active"}
                    </span>
                  </div>
                  <div className="text-[10px] text-amber-300/70 mt-0.5">Demo Freshness (Client Time)</div>
                </div>
              </div>
            </div>
          ) : (
            <div
              data-testid="database-mode-banner"
              className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-4 shadow-lg backdrop-blur-sm"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">🏛️</span>
                  <div>
                    <div className="font-bold text-emerald-300">
                      Historical APMC Mandi Records
                    </div>
                    <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                      Archival empirical records from PostgreSQL / TimescaleDB agricultural database.
                    </p>
                  </div>
                </div>
                {latestObservation && (
                  <div className="shrink-0 text-right text-[11px] text-zinc-400 bg-zinc-900/60 p-2 rounded-lg border border-zinc-800">
                    <div>
                      Session Date:{" "}
                      <span className="font-semibold text-emerald-400">
                        {latestObservation.record_date}
                      </span>
                    </div>
                    <div className="text-[10px] text-zinc-500 mt-0.5">Empirical Trading Freshness</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* North Star Proposition Banner */}
          <div className="rounded-2xl bg-gradient-to-br from-zinc-900 via-zinc-900/90 to-emerald-950/30 border border-zinc-800/90 p-7 shadow-xl">
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 uppercase tracking-wider mb-2">
              <span>Decision Support Engine</span>
              <span>•</span>
              <span>SIH26132</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl max-w-4xl leading-snug">
              &ldquo;Given my crop, quantity, quality, location, storage capacity, liquidity requirement and risk preference, what is the optimal way to sell my produce?&rdquo;
            </h1>
            <div className="mt-4 inline-flex items-center space-x-3 px-3.5 py-1.5 rounded-lg bg-zinc-950/80 border border-zinc-800 text-xs font-mono text-zinc-300">
              <span className="text-emerald-400 font-semibold">Optimal Plan</span>
              <span>=</span>
              <span className="text-zinc-400">f(Crop, Quantity, Quality, Location, Storage, Liquidity, Risk)</span>
            </div>
          </div>

          {/* Error / Loading Handlers */}
          {initLoading ? (
            <LoadingState message="Loading agricultural master commodities and APMC mandis..." />
          ) : error ? (
            <ErrorState message={error} onRetry={initMasterData} />
          ) : commodities.length === 0 ? (
            <EmptyState
              title="No Commodities Available"
              message="No agricultural produce registered in database or seed repository."
            />
          ) : (
            <>
              {/* Dynamic Selectors Section */}
              <div className="grid grid-cols-1 gap-6 p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80">
                <CommoditySelector
                  commodities={commodities}
                  selectedCommodityId={selectedCommodityId}
                  onSelectCommodity={(id) => setSelectedCommodityId(id)}
                  disabled={pricesLoading}
                />

                <div className="pt-4 border-t border-zinc-800/60">
                  <MarketSelector
                    markets={markets}
                    selectedMarketId={selectedMarketId}
                    onSelectMarket={(id) => setSelectedMarketId(id)}
                    disabled={pricesLoading}
                  />
                </div>
              </div>

              {/* Conditional Tab Rendering */}
              {activeTab === "nrv" ? (
                <div className="space-y-6">
                  <NRVCard
                    selectedCrop={activeCommodity?.name || "Tomato"}
                    selectedMarketId={selectedMarketId || "chandigarh_grain"}
                  />
                </div>
              ) : activeTab === "forecast" ? (
                <div className="space-y-6">
                  <ForecastCard
                    commodityId={selectedCommodityId || "tomato"}
                    commodityName={activeCommodity?.name || "Tomato"}
                    marketId={selectedMarketId || "mandi_ch_49"}
                    marketName={activeMarket?.name || "Chandigarh (APMC)"}
                    historicalObservations={prices}
                  />
                </div>
              ) : activeTab === "buyers" ? (
                <div className="space-y-6">
                  <BuyerIntelligencePanel
                    selectedCommodityId={selectedCommodityId || "tomato"}
                  />
                </div>
              ) : activeTab === "logistics" ? (
                <div className="space-y-6">
                  <LogisticsPanel
                    selectedCommodityId={selectedCommodityId || "tomato"}
                  />
                </div>
              ) : activeTab === "storage" ? (
                <div className="space-y-6">
                  <StoragePanel
                    selectedCommodityId={selectedCommodityId || "tomato"}
                  />
                </div>
              ) : activeTab === "dashboard" ? (
                <>
                  {/* Main Market Overview Hero Card */}
                  {pricesLoading ? (
                    <LoadingState message="Fetching daily trading session observations..." />
                  ) : (
                    <MarketOverview
                      commodity={activeCommodity}
                      market={activeMarket}
                      latestObservation={latestObservation}
                      dataSourceHeader={dataSourceHeader}
                      dataMode={dataMode}
                      retrievedAt={retrievedAt}
                    />
                  )}

                  {/* Historical Price Trend Chart */}
                  <PriceTrendChart
                    observations={prices}
                    commodityName={activeCommodity?.name || "Commodity"}
                    marketName={activeMarket?.name || "Market"}
                  />

                  {/* Regional Cross-Market Price Dispersion */}
                  <MarketComparison
                    commodityName={activeCommodity?.name || "Commodity"}
                    referenceMarketId={selectedMarketId || ""}
                    markets={markets}
                    marketLatestPrices={marketLatestPrices}
                    onSelectMarket={(id) => setSelectedMarketId(id)}
                  />

                  {/* Regional Geospatial Corridor Map */}
                  <MarketMap
                    markets={markets}
                    selectedMarketId={selectedMarketId}
                    marketLatestPrices={marketLatestPrices}
                    onSelectMarket={(id) => setSelectedMarketId(id)}
                  />

                  {/* Data Quality & Audit Provenance Panel */}
                  <DataQualityPanel
                    observation={latestObservation}
                    dataSourceHeader={dataSourceHeader}
                    dataMode={dataMode}
                  />
                </>
              ) : (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-10 text-center space-y-3">
                  <div className="text-3xl">⚙️</div>
                  <h3 className="text-base font-bold text-zinc-200">
                    {navItems.find((n) => n.id === activeTab)?.label || "Module"} — Roadmap Pipeline
                  </h3>
                  <p className="text-xs text-zinc-400 max-w-md mx-auto">
                    This subsystem is scheduled for activation in upcoming implementation stages per PRODUCT_SPEC.md.
                  </p>
                </div>
              )}
            </>
          )}

          {/* Regional Benchmark Mandis Bar */}
          <div className="p-5 rounded-xl bg-zinc-900/30 border border-zinc-800/70 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-xs font-mono text-zinc-400">BENCHMARK DEMO MANDI NETWORK:</div>
              <div className="text-sm font-semibold text-zinc-200 mt-1">
                Chandigarh APMC • Panchkula (Haryana) • Kalka (Haryana) • Patiala (Punjab) • Azadpur (Delhi Terminal)
              </div>
            </div>
            <div className="text-xs font-mono text-zinc-400 text-right">
              <div>Seed Records: 10-Year Daily Series (2014–2024)</div>
              <div className="text-emerald-400 font-medium mt-0.5">Clean-Room Benchmark Fixtures</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
