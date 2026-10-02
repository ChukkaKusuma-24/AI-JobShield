import { useState } from 'react';
import { verifyCompany } from '../api/client';
import { companyStatusClass } from '../utils/helpers';

export default function CompanyPage() {
  const [form, setForm] = useState({ company_name: '', email: '', website: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach((k) => {
        if (!payload[k]) delete payload[k];
      });
      setResult(await verifyCompany(payload));
    } catch (ex) {
      setError(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">Company verification</h1>
        <p className="text-sm text-ink/60">
          Local consistency checks; optional online lookup if enabled in .env. Unable to verify ≠ fake.
        </p>
      </div>
      <form className="card-panel space-y-3" onSubmit={onSubmit}>
        {['company_name', 'email', 'website'].map((k) => (
          <div key={k}>
            <label className="label" htmlFor={k}>
              {k === 'company_name' ? 'Company name' : k}
            </label>
            <input
              id={k}
              className="input"
              required={k === 'company_name'}
              value={form[k]}
              onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))}
            />
          </div>
        ))}
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Checking…' : 'Verify company'}
        </button>
      </form>
      {result ? (
        <div className="card-panel space-y-3">
          <span className={companyStatusClass(result.status)}>{result.status}</span>
          <p className="text-sm text-ink/70">{result.summary}</p>
          <p className="text-xs text-ink/50">
            Online lookup performed: {result.online_lookup_performed ? 'yes' : 'no'}
          </p>
          <ul className="space-y-2 text-sm">
            {(result.checks || []).map((c) => (
              <li key={c.name} className="rounded border border-ink/10 p-2">
                <div className="font-semibold">
                  {c.name}{' '}
                  <span className="font-normal text-ink/50">
                    (
                    {c.passed === true ? 'passed' : c.passed === false ? 'failed' : 'n/a'}
                    )
                  </span>
                </div>
                <div className="text-ink/60">{c.detail}</div>
              </li>
            ))}
          </ul>
          <p className="rounded bg-mist px-3 py-2 text-xs text-ink/60">
            Unable to verify does not mean the company is fake. Always use official channels.
          </p>
        </div>
      ) : null}
    </div>
  );
}
