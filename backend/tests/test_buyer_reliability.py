"""
Unit Tests for AgriClutch Buyer Empirical Reliability Engine.
Verifies fulfillment rate, cancellation rate, payment delay days, dispute rate,
and statistical sufficiency gating (N >= 3).
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date
from typing import List

import pytest

from ml.buyer.contracts import (
    BuyerTransactionRecord,
    ReliabilityStatus,
)
from ml.buyer.reliability import BuyerReliabilityEngine


@pytest.fixture
def sample_transactions() -> List[BuyerTransactionRecord]:
    return [
        BuyerTransactionRecord(
            transaction_id="t1",
            buyer_id="buyer_01",
            commodity_id="tomato",
            order_date=date(2024, 8, 1),
            agreed_quantity_kg=2000.0,
            delivered_quantity_kg=2000.0,
            agreed_price_per_kg=25.0,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=date(2024, 8, 8),
            actual_payment_date=date(2024, 8, 8),
            dispute_status=False,
        ),
        BuyerTransactionRecord(
            transaction_id="t2",
            buyer_id="buyer_01",
            commodity_id="tomato",
            order_date=date(2024, 8, 15),
            agreed_quantity_kg=3000.0,
            delivered_quantity_kg=2700.0,
            agreed_price_per_kg=27.0,
            fulfillment_status="PARTIAL",
            payment_status="PAID_LATE",
            agreed_payment_due_date=date(2024, 8, 22),
            actual_payment_date=date(2024, 8, 26),  # 4 days late
            dispute_status=False,
        ),
        BuyerTransactionRecord(
            transaction_id="t3",
            buyer_id="buyer_01",
            commodity_id="tomato",
            order_date=date(2024, 8, 25),
            agreed_quantity_kg=2500.0,
            delivered_quantity_kg=2500.0,
            agreed_price_per_kg=26.5,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=date(2024, 9, 1),
            actual_payment_date=date(2024, 9, 1),
            dispute_status=False,
        ),
    ]


def test_reliability_gating_n_less_than_3() -> None:
    """Verifies that buyers with < 3 past orders return INSUFFICIENT_HISTORY with null metrics."""
    few_txs = [
        BuyerTransactionRecord(
            transaction_id="t1",
            buyer_id="buyer_new",
            commodity_id="tomato",
            order_date=date(2024, 8, 1),
            agreed_quantity_kg=1000.0,
            delivered_quantity_kg=1000.0,
            agreed_price_per_kg=25.0,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=date(2024, 8, 8),
            actual_payment_date=date(2024, 8, 8),
            dispute_status=False,
        )
    ]
    metrics = BuyerReliabilityEngine.calculate("buyer_new", few_txs)

    assert metrics.status == ReliabilityStatus.INSUFFICIENT_HISTORY
    assert metrics.sample_size == 1
    assert metrics.fulfillment_rate is None
    assert metrics.cancellation_rate is None
    assert metrics.average_payment_delay_days is None
    assert metrics.dispute_rate is None
    assert metrics.provenance.description is not None and "below minimum threshold of 3" in metrics.provenance.description


def test_reliability_calculation_n_ge_3(sample_transactions: List[BuyerTransactionRecord]) -> None:
    """
    Verifies metric formulas for N >= 3:
    Fulfilled orders: 2 fulfilled out of 3 confirmed = 2/3 ~ 0.6667
    Cancellation rate: 0 / 3 = 0.0
    Payment delay: [0, 4, 0] -> mean = 4 / 3 = 1.33 days
    Dispute rate: 0 / 3 = 0.0
    """
    metrics = BuyerReliabilityEngine.calculate("buyer_01", sample_transactions)

    assert metrics.status == ReliabilityStatus.CALCULATED
    assert metrics.sample_size == 3
    assert metrics.fulfilled_orders == 2
    assert metrics.cancellation_rate == 0.0
    assert metrics.average_payment_delay_days == pytest.approx(1.3333, rel=1e-2)
    assert metrics.dispute_rate == 0.0


def test_reliability_with_disputes_and_cancellations() -> None:
    """Verifies dispute and cancellation accounting."""
    txs = [
        BuyerTransactionRecord(
            transaction_id="t1",
            buyer_id="buyer_risky",
            commodity_id="tomato",
            order_date=date(2024, 8, 1),
            agreed_quantity_kg=1000.0,
            delivered_quantity_kg=0.0,
            agreed_price_per_kg=25.0,
            fulfillment_status="CANCELLED",
            payment_status="PENDING",
            dispute_status=True,
        ),
        BuyerTransactionRecord(
            transaction_id="t2",
            buyer_id="buyer_risky",
            commodity_id="tomato",
            order_date=date(2024, 8, 5),
            agreed_quantity_kg=2000.0,
            delivered_quantity_kg=2000.0,
            agreed_price_per_kg=25.0,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=date(2024, 8, 12),
            actual_payment_date=date(2024, 8, 12),
            dispute_status=False,
        ),
        BuyerTransactionRecord(
            transaction_id="t3",
            buyer_id="buyer_risky",
            commodity_id="tomato",
            order_date=date(2024, 8, 10),
            agreed_quantity_kg=1000.0,
            delivered_quantity_kg=1000.0,
            agreed_price_per_kg=25.0,
            fulfillment_status="FULFILLED",
            payment_status="PAID_ON_TIME",
            agreed_payment_due_date=date(2024, 8, 17),
            actual_payment_date=date(2024, 8, 17),
            dispute_status=False,
        ),
    ]
    metrics = BuyerReliabilityEngine.calculate("buyer_risky", txs)

    assert metrics.sample_size == 3
    assert metrics.cancellation_rate == pytest.approx(1 / 3, rel=1e-2)
    assert metrics.dispute_rate == pytest.approx(1 / 3, rel=1e-2)
    assert metrics.fulfilled_orders == 2
