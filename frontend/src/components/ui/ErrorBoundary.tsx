import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) console.error('UI error', error, info.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    if (this.props.fallback) return this.props.fallback;
    return (
      <div role="alert" className="mx-auto mt-16 max-w-md p-6 text-center">
        <AlertTriangle className="mx-auto mb-3 h-10 w-10 text-amber-300" aria-hidden />
        <h2 className="text-xl font-semibold">Something went wrong</h2>
        <p className="mt-2 text-sm text-ink-muted">An unexpected error occurred while showing this screen.</p>
        <div className="mt-5 flex justify-center gap-2">
          <button type="button" className="chip" onClick={this.reset}>
            Try again
          </button>
          <button type="button" className="chip" onClick={() => window.location.assign('/')}>
            Go home
          </button>
        </div>
      </div>
    );
  }
}
