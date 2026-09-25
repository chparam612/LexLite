import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackMessage?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 m-4 max-w-lg mx-auto bg-white rounded-xl shadow-sm border border-red-200 text-center">
          <div className="w-12 h-12 bg-red-50 text-red-600 rounded-full flex items-center justify-center mx-auto mb-3">
            <AlertCircle className="w-6 h-6" aria-hidden="true" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 mb-1">
            Something went wrong
          </h2>
          <p className="text-sm text-slate-600 mb-4">
            {this.props.fallbackMessage ||
              'A rendering error occurred in this view. You can retry without reloading the entire application.'}
          </p>
          {this.state.error?.message && (
            <div className="text-xs font-mono bg-slate-50 text-slate-700 p-2 rounded border border-slate-200 mb-4 text-left overflow-auto max-h-28">
              {this.state.error.message}
            </div>
          )}
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={this.handleReset}
              aria-label="Try recovering from error"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              aria-label="Reload entire page"
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
