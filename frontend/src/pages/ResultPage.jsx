import { useEffect, useState } from 'react';
import { useLocation, useParams, Link } from 'react-router-dom';
import { getHistoryItem } from '../api/client';
import AnalysisResultView from '../components/AnalysisResultView';

export default function ResultPage() {
  const { id } = useParams();
  const location = useLocation();
  const [data, setData] = useState(location.state?.analysis || null);
  const [loading, setLoading] = useState(!location.state?.analysis);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    // Always fetch fresh analysis from backend to ensure all database-persisted fields are current
    setLoading(true);
    getHistoryItem(id)
      .then((item) => {
        setData(item);
        setError('');
      })
      .catch((e) => {
        // If fetch fails but we already have state, use it; otherwise display error
        if (location.state?.analysis) {
          setData(location.state.analysis);
        } else {
          setError(e.message || 'Failed to retrieve analysis record from database.');
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading && !data) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-accent border-r-transparent"></div>
        <p className="mt-3 text-sm text-ink/60">Loading analysis from database…</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12">
        <div className="rounded-lg border border-danger/30 bg-danger/10 p-6 text-center">
          <p className="font-semibold text-danger">{error}</p>
          <p className="mt-2 text-xs text-ink/60">
            This analysis may not exist or may belong to another user account.
          </p>
          <div className="mt-4">
            <Link to="/history" className="btn-secondary text-xs">
              Return to Analysis History
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">Analysis Result</h1>
          <p className="text-sm text-ink/60">
            Comprehensive multi-dimensional trust evaluation persisted to database.
          </p>
        </div>
        <Link to="/history" className="btn-secondary text-sm">
          ← Back to History
        </Link>
      </div>
      <AnalysisResultView data={data} />
    </div>
  );
}
