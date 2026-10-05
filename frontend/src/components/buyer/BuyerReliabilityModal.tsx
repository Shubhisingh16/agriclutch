import React, { useEffect, useState } from "react";
import { ReliabilityMetrics } from "@/types/buyer";
import { getBuyerReliability } from "@/lib/api/buyers";

interface BuyerReliabilityModalProps {
  buyerId: string;
  buyerName: string;
  onClose: () => void;
}

export const BuyerReliabilityModal: React.FC<BuyerReliabilityModalProps> = ({
  buyerId,
  buyerName,
  onClose,
}) => {
  const [metrics, setMetrics] = useState<ReliabilityMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    getBuyerReliability(buyerId)
      .then((data) => {
        if (!isMounted) return;
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || "Failed to load reliability metrics");
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [buyerId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl bg-zinc-900 border border-zinc-800 p-6 shadow-2xl space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-zinc-800/80 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-white tracking-tight">{buyerName}</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                AUDIT LOG
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-1 font-mono">
              Empirical Performance Analytics • Historical Transactions
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="py-12 text-center text-xs font-mono text-zinc-400 animate-pulse">
            Auditing historical transaction records...
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 font-mono">
            {error}
          </div>
        ) : metrics ? (
          <div className="space-y-5">
            {/* Statistical Gating Notice */}
            <div
              className={`p-3 rounded-xl border text-xs font-mono ${
                metrics.status === "CALCULATED"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-amber-500/10 border-amber-500/30 text-amber-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold uppercase tracking-wider">
                  Audit Status: {metrics.status}
                </span>
                <span className="px-2 py-0.5 rounded bg-zinc-950/60 text-zinc-300 text-[10px]">
                  N = {metrics.sample_size} past orders
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 mt-1.5 leading-relaxed">
                {metrics.audit_note}
              </p>
            </div>

            {/* Empirical Performance Metrics Grid */}
            {metrics.status === "CALCULATED" ? (
              <div className="grid grid-cols-2 gap-3.5">
                <div className="p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400 uppercase">Fulfillment Rate</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    {metrics.fulfillment_rate !== null && metrics.fulfillment_rate !== undefined
                      ? `${(metrics.fulfillment_rate * 100).toFixed(1)}%`
                      : "N/A"}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5">Delivered vs agreed volume</div>
                </div>

                <div className="p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400 uppercase">Cancellation Rate</div>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      (metrics.cancellation_rate || 0) > 0.1 ? "text-amber-400" : "text-zinc-200"
                    }`}
                  >
                    {metrics.cancellation_rate !== null && metrics.cancellation_rate !== undefined
                      ? `${(metrics.cancellation_rate * 100).toFixed(1)}%`
                      : "N/A"}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5">Ratio of orders cancelled</div>
                </div>

                <div className="p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400 uppercase">Avg Payment Delay</div>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      (metrics.avg_payment_delay_days || 0) > 2 ? "text-amber-400" : "text-emerald-400"
                    }`}
                  >
                    {metrics.avg_payment_delay_days !== null && metrics.avg_payment_delay_days !== undefined
                      ? `${metrics.avg_payment_delay_days.toFixed(1)} days`
                      : "N/A"}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5">Settlement past due date</div>
                </div>

                <div className="p-3.5 rounded-xl bg-zinc-950/60 border border-zinc-800">
                  <div className="text-[11px] font-mono text-zinc-400 uppercase">Dispute Frequency</div>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      (metrics.dispute_rate || 0) > 0 ? "text-red-400" : "text-emerald-400"
                    }`}
                  >
                    {metrics.dispute_rate !== null && metrics.dispute_rate !== undefined
                      ? `${(metrics.dispute_rate * 100).toFixed(1)}%`
                      : "0.0%"}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5">Formal grade/payment disputes</div>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-xl bg-zinc-950/50 border border-zinc-800 text-center space-y-2">
                <div className="text-2xl">⏳</div>
                <div className="text-xs font-semibold text-zinc-300">Insufficient Transaction History</div>
                <p className="text-[11px] text-zinc-400 max-w-sm mx-auto">
                  AgriClutch enforces strict statistical gating (N &ge; 3 completed transactions) before computing
                  performance indicators. No default or fabricated trust scores are provided.
                </p>
              </div>
            )}

            {/* Methodology & Non-Normative Disclosure */}
            <div className="p-3.5 rounded-xl bg-zinc-950/40 border border-zinc-800/80 text-[11px] text-zinc-400 space-y-1">
              <div className="font-semibold text-zinc-300 font-mono text-[10px] uppercase">
                Methodological Disclosure:
              </div>
              <p>
                Metrics are computed strictly from completed transaction receipts and verified payment settlement timestamps.
                No arbitrary reputation ratings, user star reviews, or algorithmic black-box scores are used.
              </p>
            </div>
          </div>
        ) : null}

        {/* Footer */}
        <div className="flex justify-end pt-2 border-t border-zinc-800/80">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold transition-colors"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
};
