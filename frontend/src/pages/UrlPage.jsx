import { useState } from 'react';
import { analyzeUrl } from '../api/client';
import { riskBadgeClass } from '../utils/helpers';

export default function UrlPage() {
  const [url, setUrl] = useState('');
  const [company, setCompany] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      setResult(
        await analyzeUrl({
          url,
          company_name: company || undefined,
        })
      );
    } catch (ex) {
      setError(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">URL checker</h1>
        <p className="text-sm text-ink/60">
          Purely local heuristics — does not fetch the URL. Suspicious characteristics ≠ proven malware.
        </p>
      </div>
      <form className="card-panel space-y-3" onSubmit={onSubmit}>
        <div>
          <label className="label" htmlFor="url">
            URL
          </label>
          <input id="url" className="input" required value={url} onChange={(e) => setUrl(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="company">
            Company name (optional)
          </label>
          <input
            id="company"
            className="input"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </div>
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Checking…' : 'Analyze URL'}
        </button>
      </form>
      {result ? (
        <div className="card-panel space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className={riskBadgeClass(result.risk_level)}>{result.risk_level}</span>
            <span className="text-sm text-ink/50">score {result.risk_score}</span>
          </div>
          <p className="text-sm break-all text-ink/70">{result.url}</p>
          <p className="text-sm text-ink/70">{result.explanation}</p>
          <ul className="space-y-2">
            {(result.indicators || []).map((i) => (
              <li key={i.id} className="rounded border border-ink/10 px-3 py-2 text-sm">
                <span className="font-semibold">{i.label}</span>
                <span className="ml-2 text-xs uppercase text-ink/45">{i.severity}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
