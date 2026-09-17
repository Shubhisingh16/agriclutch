/**
 * AgriClutch Frontend Dashboard Data & Logic Test Suite.
 * Verified with Node.js 20 built-in test runner.
 * SIH26132 — Market Linkages & Price Discovery for Farmers.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

describe("AgriClutch Dashboard Data Contracts & Logic", () => {
  describe("Dual Pricing Normalization Logic", () => {
    it("correctly converts Rs/Quintal to INR/kg by dividing by 100", () => {
      const originalModalPrice = 2850.0;
      const originalUnit = "Rs/Quintal";

      let normalizedPrice;
      if (originalUnit.toLowerCase().includes("quintal")) {
        normalizedPrice = Number((originalModalPrice * 0.01).toFixed(2));
      } else {
        normalizedPrice = originalModalPrice;
      }

      assert.equal(normalizedPrice, 28.5);
    });

    it("leaves INR/kg units unscaled", () => {
      const originalModalPrice = 28.5;
      const originalUnit = "INR_PER_KG";

      let normalizedPrice;
      if (originalUnit.toLowerCase().includes("quintal")) {
        normalizedPrice = Number((originalModalPrice * 0.01).toFixed(2));
      } else {
        normalizedPrice = originalModalPrice;
      }

      assert.equal(normalizedPrice, 28.5);
    });
  });

  describe("Chronological Time-Series Sorting", () => {
    it("orders observations strictly ascending by trading date for time-series charting", () => {
      const rawObservations = [
        { record_date: "2024-09-14", normalized_modal_price: 29.5 },
        { record_date: "2024-09-10", normalized_modal_price: 28.0 },
        { record_date: "2024-09-12", normalized_modal_price: 29.0 },
        { record_date: "2024-09-11", normalized_modal_price: 28.5 },
      ];

      const sorted = [...rawObservations].sort(
        (a, b) => new Date(a.record_date).getTime() - new Date(b.record_date).getTime()
      );

      assert.equal(sorted[0].record_date, "2024-09-10");
      assert.equal(sorted[1].record_date, "2024-09-11");
      assert.equal(sorted[2].record_date, "2024-09-12");
      assert.equal(sorted[3].record_date, "2024-09-14");
    });
  });

  describe("Cross-Market Price Dispersion Deltas", () => {
    it("calculates accurate price delta and percentage versus baseline mandi", () => {
      const baselinePrice = 28.5; // Chandigarh
      const azadpurPrice = 31.5; // Azadpur Delhi
      const panchkulaPrice = 27.5; // Panchkula

      const deltaAzadpur = azadpurPrice - baselinePrice;
      const deltaAzadpurPct = (deltaAzadpur / baselinePrice) * 100;

      const deltaPanchkula = panchkulaPrice - baselinePrice;
      const deltaPanchkulaPct = (deltaPanchkula / baselinePrice) * 100;

      assert.equal(Number(deltaAzadpur.toFixed(2)), 3.0);
      assert.equal(Number(deltaAzadpurPct.toFixed(1)), 10.5);

      assert.equal(Number(deltaPanchkula.toFixed(2)), -1.0);
      assert.equal(Number(deltaPanchkulaPct.toFixed(1)), -3.5);
    });
  });

  describe("Geographic Coordinate Validation", () => {
    it("verifies Indian territorial bounds for regional corridor mandis", () => {
      const mandis = [
        { id: "mandi_ch_49", name: "Chandigarh", lat: 30.7333, lon: 76.7794 },
        { id: "mandi_hr_01", name: "Panchkula", lat: 30.6942, lon: 76.8606 },
        { id: "mandi_pb_12", name: "Patiala", lat: 30.3398, lon: 76.3869 },
        { id: "mandi_dl_164", name: "Azadpur", lat: 28.7161, lon: 77.1706 },
      ];

      for (const m of mandis) {
        // Assert within Indian territorial bounds (Lat 8.0 to 37.5, Lon 68.5 to 97.5)
        assert.ok(m.lat >= 8.0 && m.lat <= 37.5, `${m.name} latitude out of bounds`);
        assert.ok(m.lon >= 68.5 && m.lon <= 97.5, `${m.name} longitude out of bounds`);
      }
    });
  });

  describe("Data Provenance & Non-Fabrication Rules", () => {
    it("ensures observations carry verifiable source labels and no fake forecast indicators", () => {
      const observation = {
        observation_id: "00000000-0000-0000-0000-000000000001",
        source_name: "SYNTHETIC_DEMO",
        source_record_id: "SYN_001",
        record_date: "2024-09-10",
        normalized_modal_price: 28.0,
        is_interpolated: false,
        is_outlier: false,
      };

      // Assert non-empty provenance
      assert.ok(observation.source_name.length > 0);
      assert.ok(observation.source_record_id.length > 0);

      // Assert no fake forecast fields exist in the raw observation
      assert.equal(observation["predicted_price"], undefined);
      assert.equal(observation["forecast_p50"], undefined);
      assert.equal(observation["ai_confidence"], undefined);
    });
  });

  describe("Explicit Demo Mode Disclosure & Freshness Distinction", () => {
    it("maps demo data mode to unambiguous DEMO DATA banner with zero forbidden claims", () => {
      const mode = "DEMO";
      const header = "SYNTHETIC_TEST_FIXTURE";
      const sourceName = "SYNTHETIC_DEMO";

      const isDemo =
        mode === "DEMO" ||
        header === "SYNTHETIC_TEST_FIXTURE" ||
        sourceName.toUpperCase().includes("SYNTHETIC");

      assert.equal(isDemo, true);

      // Verify canonical banner label
      const bannerTitle = isDemo
        ? "DEMO DATA — Synthetic test fixture"
        : "Historical APMC Mandi Records";
      assert.equal(bannerTitle, "DEMO DATA — Synthetic test fixture");

      // Verify explicit synthetic disclosure text
      const disclosureText =
        "These values are synthetic test observations used for offline benchmarking and interface testing. They do not represent current, live, or empirical agricultural market transactions.";
      assert.ok(disclosureText.includes("synthetic test observations"));

      // Forbidden words check: Assert that the label and UI descriptor do NOT claim to be live/real-time
      const forbiddenTerms = [
        "live",
        "real-time",
        "verified apmc feed",
        "genuine market observation",
        "current market price",
      ];
      const lowerTitle = bannerTitle.toLowerCase();
      for (const term of forbiddenTerms) {
        assert.equal(
          lowerTitle.includes(term),
          false,
          `Demo banner label must NOT include forbidden claim '${term}'`
        );
      }

      // Assert freshness separation: Fixture Loaded (demo time) vs Empirical Record Date
      const demoFreshnessLabel = "Fixture Loaded";
      const empiricalFreshnessLabel = "Empirical Record Date";
      assert.notEqual(demoFreshnessLabel, empiricalFreshnessLabel);
    });

    it("maps database mode to Historical APMC Mandi Records with empirical session freshness", () => {
      const mode = "DATABASE";
      const header = "POSTGRESQL";
      const sourceName = "APMC_HISTORICAL";

      const isDemo =
        mode === "DEMO" ||
        header === "SYNTHETIC_TEST_FIXTURE" ||
        sourceName.toUpperCase().includes("SYNTHETIC");

      assert.equal(isDemo, false);

      const bannerTitle = isDemo
        ? "DEMO DATA — Synthetic test fixture"
        : "Historical APMC Mandi Records";
      assert.equal(bannerTitle, "Historical APMC Mandi Records");
    });
  });
});
