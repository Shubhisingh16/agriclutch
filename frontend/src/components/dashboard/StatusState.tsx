"use client";

import React from "react";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading market data...",
  className = "",
}) => {
  return (
    <div
      className={`p-8 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col items-center justify-center text-center space-y-3 ${className}`}
    >
      <div className="relative w-8 h-8">
        <div className="w-8 h-8 rounded-full border-2 border-emerald-500/20 border-t-emerald-400 animate-spin" />
      </div>
      <p className="text-xs font-mono text-zinc-400">{message}</p>
    </div>
  );
};

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No Observations Found",
  message = "No observations available for this selection.",
  actionText,
  onAction,
  className = "",
}) => {
  return (
    <div
      className={`p-8 rounded-2xl bg-zinc-900/30 border border-dashed border-zinc-800 flex flex-col items-center justify-center text-center space-y-3 ${className}`}
    >
      <div className="text-3xl text-zinc-600">📊</div>
      <h4 className="text-sm font-semibold text-zinc-300">{title}</h4>
      <p className="text-xs text-zinc-400 max-w-sm">{message}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-2 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-200 border border-zinc-700 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Market Data Unavailable",
  message = "Unable to fetch agricultural market observations. Please verify API service connectivity.",
  onRetry,
  className = "",
}) => {
  return (
    <div
      className={`p-6 rounded-2xl bg-rose-950/20 border border-rose-800/40 flex flex-col items-center justify-center text-center space-y-3 ${className}`}
    >
      <div className="text-2xl text-rose-400">⚠️</div>
      <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
      <p className="text-xs text-rose-300/80 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3.5 py-1.5 rounded-lg bg-rose-900/40 hover:bg-rose-800/50 text-xs font-medium text-rose-200 border border-rose-700/50 transition-colors"
        >
          Retry Request
        </button>
      )}
    </div>
  );
};
