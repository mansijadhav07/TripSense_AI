"use client";

import React from "react";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Filter out MetaMask and other browser extension errors
    const isExtensionError = 
      error.message.includes("addListener") ||
      error.message.includes("MetaMask") ||
      error.stack?.includes("chrome-extension://");
    
    if (!isExtensionError) {
      console.error("ErrorBoundary caught an error:", error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      // Check if it's a browser extension error - don't show error UI
      const isExtensionError = 
        this.state.error?.message.includes("addListener") ||
        this.state.error?.message.includes("MetaMask") ||
        this.state.error?.stack?.includes("chrome-extension://");

      if (isExtensionError) {
        // Silently recover from extension errors
        return this.props.children;
      }

      return (
        this.props.fallback || (
          <div className="max-w-7xl mx-auto px-4 py-16 text-center">
            <div className="bg-slate-900/60 p-8 rounded-2xl border border-red-500/20">
              <h2 className="text-2xl font-bold text-red-400 mb-4">Something went wrong</h2>
              <p className="text-slate-400 mb-6">{this.state.error?.message || "An unexpected error occurred"}</p>
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.reload();
                }}
                className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl transition"
              >
                Reload Page
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
