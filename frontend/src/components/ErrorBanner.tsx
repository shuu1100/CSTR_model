import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onRetry, onDismiss }) => {
  return (
    <div className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-4 text-rose-200 flex items-start justify-between shadow-lg backdrop-blur-sm">
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
        <div>
          <h4 className="text-sm font-semibold text-rose-300">Computation / Validation Error</h4>
          <p className="text-xs text-rose-200/90 mt-0.5 leading-relaxed font-mono">{message}</p>
        </div>
      </div>
      <div className="flex items-center space-x-2 ml-4">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center space-x-1 px-2.5 py-1 bg-rose-900/60 hover:bg-rose-900 border border-rose-700/60 rounded text-xs text-rose-200 font-medium transition"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="px-2 py-1 text-xs text-rose-400 hover:text-rose-200 transition"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
};
