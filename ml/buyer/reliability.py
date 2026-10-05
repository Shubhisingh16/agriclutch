"""
AgriClutch Buyer Reliability Analytics Subsystem.
Calculates transparent, auditable historical transaction metrics:
fulfillment rates, cancellation rates, payment delays, and dispute frequencies.
Enforces statistical sample size gating (N >= 3) and strictly forbids black-box scoring.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""


from ml.buyer.contracts import (
    BuyerTransactionRecord,
    EconomicProvenance,
    ProvenanceStatus,
    ReliabilityMetrics,
    ReliabilityStatus,
)


class BuyerReliabilityEngine:
    """
    Computes objective commercial performance indicators from immutable transaction logs.
    Never fabricates default scores; fails safely to INSUFFICIENT_HISTORY or UNAVAILABLE.
    """

    MINIMUM_SAMPLE_SIZE = 3

    @classmethod
    def calculate(
        cls,
        buyer_id: str,
        transactions: list[BuyerTransactionRecord],
    ) -> ReliabilityMetrics:
        """
        Calculates empirical performance indicators for a single buyer.
        """
        b_txs = [t for t in transactions if t.buyer_id == buyer_id]
        n_total = len(b_txs)

        if n_total == 0:
            return ReliabilityMetrics(
                buyer_id=buyer_id,
                status=ReliabilityStatus.UNAVAILABLE,
                sample_size=0,
                fulfilled_orders=0,
                confirmed_orders=0,
                fulfillment_rate=None,
                cancelled_orders=0,
                cancellation_rate=None,
                quantity_fulfillment_ratio=None,
                average_payment_delay_days=None,
                disputed_orders=0,
                dispute_rate=None,
                provenance=EconomicProvenance(
                    source_name="TRANSACTION_AUDIT_LOG",
                    status=ProvenanceStatus.UNAVAILABLE,
                    is_demo=False,
                    description=f"Zero transaction records on file for buyer '{buyer_id}'.",
                ),
            )

        if n_total < cls.MINIMUM_SAMPLE_SIZE:
            return ReliabilityMetrics(
                buyer_id=buyer_id,
                status=ReliabilityStatus.INSUFFICIENT_HISTORY,
                sample_size=n_total,
                fulfilled_orders=sum(1 for t in b_txs if t.fulfillment_status == "FULFILLED"),
                confirmed_orders=n_total,
                fulfillment_rate=None,
                cancelled_orders=sum(1 for t in b_txs if t.fulfillment_status == "CANCELLED"),
                cancellation_rate=None,
                quantity_fulfillment_ratio=None,
                average_payment_delay_days=None,
                disputed_orders=sum(1 for t in b_txs if t.dispute_status),
                dispute_rate=None,
                provenance=EconomicProvenance(
                    source_name="TRANSACTION_AUDIT_LOG",
                    status=ProvenanceStatus.DEMO if any(t.provenance.is_demo for t in b_txs) else ProvenanceStatus.EMPIRICAL,
                    is_demo=any(t.provenance.is_demo for t in b_txs),
                    description=(
                        f"Sample size ({n_total} transactions) is below minimum threshold of "
                        f"{cls.MINIMUM_SAMPLE_SIZE} required for reliable performance metrics."
                    ),
                ),
            )

        # Sufficient sample size (N >= 3)
        confirmed_orders = n_total
        fulfilled_orders = sum(1 for t in b_txs if t.fulfillment_status == "FULFILLED")
        cancelled_orders = sum(1 for t in b_txs if t.fulfillment_status == "CANCELLED")
        disputed_orders = sum(1 for t in b_txs if t.dispute_status)

        fulfillment_rate = fulfilled_orders / confirmed_orders if confirmed_orders > 0 else 0.0
        cancellation_rate = cancelled_orders / confirmed_orders if confirmed_orders > 0 else 0.0
        dispute_rate = disputed_orders / confirmed_orders if confirmed_orders > 0 else 0.0

        # Quantity fulfillment ratio on delivered/partial orders
        qty_ratios = [
            min(1.0, t.delivered_quantity_kg / t.agreed_quantity_kg)
            for t in b_txs
            if t.agreed_quantity_kg > 0 and t.fulfillment_status in ["FULFILLED", "PARTIAL"]
        ]
        q_fulfillment_ratio = sum(qty_ratios) / len(qty_ratios) if qty_ratios else None

        # Payment delays on settled orders with documented dates
        payment_delays: list[float] = []
        for t in b_txs:
            if t.actual_payment_date and t.agreed_payment_due_date:
                delay = (t.actual_payment_date - t.agreed_payment_due_date).days
                # Delay is strictly >= 0 (early payment counts as 0 delay)
                payment_delays.append(float(max(0, delay)))

        avg_payment_delay = sum(payment_delays) / len(payment_delays) if payment_delays else None

        dates = [t.order_date for t in b_txs]
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None
        all_demo = all(t.provenance.is_demo for t in b_txs)

        prov = EconomicProvenance(
            source_name="TRANSACTION_AUDIT_LOG",
            status=ProvenanceStatus.DEMO if all_demo else ProvenanceStatus.EMPIRICAL,
            is_demo=all_demo,
            description=f"Performance metrics computed over {confirmed_orders} verified historical transactions.",
        )

        return ReliabilityMetrics(
            buyer_id=buyer_id,
            status=ReliabilityStatus.CALCULATED,
            sample_size=confirmed_orders,
            fulfilled_orders=fulfilled_orders,
            confirmed_orders=confirmed_orders,
            fulfillment_rate=fulfillment_rate,
            cancelled_orders=cancelled_orders,
            cancellation_rate=cancellation_rate,
            quantity_fulfillment_ratio=q_fulfillment_ratio,
            average_payment_delay_days=avg_payment_delay,
            disputed_orders=disputed_orders,
            dispute_rate=dispute_rate,
            time_window_start=min_date,
            time_window_end=max_date,
            provenance=prov,
        )
