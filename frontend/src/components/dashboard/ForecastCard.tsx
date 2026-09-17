"use client";

import React, { useState, useEffect } from "react";
import {
  ForecastInsufficiency,
  ForecastResponse,
  ModelComparisonResponse,
  PriceObservation,
  RegisteredModelInfo,
} from "@/lib/api/types";
import { getForecast, getAvailableModels, getModelEvaluations } from "@/lib/api/forecasts";
import { ForecastTrendChart } from "./ForecastTrendChart";
import { ModelEvaluationTable } from "./ModelEvaluationTable";

interface ForecastCardProps {
  commodityId: string;
  commodityName: string;
  marketId: string;
  marketName: string;
  historicalObservations: PriceObservation[];
}

const DEFAULT_MODELS: RegisteredModelInfo[] = [
  {
    id: "chronos-2",
    name: "Amazon Chronos-2",
    family: "foundation",
    description: "Amazon Chronos-2 (120M parameters) zero-shot probabilistic foundation model",
    is_available: true,
    supported_quantiles: [0.1, 0.2, 0.5, 0.8, 0.9],
  },
  {
    id: "gradient_boosting",
    name: "Multi-Quantile Gradient Boosting",
    family: "ml",
    description: "HistGradientBoostingRegressor fitted across P10, P20, P50, P80, P90 with isotonic rearrangement",
    is_available: true,
    supported_quantiles: [0.1, 0.2, 0.5, 0.8, 0.9],
  },
  {
    id: "statistical",
    name: "Holt Exponential Smoothing",
    family: "statistical",
    description: "Additive damped trend with analytical error propagation intervals",
    is_available: true,
    supported_quantiles: [0.1, 0.2, 0.5, 0.8, 0.9],
  },
  {
    id: "seasonal_naive",
    name: "Seasonal Naive (7-Day)",
    family: "baseline",
    description: "Weekly cyclical persistence (y[t+h] = y[t+h-7])",
    is_available: true,
    supported_quantiles: [0.1, 0.2, 0.5, 0.8, 0.9],
  },
  {
    id: "naive",
    name: "Naive Persistence",
    family: "baseline",
    description: "Flat projection of latest price with square-root horizon variance",
    is_available: true,
    supported_quantiles: [0.1, 0.2, 0.5, 0.8, 0.9],
  },
];

export const ForecastCard: React.FC<ForecastCardProps> = ({
  commodityId,
  commodityName,
  marketId,
  marketName,
  historicalObservations,
}) => {
  const [horizon, setHorizon] = useState<number>(14);
  const [selectedModel, setSelectedModel] = useState<string>("gradient_boosting");
  const [models, setModels] = useState<RegisteredModelInfo[]>(DEFAULT_MODELS);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [insufficiency, setInsufficiency] = useState<ForecastInsufficiency | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [evaluations, setEvaluations] = useState<ModelComparisonResponse | null>(null);
  const [isEvalLoading, setIsEvalLoading] = useState<boolean>(false);
  const [showBenchmarks, setShowBenchmarks] = useState<boolean>(false);

  // Load registered models once
  useEffect(() => {
    getAvailableModels().then((data) => {
      if (data && data.length > 0) {
        setModels(data);
        // Default to chronos-2 if available, else gradient_boosting
        const chronos = data.find((m) => m.id === "chronos-2" && m.is_available);
        if (chronos) {
          setSelectedModel("chronos-2");
        } else {
          setSelectedModel("gradient_boosting");
        }
      }
    });
  }, []);

  // Fetch forecast whenever commodity, market, horizon, or model changes
  useEffect(() => {
    let active = true;

    async function fetchForecast() {
      const res = await getForecast({
        commodity: commodityId,
        market: marketId,
        horizon,
        model: selectedModel,
      });
      if (!active) return;
      if (res.success) {
        setForecast(res.forecast);
        setInsufficiency(null);
        setErrorMessage(null);
      } else if ("insufficiency" in res) {
        setForecast(null);
        setInsufficiency(res.insufficiency);
        setErrorMessage(null);
      } else {
        setForecast(null);
        setInsufficiency(null);
        setErrorMessage(res.error || "Failed to generate price forecast.");
      }
      setIsLoading(false);
    }

    void fetchForecast();

    return () => {
      active = false;
    };
  }, [commodityId, marketId, horizon, selectedModel]);

  // Load benchmark comparisons when requested
  useEffect(() => {
    if (!showBenchmarks) return;
    let active = true;

    async function fetchBenchmarks() {
      const data = await getModelEvaluations({
        commodity: commodityId,
        market: marketId,
        horizon,
      });
      if (!active) return;
      setEvaluations(data);
      setIsEvalLoading(false);
    }

    void fetchBenchmarks();

    return () => {
      active = false;
    };
  }, [showBenchmarks, commodityId, marketId, horizon]);

  return (
    <div className="space-y-6">
      {/* Control Strip */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 backdrop-blur-md shadow-xl flex flex-wrap items-center justify-between gap-4">
        {/* Horizon selector */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-zinc-400 block uppercase tracking-wider">
            Forecast Horizon
          </label>
          <div className="inline-flex rounded-xl bg-zinc-950 p-1 border border-zinc-800">
            {[7, 14, 28].map((h) => (
              <button
                key={h}
                type="button"
                onClick={() => setHorizon(h)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  horizon === h
                    ? "bg-purple-600 text-white shadow-lg shadow-purple-600/30 font-semibold"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {h} Days
              </button>
            ))}
          </div>
        </div>

        {/* Model Engine selector */}
        <div className="space-y-1 min-w-[260px]">
          <label className="text-xs font-semibold text-zinc-400 block uppercase tracking-wider">
            Forecasting Engine
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-3.5 py-2 rounded-xl bg-zinc-950 border border-zinc-800 text-xs font-medium text-zinc-200 focus:outline-none focus:border-purple-500 transition-colors"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} {!m.is_available ? "(Offline / Fallback)" : ""}
              </option>
            ))}
          </select>
        </div>

        {/* Benchmark Toggle Button */}
        <div className="space-y-1 self-end">
          <button
            type="button"
            onClick={() => setShowBenchmarks(!showBenchmarks)}
            className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all flex items-center gap-2 ${
              showBenchmarks
                ? "bg-purple-950/40 border-purple-600/60 text-purple-300"
                : "bg-zinc-950 border-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <span>📊</span>
            <span>{showBenchmarks ? "Hide Benchmarks" : "Compare Models"}</span>
          </button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 text-center space-y-3">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
          <p className="text-sm text-zinc-400">Computing probabilistic price distributions...</p>
        </div>
      )}

      {/* Insufficient History State */}
      {!isLoading && insufficiency && (
        <div className="rounded-2xl border border-amber-800/60 bg-amber-950/20 p-6 space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h4 className="text-base font-bold text-amber-200">
                Data Sufficiency Gate: Insufficient History
              </h4>
              <p className="text-xs text-amber-300/80 mt-0.5">
                {insufficiency.available_records} valid historical trading sessions recorded; minimum {insufficiency.required_minimum} required.
              </p>
            </div>
          </div>
          <p className="text-xs text-zinc-400 pl-9">
            {insufficiency.detail} AgriClutch enforces strict empirical data sufficiency rules: models never extrapolate or guess without adequate temporal sample depth.
          </p>
        </div>
      )}

      {/* Model Unavailable or Generic Error State */}
      {!isLoading && errorMessage && (
        <div className="rounded-2xl border border-rose-800/60 bg-rose-950/20 p-6 space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h4 className="text-base font-bold text-rose-200">Model Unavailable</h4>
              <p className="text-xs text-rose-300/80 mt-0.5">{errorMessage}</p>
            </div>
          </div>
          <div className="pl-9">
            <button
              type="button"
              onClick={() => setSelectedModel("gradient_boosting")}
              className="px-3.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200 font-medium transition-colors"
            >
              Switch to Multi-Quantile Gradient Boosting Baseline
            </button>
          </div>
        </div>
      )}

      {/* Success State: Forecast Chart and Metric Tiles */}
      {!isLoading && forecast && (
        <div className="space-y-6">
          {/* Horizon Terminal Summary Cards */}
          {forecast.points.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-1">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
                  Projected Median (P50 at Day {forecast.horizon})
                </span>
                <div className="text-2xl font-black text-purple-400 font-mono">
                  ₹{forecast.points[forecast.points.length - 1].q50.toFixed(2)}{" "}
                  <span className="text-xs font-normal text-zinc-500">/ kg</span>
                </div>
                <p className="text-[11px] text-zinc-500">
                  Target date: {forecast.points[forecast.points.length - 1].date}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-1">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
                  80% Prediction Corridor (P10 – P90)
                </span>
                <div className="text-2xl font-black text-zinc-100 font-mono">
                  ₹{forecast.points[forecast.points.length - 1].q10.toFixed(2)} – ₹
                  {forecast.points[forecast.points.length - 1].q90.toFixed(2)}
                </div>
                <p className="text-[11px] text-zinc-500">
                  Downside floor to upside ceiling range
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-1">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
                  Model Provenance
                </span>
                <div className="text-sm font-bold text-zinc-200 truncate">
                  {forecast.metadata.model_name.toUpperCase()}
                </div>
                <p className="text-[11px] text-zinc-500">
                  {forecast.metadata.context_length} sessions context &bull; {forecast.metadata.device} &bull; {forecast.metadata.parameter_count} params
                </p>
              </div>
            </div>
          )}

          {/* Time Series SVG Visualizer */}
          <ForecastTrendChart
            observations={historicalObservations}
            forecastPoints={forecast.points}
            originDate={forecast.origin_date}
            commodityName={commodityName}
            marketName={marketName}
            modelName={forecast.metadata.model_name.toUpperCase()}
          />
        </div>
      )}

      {/* Benchmarking Cross-Validation Section */}
      {showBenchmarks && evaluations && (
        <ModelEvaluationTable
          evaluations={evaluations.evaluations}
          splitCount={evaluations.split_count}
          horizon={evaluations.horizon}
          isLoading={isEvalLoading}
        />
      )}
    </div>
  );
};
