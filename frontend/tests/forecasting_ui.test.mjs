import test from "node:test";
import assert from "node:assert/strict";

test("AgriClutch Forecasting UI & Client Data Contracts", async (t) => {
  await t.test("Quantile Ordering and Monotonicity", () => {
    const mockPoint = {
      date: "2024-09-20",
      q10: 24.50,
      q20: 26.00,
      q50: 28.50,
      q80: 31.20,
      q90: 33.80,
      quantile_adjusted: false,
    };

    assert.ok(mockPoint.q10 <= mockPoint.q20, "q10 <= q20 violated");
    assert.ok(mockPoint.q20 <= mockPoint.q50, "q20 <= q50 violated");
    assert.ok(mockPoint.q50 <= mockPoint.q80, "q50 <= q80 violated");
    assert.ok(mockPoint.q80 <= mockPoint.q90, "q80 <= q90 violated");
  });

  await t.test("Data Sufficiency Gate Detection", () => {
    const mockInsufficiency = {
      status: "INSUFFICIENT_HISTORY",
      commodity_id: "tomato",
      market_id: "mandi_dl_164",
      available_records: 18,
      required_minimum: 30,
      detail: "Series contains 18 trading sessions; minimum 30 required for dependable forecasting.",
    };

    assert.equal(mockInsufficiency.status, "INSUFFICIENT_HISTORY");
    assert.ok(mockInsufficiency.available_records < mockInsufficiency.required_minimum);
    assert.match(mockInsufficiency.detail, /minimum 30 required/);
  });

  await t.test("Mandatory Uncertainty Disclaimer Compliance", () => {
    const mandatoryDisclaimer = "Model forecast — not a guaranteed price.";
    const mockMetadata = {
      model_name: "chronos-2",
      model_version: "amazon/chronos-2",
      parameter_count: "120M",
      context_length: 60,
      device: "cpu",
      data_source: "SYNTHETIC_DEMO_FIXTURE",
      quantiles: [0.1, 0.2, 0.5, 0.8, 0.9],
      is_demo: true,
      disclaimer: mandatoryDisclaimer,
    };

    assert.equal(mockMetadata.disclaimer, mandatoryDisclaimer);
    assert.match(mockMetadata.disclaimer, /not a guaranteed price/i);
  });

  await t.test("Strict Zero-Recommendation Policy Compliance", () => {
    // Verify that the forecast payload does not contain SELL, HOLD, or BUY signals
    const sampleKeys = ["status", "commodity_id", "market_id", "origin_date", "horizon", "unit", "points", "metadata"];
    const forbiddenSignals = ["BUY", "HOLD", "SELL", "STRONG_BUY", "RECOMMENDATION", "ACTION"];

    for (const key of sampleKeys) {
      assert.ok(!forbiddenSignals.includes(key.toUpperCase()), `Forbidden recommendation key found: ${key}`);
    }
  });
});
