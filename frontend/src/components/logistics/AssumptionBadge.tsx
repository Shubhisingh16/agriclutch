"use client";

import React from "react";

interface AssumptionBadgeProps {
  status: string;
  isDemo?: boolean;
  className?: string;
}

export const AssumptionBadge: React.FC<AssumptionBadgeProps> = ({
  status,
  isDemo = true,
  className = "",
}) => {
  const normStatus = status.toUpperCase();

  if (isDemo || normStatus === "DEMO" || normStatus === "DEMO_ASSUMPTION") {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
        title="Configured synthetic demo assumption. Not empirically certified physical infrastructure."
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5 animate-pulse" />
        DEMO ASSUMPTION
      </span>
    );
  }

  if (normStatus === "CONFIGURED") {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30 ${className}`}
        title="Explicit system assumption configured without live telemetry."
      >
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mr-1.5" />
        CONFIGURED
      </span>
    );
  }

  if (normStatus === "EMPIRICAL" || normStatus === "COMPLETE_EMPIRICAL") {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${className}`}
        title="Empirically documented route or transit measurement."
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5" />
        EMPIRICAL
      </span>
    );
  }

  if (normStatus === "INCOMPLETE") {
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-red-500/10 text-red-400 border border-red-500/30 ${className}`}
        title="Missing one or more required physical or economic cost parameters."
      >
        <span className="w-1.5 h-1.5 rounded-full bg-red-400 mr-1.5" />
        INCOMPLETE
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-800 text-zinc-400 border border-zinc-700 ${className}`}
    >
      {normStatus}
    </span>
  );
};
