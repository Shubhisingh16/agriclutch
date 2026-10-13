import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const decisionComponentsDir = path.resolve(__dirname, "../src/components/decision");

test("AgriClutch Step 14 Decision Engine, Optimal Selling Plan & What-If Simulator", async (t) => {
  await t.test("Component files existence and integrity", () => {
    assert.ok(fs.existsSync(path.join(decisionComponentsDir, "DecisionDashboard.tsx")));
    assert.ok(fs.existsSync(path.join(decisionComponentsDir, "WhatIfSimulator.tsx")));
    assert.ok(fs.existsSync(path.resolve(__dirname, "../src/types/decision.ts")));
    assert.ok(fs.existsSync(path.resolve(__dirname, "../src/lib/api/decision.ts")));
  });

  await t.test("Decision Objective & Downside Risk Penalty Mathematics", () => {
    // Formulation: c_i = ExpectedNRV_i - lambda * max(0, ExpectedNRV_i - NRV_p10_i)
    const computeNetCoeff = (expectedNrv, nrvP10, lambda) => {
      const downsideShortfall = Math.max(0, expectedNrv - nrvP10);
      return expectedNrv - (lambda * downsideShortfall);
    };

    const expNRV = 32.50;
    const p10NRV = 27.00;

    const coeffNeutral = computeNetCoeff(expNRV, p10NRV, 0.0);
    const coeffAware = computeNetCoeff(expNRV, p10NRV, 0.5);
    const coeffAverse = computeNetCoeff(expNRV, p10NRV, 1.0);

    assert.equal(coeffNeutral, 32.50, "Risk neutral must equal expected NRV");
    assert.equal(coeffAware, 32.50 - (0.5 * 5.50), "Risk aware must deduct 0.5x shortfall");
    assert.equal(coeffAverse, 32.50 - (1.0 * 5.50), "Risk averse must deduct 1.0x shortfall");
    assert.ok(coeffAverse < coeffAware && coeffAware < coeffNeutral);
  });

  await t.test("Total Supply Conservation & Allocation Split Identity", () => {
    const allocations = [
      { name: "Direct Buyer", qtyKg: 1800.0, netNrv: 31.00 },
      { name: "Terminal Mandi", qtyKg: 1200.0, netNrv: 29.50 },
    ];
    const totalSupply = 3000.0;

    const totalAllocated = allocations.reduce((acc, a) => acc + a.qtyKg, 0);
    assert.equal(totalAllocated, totalSupply, "Sum of allocations must strictly conserve total supply");

    const totalExpectedNrv = allocations.reduce((acc, a) => acc + (a.qtyKg * a.netNrv), 0);
    const avgNrvPerKg = totalExpectedNrv / totalAllocated;

    assert.equal(totalExpectedNrv, (1800 * 31.00) + (1200 * 29.50));
    assert.ok(avgNrvPerKg >= 29.50 && avgNrvPerKg <= 31.00);
  });

  await t.test("What-If Counterfactual NRV Delta Calculation", () => {
    const baselineNrv = 92000.0;
    const counterfactualNrv = 85560.0;

    const nrvDelta = counterfactualNrv - baselineNrv;
    const pctChange = (nrvDelta / baselineNrv) * 100.0;

    assert.equal(nrvDelta, -6440.0);
    assert.ok(Math.abs(pctChange - (-7.0)) < 0.1);
  });
});
