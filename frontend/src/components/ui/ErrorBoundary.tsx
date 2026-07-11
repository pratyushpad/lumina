import { AlertTriangle, RotateCcw } from "lucide-react";
import { Component, type ReactNode } from "react";
import { GradientButton } from "./GradientButton";

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown) {
    console.error("UI error:", error, info);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="flex h-screen items-center justify-center bg-background px-6">
        <div className="hairline bg-surface max-w-md p-8">
          <AlertTriangle className="mb-4 text-rose-400" size={28} />
          <div className="text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
            Error
          </div>
          <h2 className="mt-2 font-display text-2xl font-semibold tracking-tight2">
            Something broke
          </h2>
          <p className="mt-3 text-sm text-textSecondary">
            {this.state.error.message || "An unexpected error occurred."}
          </p>
          <pre className="mt-4 max-h-32 overflow-auto hairline bg-card p-3 text-left text-[10px] font-mono text-textMuted">
            {this.state.error.stack?.split("\n").slice(0, 6).join("\n")}
          </pre>
          <GradientButton className="mt-6" onClick={this.reset}>
            <RotateCcw size={13} /> Try again
          </GradientButton>
        </div>
      </div>
    );
  }
}
