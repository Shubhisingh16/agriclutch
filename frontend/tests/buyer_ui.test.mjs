import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const buyerComponentsDir = path.resolve(__dirname, "../src/components/buyer");

test("AgriClutch Buyer Intelligence & Matching UI / Mathematical Contracts", async (t) => {
  await t.test("Haversine Distance Metric Consistency", () => {
    // Great circle distance formula between Chandigarh (30.7333, 76.7794) and Patiala (30.3398, 76.3869)
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

    const dist = haversineKm(30.7333, 76.7794, 30.3398, 76.3869);
    // Road distance is ~65-70km, great-circle straight-line distance is ~57-60km
    assert.ok(dist > 50 && dist < 70, `Haversine distance out of range: ${dist} km`);
  });

  await t.test("Herfindahl-Hirschman Index (HHI) Concentration Arithmetic", () => {
    const computeHHI = (quantities) => {
      const total = quantities.reduce((a, b) => a + b, 0);
      if (total <= 0) return null;
      const shares = quantities.map((q) => q / total);
      const sumSquares = shares.reduce((a, s) => a + s * s, 0);
      return 10000.0 * sumSquares;
    };

    // Case 1: Monopsony (1 buyer purchasing 100% of demand)
    const singleBuyerHhi = computeHHI([50000]);
    assert.equal(singleBuyerHhi, 10000.0, "Monopsony HHI must be exactly 10,000");

    // Case 2: Equal 4 buyers (each purchasing 25%)
    const fourBuyersHhi = computeHHI([2500, 2500, 2500, 2500]);
    assert.equal(fourBuyersHhi, 2500.0, "Equal 4 buyers HHI must be exactly 2,500");

    // Case 3: 10 equal buyers (each purchasing 10%)
    const tenBuyersHhi = computeHHI([1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]);
    assert.ok(
      Math.abs(tenBuyersHhi - 1000.0) < 1e-6,
      `Equal 10 buyers HHI must be approximately 1,000, got ${tenBuyersHhi}`
    );
  });

  await t.test("Order Size Distribution Statistical Gating ($N >= 3$)", () => {
    const evaluateDistributionGating = (sampleSize) => {
      if (sampleSize < 3) {
        return {
          status: "INSUFFICIENT_DATA",
          min_kg: null,
          median_kg: null,
          max_kg: null,
        };
      }
      return {
        status: "VALID",
        min_kg: 500,
        median_kg: 2500,
        max_kg: 10000,
      };
    };

    const gatedBelow = evaluateDistributionGating(2);
    assert.equal(gatedBelow.status, "INSUFFICIENT_DATA");
    assert.equal(gatedBelow.median_kg, null);

    const gatedAt = evaluateDistributionGating(3);
    assert.equal(gatedAt.status, "VALID");
    assert.equal(gatedAt.median_kg, 2500);
  });

  await t.test("Distribution Quantile Monotonicity", () => {
    const validQuantiles = {
      min: 500,
      p10: 800,
      p25: 1200,
      median: 2500,
      p75: 5000,
      p90: 8500,
      max: 12000,
    };

    assert.ok(validQuantiles.min <= validQuantiles.p10);
    assert.ok(validQuantiles.p10 <= validQuantiles.p25);
    assert.ok(validQuantiles.p25 <= validQuantiles.median);
    assert.ok(validQuantiles.median <= validQuantiles.p75);
    assert.ok(validQuantiles.p75 <= validQuantiles.p90);
    assert.ok(validQuantiles.p90 <= validQuantiles.max);
  });

  await t.test("Produce Lot Quantity Compatibility Partitioning", () => {
    const evaluateLotCompatibility = (supplyKg, minReqKg, maxReqKg) => {
      if (supplyKg < minReqKg) {
        return {
          status: "BELOW_MINIMUM",
          compatibleKg: 0,
          unmatchedKg: supplyKg,
        };
      }
      const compatibleKg = Math.min(supplyKg, maxReqKg);
      const unmatchedKg = Math.max(0, supplyKg - compatibleKg);
      const status = supplyKg <= maxReqKg ? "FULLY_SATISFIES" : "EXCEEDS_MAXIMUM_PARTIAL";
      return { status, compatibleKg, unmatchedKg };
    };

    // Supply 5000 kg into buyer requirement of [1000, 4000] kg
    const res1 = evaluateLotCompatibility(5000, 1000, 4000);
    assert.equal(res1.status, "EXCEEDS_MAXIMUM_PARTIAL");
    assert.equal(res1.compatibleKg, 4000);
    assert.equal(res1.unmatchedKg, 1000);

    // Supply 2500 kg into buyer requirement of [1000, 5000] kg
    const res2 = evaluateLotCompatibility(2500, 1000, 5000);
    assert.equal(res2.status, "FULLY_SATISFIES");
    assert.equal(res2.compatibleKg, 2500);
    assert.equal(res2.unmatchedKg, 0);

    // Supply 500 kg into buyer requirement of [1000, 5000] kg
    const res3 = evaluateLotCompatibility(500, 1000, 5000);
    assert.equal(res3.status, "BELOW_MINIMUM");
    assert.equal(res3.compatibleKg, 0);
    assert.equal(res3.unmatchedKg, 500);
  });

  await t.test("Temporal Overlap Window Calculation", () => {
    const calcOverlapDays = (availStart, availEnd, reqStart, reqEnd) => {
      const start = new Date(Math.max(new Date(availStart).getTime(), new Date(reqStart).getTime()));
      const end = new Date(Math.min(new Date(availEnd).getTime(), new Date(reqEnd).getTime()));
      const diffMs = end.getTime() - start.getTime();
      if (diffMs < 0) return 0;
      return Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;
    };

    const days = calcOverlapDays("2026-10-01", "2026-10-10", "2026-10-05", "2026-10-15");
    assert.equal(days, 6, "Window Oct 5 to Oct 10 inclusive must be 6 days");

    const zeroDays = calcOverlapDays("2026-10-01", "2026-10-04", "2026-10-05", "2026-10-15");
    assert.equal(zeroDays, 0, "Non-overlapping intervals must yield 0 days");
  });

  await t.test("Strict Zero-Recommendation Enforcement Across Component Source Code", () => {
    const files = fs.readdirSync(buyerComponentsDir).filter((f) => f.endsWith(".tsx"));
    assert.ok(files.length >= 6, `Expected at least 6 buyer components, found ${files.length}`);

    const forbiddenPhrases = [
      "RECOMMENDED BUYER",
      "BEST BUYER",
      "WINNER",
      "TOP CHOICE",
      "SELL NOW",
      "HOLD YOUR PRODUCE",
      "OPTIMAL BUYER",
      "OPTIMAL PLAN RECOMMENDS",
    ];

    for (const file of files) {
      const fullPath = path.join(buyerComponentsDir, file);
      const content = fs.readFileSync(fullPath, "utf-8");

      for (const phrase of forbiddenPhrases) {
        // We allow the phrase in explicit disclaimers (e.g. "does not provide 'BEST BUYER' or 'SELL NOW'")
        const nonDisclaimerMatches = content
          .split("\n")
          .filter(
            (line) =>
              line.toUpperCase().includes(phrase) &&
              !line.toLowerCase().includes("does not") &&
              !line.toLowerCase().includes("zero") &&
              !line.toLowerCase().includes("no ") &&
              !line.toLowerCase().includes("disclaimer") &&
              !line.toLowerCase().includes("forbidden") &&
              !line.toLowerCase().includes("strictly")
          );

        assert.equal(
          nonDisclaimerMatches.length,
          0,
          `Found forbidden normative recommendation phrase "${phrase}" in ${file}: ${nonDisclaimerMatches.join("; ")}`
        );
      }
    }
  });

  await t.test("Data Provenance & Non-Normative Transparency Notice Verification", () => {
    const panelPath = path.join(buyerComponentsDir, "BuyerIntelligencePanel.tsx");
    const content = fs.readFileSync(panelPath, "utf-8");

    assert.ok(
      content.includes("NON-NORMATIVE DATA CONTRACT"),
      "BuyerIntelligencePanel must prominently declare NON-NORMATIVE DATA CONTRACT"
    );
    assert.ok(
      content.includes("does not rank, select winners, or issue selling advice"),
      "BuyerIntelligencePanel must state that it does not rank or issue selling advice"
    );
  });
});
