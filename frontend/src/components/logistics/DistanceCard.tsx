"use client";

import React, { useState } from "react";
import { calculateDistance } from "@/lib/api/logistics";
import { DistanceResult } from "@/types/logistics";
import { AssumptionBadge } from "./AssumptionBadge";

interface DistanceCardProps {
  defaultOrigin?: string;
  defaultDestination?: string;
}

export const DistanceCard: React.FC<DistanceCardProps> = ({
  defaultOrigin = "Kalka Farm Gate (30.8350, 76.9350)",
  defaultDestination = "Chandigarh APMC Yard (30.7250, 76.8000)",
}) => {
  const [originLat, setOriginLat] = useState<number>(30.835);
  const [originLon, setOriginLon] = useState<number>(76.935);
  const [destLat, setDestLat] = useState<number>(30.725);
  const [destLon, setDestLon] = useState<number>(76.8);
  const [speedKmh, setSpeedKmh] = useState<number>(45);
  const [roadKm, setRoadKm] = useState<string>("24.0");
  const [useRoad, setUseRoad] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DistanceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await calculateDistance({
        origin_lat: originLat,
        origin_lon: originLon,
        dest_lat: destLat,
        dest_lon: destLon,
        road_distance_km: useRoad && roadKm ? parseFloat(roadKm) : null,
        speed_kmh: speedKmh > 0 ? speedKmh : null,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Distance calculation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
        <div className="flex items-center space-x-2">
          <span className="text-xl">📍</span>
          <div>
            <h4 className="text-sm font-bold text-zinc-100">Geodesic & Road Distance Engine</h4>
            <p className="text-[11px] text-zinc-400">
              Spherical Haversine distance with explicit distinction between road corridors and straight-line paths
            </p>
          </div>
        </div>
        <AssumptionBadge status="DEMO_ASSUMPTION" isDemo={true} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Origin */}
        <div className="space-y-2 p-3 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
          <div className="text-xs font-semibold text-emerald-400">Origin: {defaultOrigin}</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="text-[10px] font-mono text-zinc-400">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={originLat}
                onChange={(e) => setOriginLat(parseFloat(e.target.value) || 0)}
                className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-zinc-400">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={originLon}
                onChange={(e) => setOriginLon(parseFloat(e.target.value) || 0)}
                className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100"
              />
            </div>
          </div>
        </div>

        {/* Destination */}
        <div className="space-y-2 p-3 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
          <div className="text-xs font-semibold text-blue-400">Destination: {defaultDestination}</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="text-[10px] font-mono text-zinc-400">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={destLat}
                onChange={(e) => setDestLat(parseFloat(e.target.value) || 0)}
                className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-zinc-400">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={destLon}
                onChange={(e) => setDestLon(parseFloat(e.target.value) || 0)}
                className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Corridor Settings */}
      <div className="flex flex-wrap items-center gap-4 text-xs bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/60">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useRoad}
            onChange={(e) => setUseRoad(e.target.checked)}
            className="rounded border-zinc-700 text-emerald-500 focus:ring-emerald-500 bg-zinc-900"
          />
          <span className="text-zinc-300">Use Documented Road Distance (km)</span>
        </label>
        {useRoad && (
          <input
            type="number"
            value={roadKm}
            onChange={(e) => setRoadKm(e.target.value)}
            className="w-24 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100 font-mono"
            placeholder="Road km"
          />
        )}
        <div className="flex items-center space-x-2">
          <span className="text-zinc-400">Speed Assumption:</span>
          <input
            type="number"
            value={speedKmh}
            onChange={(e) => setSpeedKmh(parseFloat(e.target.value) || 0)}
            className="w-16 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100 font-mono"
          />
          <span className="text-zinc-400">km/h</span>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading}
          className="ml-auto px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? "Computing..." : "Resolve Route"}
        </button>
      </div>

      {error && <div className="text-xs text-red-400 bg-red-500/10 p-2.5 rounded border border-red-500/20">{error}</div>}

      {/* Results Display */}
      {result && (
        <div className="space-y-3 pt-2">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">
                {result.distance_type === "ROAD_DISTANCE"
                  ? "DOCUMENTED ROAD DISTANCE"
                  : result.distance_type === "ESTIMATED_ROUTE_DISTANCE"
                  ? "ESTIMATED ROUTE DISTANCE"
                  : "STRAIGHT-LINE DISTANCE"}
              </div>
              <div className="text-lg font-bold text-white font-mono mt-0.5">
                {result.distance_km != null ? `${result.distance_km} km` : "N/A"}
              </div>
              <div className="text-[10px] text-zinc-400 mt-1 truncate">{result.distance_type}</div>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">STRAIGHT-LINE GEODESIC</div>
              <div className="text-lg font-bold text-zinc-300 font-mono mt-0.5">
                {result.straight_line_distance_km != null ? `${result.straight_line_distance_km} km` : "N/A"}
              </div>
              <div className="text-[10px] text-zinc-400 mt-1">
                {result.circuity_factor ? `Circuity: ${result.circuity_factor}× (Configured)` : "Haversine WGS84"}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">EST. TRANSIT DURATION</div>
              <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                {result.transit_duration_hours != null ? `${result.transit_duration_hours} hrs` : "N/A"}
              </div>
              <div className="text-[10px] text-zinc-400 mt-1">{result.transit_time_status}</div>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="text-[10px] font-mono text-zinc-400">PROVENANCE STATUS</div>
              <div className="text-xs font-semibold text-amber-400 font-mono mt-1">
                {result.provenance.status}
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-1">
                {result.provenance.source_name}
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-zinc-950/70 border border-zinc-800/80 text-xs space-y-1">
            <div className="text-zinc-300">{result.provenance.justification}</div>
            {result.distance_type === "ESTIMATED_ROUTE_DISTANCE" && (
              <div className="text-[11px] text-amber-400/90 font-mono">
                Notice: Estimated route distance using configured 1.25× circuity factor. Do not interpret as observed road distance.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
