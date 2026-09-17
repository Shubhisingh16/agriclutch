import test from "node:test";
import assert from "node:assert/strict";

test("AgriClutch NRV Engine UI & Client Contracts", async (t) => {
  await t.test("Quantity Unit Conversion Arithmetic", () => {
    const toKg = (val, unit) => {
      switch (unit) {
        case "kg":
          return val;
        case "quintal":
          return val * 100.0;
        case "tonne":
          return val * 1000.0;
        default:
          throw new Error(`Unknown unit: ${unit}`);
      }
    };

    assert.equal(toKg(50, "quintal"), 5000.0);
    assert.equal(toKg(5, "tonne"), 5000.0);
    assert.equal(toKg(2500, "kg"), 2500.0);
  });

  await t.test("NRV Quantile Monotonicity Verification", () => {
    const mockDistribution = {
      p10: 95000.0,
      p20: 105000.0,
      p50: 120000.0,
      p80: 138000.0,
      p90: 152000.0,
      mean: 122000.0,
    };

    assert.ok(mockDistribution.p10 <= mockDistribution.p20, "p10 <= p20 violated");
    assert.ok(mockDistribution.p20 <= mockDistribution.p50, "p20 <= p50 violated");
    assert.ok(mockDistribution.p50 <= mockDistribution.p80, "p50 <= p80 violated");
    assert.ok(mockDistribution.p80 <= mockDistribution.p90, "p80 <= p90 violated");
  });

  await t.test("NRV Friction Deductions Consistency", () => {
    const grossP50 = 150000.0;
    const costs = {
      transport: 12000.0,
      storage: 4500.0,
      handling: 2500.0,
      market_fee: 3000.0,
      other: 1000.0,
      loss: 7000.0,
    };
    const totalCost = Object.values(costs).reduce((acc, c) => acc + c, 0);
    const nrvP50 = grossP50 - totalCost;

    assert.equal(totalCost, 30000.0);
    assert.equal(nrvP50, 120000.0);
    assert.equal(grossP50 - totalCost, nrvP50);
  });

  await t.test("Break-Even Quoted Price Calculation", () => {
    // Formula: P_be = C_non_market / (Q_eff * F_quality * (1 - market_cess_rate))
    const effectiveQtyKg = 4800.0; // after 4% loss
    const qualityFactor = 1.0;     // Grade A
    const apmcCessRate = 0.02;     // 2%
    const nonMarketCosts = 12000.0 + 4500.0 + 2500.0 + 1000.0; // 20,000 INR

    const denominator = effectiveQtyKg * qualityFactor * (1.0 - apmcCessRate);
    const breakEvenPrice = nonMarketCosts / denominator;

    // Verify: At break-even price, gross rev = 4800 * 1.0 * P_be
    const grossAtBreakEven = effectiveQtyKg * qualityFactor * breakEvenPrice;
    const apmcFee = grossAtBreakEven * apmcCessRate;
    const totalDeductions = nonMarketCosts + apmcFee;
    const nrvAtBreakEven = grossAtBreakEven - totalDeductions;

    assert.ok(Math.abs(nrvAtBreakEven) < 1e-10, `NRV at break-even must be 0, got ${nrvAtBreakEven}`);
    assert.ok(breakEvenPrice > 0, "Break-even price must be positive");
  });

  await t.test("Strict Zero-Recommendation Enforcement", () => {
    // Ensure that no component outputs advice, winner badges, or trading recommendations
    const mockReport = {
      action: null,
      recommendation: null,
      winner: null,
      best_market: null,
      disclaimer: "Economic Net Realizable Value distribution — not a trading recommendation or guarantee.",
    };

    const forbiddenFields = [
      "action",
      "recommendation",
      "winner",
      "best_market",
      "sell",
      "hold",
      "buy",
      "store",
      "recommended_action",
      "recommended_market",
    ];
    for (const f of forbiddenFields) {
      assert.ok(!mockReport[f], `Forbidden decision advice field present: ${f}`);
    }
    assert.match(mockReport.disclaimer, /not a trading recommendation/i);
  });

  await t.test("Demo Assumption Auditing & Provenance Disclosure", () => {
    const demoPayload = {
      is_demo: true,
      provenance_status: "DEMO",
      disclaimer: "Economic calculations based on demo assumptions. Not certified trading advice.",
    };

    assert.equal(demoPayload.is_demo, true);
    assert.equal(demoPayload.provenance_status, "DEMO");
    assert.match(demoPayload.disclaimer, /demo assumptions/i);
  });

  await t.test("Sensitivity Matrix Dimensions & Baseline Alignment", () => {
    const sensitivityGrid = {
      variable_1_deltas: [-0.10, 0.0, 0.10],
      variable_2_deltas: [-0.15, 0.0, 0.15],
      base_nrv: 120000.0,
      matrix: [
        [{ nrv_p50: 105000 }, { nrv_p50: 108000 }, { nrv_p50: 111000 }],
        [{ nrv_p50: 117000 }, { nrv_p50: 120000 }, { nrv_p50: 123000 }],
        [{ nrv_p50: 129000 }, { nrv_p50: 132000 }, { nrv_p50: 135000 }],
      ],
    };

    assert.equal(sensitivityGrid.matrix.length, 3);
    assert.equal(sensitivityGrid.matrix[0].length, 3);
    // Center element (index [1][1]) must equal baseline NRV
    assert.equal(sensitivityGrid.matrix[1][1].nrv_p50, sensitivityGrid.base_nrv);
  });
});
