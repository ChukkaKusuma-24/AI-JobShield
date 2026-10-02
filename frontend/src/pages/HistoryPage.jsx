import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { listHistory, deleteHistoryItem } from '../api/client';
import { riskBadgeClass } from '../utils/helpers';

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [risk, setRisk] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');

  const fetchHistory = useCallback(() => {
    setLoading(true);
    setError('');
    const params = { page, limit: 10 };
    if (risk) params.risk_level = risk;
    listHistory(params)
      .then((d) => {
        setItems(d.items || []);
        setTotal(d.total || 0);
      })
      .catch((e) => setError(e.message || 'Failed to fetch scan history.'))
      .finally(() => setLoading(false));
  }, [page, risk]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  async function handleDelete(id, title) {
    if (!window.confirm(`Are you sure you want to delete the analysis for "${title || 'this job'}"?`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteHistoryItem(id);
      setSuccessMsg('Analysis record deleted.');
      setTimeout(() => setSuccessMsg(''), 4000);
      fetchHistory();
    } catch (e) {
      setError(e.message || 'Failed to delete record.');
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 animate-fade-up">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">Analysis History</h1>
          <p className="text-sm text-ink/60">
            Secure, persistent record of your completed job scans stored in the database.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div>
            <label className="label" htmlFor="risk">
              Filter risk
            </label>
            <select
              id="risk"
              className="input !w-auto"
              value={risk}
              onChange={(e) => {
                setPage(1);
                setRisk(e.target.value);
              }}
            >
              <option value="">All Risks</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>
          </div>
          <button
            type="button"
            className="btn-secondary self-end"
            onClick={fetchHistory}
            disabled={loading}
            title="Refresh history from server"
          >
            {loading ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {successMsg ? (
        <div className="rounded-lg border border-safe/30 bg-safe/10 px-4 py-3 text-sm text-safe">
          {successMsg}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      ) : null}

      <div className="card-panel overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="border-b border-ink/10 text-ink/50">
              <th className="py-3">Job Title</th>
              <th className="py-3">Company</th>
              <th className="py-3">Score</th>
              <th className="py-3">Risk Level</th>
              <th className="py-3">Source</th>
              <th className="py-3">Date</th>
              <th className="py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-ink/60">
                  <div className="flex items-center justify-center gap-2">
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-accent border-r-transparent"></span>
                    <span>Loading analysis history from database…</span>
                  </div>
                </td>
              </tr>
            ) : items.length > 0 ? (
              items.map((a) => (
                <tr key={a.analysis_id || a.id} className="border-b border-ink/5 transition-colors hover:bg-mist/40">
                  <td className="py-3">
                    <Link
                      className="font-medium text-accent hover:underline"
                      to={`/result/${a.analysis_id || a.id}`}
                    >
                      {a.title || 'Untitled Posting'}
                    </Link>
                  </td>
                  <td className="py-3 text-ink/80">{a.company_name || '—'}</td>
                  <td className="py-3 font-semibold">{a.trust_score}/100</td>
                  <td className="py-3">
                    <span className={riskBadgeClass(a.risk_level)}>{a.risk_level}</span>
                  </td>
                  <td className="py-3">
                    <span className="rounded bg-ink/5 px-2 py-0.5 text-xs text-ink/70 uppercase">
                      {a.source || 'manual'}
                    </span>
                  </td>
                  <td className="py-3 text-ink/50">
                    {a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        to={`/result/${a.analysis_id || a.id}`}
                        className="rounded px-2.5 py-1 text-xs font-medium text-accent hover:bg-accent/10"
                      >
                        View
                      </Link>
                      <button
                        type="button"
                        onClick={() => handleDelete(a.analysis_id || a.id, a.title)}
                        disabled={deletingId === (a.analysis_id || a.id)}
                        className="rounded px-2.5 py-1 text-xs font-medium text-danger hover:bg-danger/10 disabled:opacity-50"
                      >
                        {deletingId === (a.analysis_id || a.id) ? 'Deleting…' : 'Delete'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="py-12 text-center text-ink/60">
                  <div className="mx-auto max-w-sm space-y-2">
                    <p className="font-semibold text-ink/80">No scan history found</p>
                    <p className="text-xs text-ink/50">
                      {risk
                        ? `No ${risk} risk analyses recorded yet.`
                        : "You haven't analyzed any job postings yet. Analyzed jobs will persist in your database history."}
                    </p>
                    <div className="pt-2">
                      <Link to="/analyze" className="btn-primary text-xs">
                        Analyze a Job Now
                      </Link>
                    </div>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!loading && total > 10 ? (
        <div className="flex items-center justify-between">
          <button
            type="button"
            className="btn-secondary"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </button>
          <span className="text-sm text-ink/60">
            Page {page} of {Math.ceil(total / 10)} ({total} total analyses)
          </span>
          <button
            type="button"
            className="btn-secondary"
            disabled={page * 10 >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      ) : null}
    </div>
  );
}
