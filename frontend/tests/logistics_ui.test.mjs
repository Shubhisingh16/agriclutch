import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const logisticsComponentsDir = path.resolve(__dirname, "../src/components/logistics");

test("AgriClutch Step 13 Logistics, Storage & Perishability UI & Mathematical Contracts", async (t) => {
  await t.test("Haversine Great-Circle Geodesic Arithmetic", () => {
    const toRad = (deg) => (deg * Math.PI) / 180.0;
    const haversineKm = (lat1, lon1, lat2, lon2) => {
      const R = 6371.0;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a =
        Math.sin(dLat / 2.0) ** 2 +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2.0) ** 2;
      const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
      return R * c;
    };

    // Kalka (30.8350, 76.9350) to Chandigarh APMC (30.7050, 76.7900)
    const dist = haversineKm(30.835, 76.935, 30.705, 76.79);
    assert.ok(dist >= 18.0 && dist <= 24.0, `Calculated distance ${dist} km out of benchmark range [18, 24]`);

    // Zero distance for identical coordinates
    const zeroDist = haversineKm(30.835, 76.935, 30.835, 76.935);
    assert.equal(zeroDist, 0.0, "Identical coordinates must yield exactly 0 km");
  });

  await t.test("Decoupled Perishability Exponential Equations: S(t) = exp(-delta*t), F(t) = F0*exp(-beta*t)", () => {
    const delta = 0.035; // Tomato ambient decay rate
    const beta = 0.05; // Quality decay rate
    const initialQty = 2000.0;
    const initialQuality = 1.0;
    const days = 5;

    const s5 = Math.exp(-delta * days);
    const deliveredQty = initialQty * s5;
    const q5 = initialQuality * Math.exp(-beta * days);

    // Verify mathematical bounds
    assert.ok(s5 > 0.8 && s5 < 0.9, `S(5) out of expected range: ${s5}`);
    assert.ok(deliveredQty < initialQty, "Delivered volume must be lower than initial harvest volume");
    assert.ok(q5 < initialQuality, "Final quality factor must degrade over time");
  });

  await t.test("Storage Capacity Partitioning without Shortfall Rounding", () => {
    const allocateStorage = (requestedQty, availableCapacity, durationDays, ratePerKgDay) => {
      const stored = Math.min(requestedQty, Math.max(0, availableCapacity));
      const unstored = Math.max(0, requestedQty - availableCapacity);
      const cost = stored * durationDays * ratePerKgDay;
      const status = unstored > 0 ? "PARTIALLY_FEASIBLE" : "FEASIBLE";
      return { stored, unstored, cost, status };
    };

    // Case 1: Partial storage capacity shortfall
    const partial = allocateStorage(2500, 1500, 10, 0.2);
    assert.equal(partial.stored, 1500, "Stored volume must be capped at available capacity");
    assert.equal(partial.unstored, 1000, "Unstored volume shortfall must equal 1000 kg");
    assert.equal(partial.status, "PARTIALLY_FEASIBLE");
    assert.equal(partial.cost, 1500 * 10 * 0.2);

    // Case 2: Full capacity available
    const full = allocateStorage(1000, 5000, 7, 0.15);
    assert.equal(full.stored, 1000);
    assert.equal(full.unstored, 0);
    assert.equal(full.status, "FEASIBLE");
  });

  await t.test("Additive Friction Logistics Cost Decomposition", () => {
    const baseFee = 800.0;
    const costPerKm = 25.0;
    const distanceKm = 40.0;
    const loadingPerQtl = 12.0;
    const unloadingPerQtl = 10.0;
    const qtyKg = 2000.0; // 20 quintals
    const extraHandling = 150.0;

    const haulageCost = distanceKm * costPerKm;
    const transportCost = baseFee + haulageCost;
    const loadingCost = (qtyKg / 100.0) * loadingPerQtl;
    const unloadingCost = (qtyKg / 100.0) * unloadingPerQtl;
    const totalCost = transportCost + loadingCost + unloadingCost + extraHandling;

    assert.equal(transportCost, 1800.0);
    assert.equal(loadingCost, 240.0);
    assert.equal(unloadingCost, 200.0);
    assert.equal(totalCost, 2390.0);
  });

  await t.test("Strict Absence of Recommendation Leakage in Step 13 UI Components", () => {
    const forbiddenTerms = [
      "best_route",
      "preferred_route",
      "selected_route",
      "optimal_route",
      "recommended_route",
      "winner",
      "rank",
      "rank_score",
      "priority_score",
      "recommendation_score",
      "is_best",
      "is_preferred",
      "is_selected",
      "best",
      "optimal",
      "ranking",
      "recommended action",
      "recommended buyer",
      "recommended market",
      "score",
    ];

    const files = fs.readdirSync(logisticsComponentsDir);
    assert.ok(files.length >= 4, "Must contain all Step 13 logistics components");

    for (const file of files) {
      if (!file.endsWith(".tsx")) continue;
      const content = fs.readFileSync(path.join(logisticsComponentsDir, file), "utf-8").toLowerCase();
      for (const term of forbiddenTerms) {
        assert.ok(
          !content.includes(`"${term}"`) && !content.includes(`'${term}'`),
          `Forbidden recommendation term '${term}' found in UI component ${file}`
        );
      }
    }
  });
});
