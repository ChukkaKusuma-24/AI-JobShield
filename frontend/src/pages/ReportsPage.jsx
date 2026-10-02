import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { createReport, listReports } from '../api/client';

export default function ReportsPage() {
  const location = useLocation();
  const prefill = location.state?.prefill || {};
  const [form, setForm] = useState({
    job_title: prefill.job_title || '',
    company_name: prefill.company_name || '',
    description: prefill.description || '',
    url: '',
    reason: '',
  });
  const [file, setFile] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  async function load(p = page) {
    try {
      const data = await listReports({ page: p, limit: 8 });
      setItems(data.items);
      setTotal(data.total);
    } catch (ex) {
      setError(ex.message);
    }
  }

  useEffect(() => {
    load(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function onSubmit(e) {
    e.preventDefault();
    setError('');
    setMsg('');
    setLoading(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => {
        if (v) fd.append(k, v);
      });
      if (file) fd.append('screenshot', file);
      await createReport(fd);
      setMsg('Report submitted.');
      setForm({ job_title: '', company_name: '', description: '', url: '', reason: '' });
      setFile(null);
      setPage(1);
      await load(1);
    } catch (ex) {
      setError(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">Scam reports</h1>
        <p className="text-sm text-ink/60">Community reports stored locally for duplicate detection demos.</p>
      </div>

      <form className="card-panel grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
        <h2 className="sm:col-span-2 font-display text-lg font-semibold">Submit a report</h2>
        {[
          ['job_title', 'Job title'],
          ['company_name', 'Company'],
          ['url', 'URL (optional)'],
        ].map(([k, label]) => (
          <div key={k}>
            <label className="label" htmlFor={k}>
              {label}
            </label>
            <input
              id={k}
              className="input"
              required={k !== 'url'}
              value={form[k]}
              onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))}
            />
          </div>
        ))}
        <div className="sm:col-span-2">
          <label className="label" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            className="input min-h-[100px]"
            required
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>
        <div className="sm:col-span-2">
          <label className="label" htmlFor="reason">
            Why is this suspicious?
          </label>
          <textarea
            id="reason"
            className="input min-h-[80px]"
            required
            value={form.reason}
            onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
          />
        </div>
        <div className="sm:col-span-2">
          <label className="label" htmlFor="shot">
            Optional screenshot
          </label>
          <input
            id="shot"
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <p className="mt-1 text-xs text-ink/45">Report date is set automatically on the server.</p>
        </div>
        {error ? <p className="sm:col-span-2 text-sm text-danger">{error}</p> : null}
        {msg ? <p className="sm:col-span-2 text-sm text-safe">{msg}</p> : null}
        <div className="sm:col-span-2">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Submitting…' : 'Submit report'}
          </button>
        </div>
      </form>

      <div className="card-panel space-y-3">
        <h2 className="font-display text-lg font-semibold">Reports ({total})</h2>
        {items.map((r) => (
          <article key={r.id} className="rounded-lg border border-ink/10 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-semibold">
                {r.job_title} · {r.company_name}
              </h3>
              <span className="badge bg-ink/10 text-ink/60">{r.status}</span>
            </div>
            <p className="mt-1 text-sm text-ink/70">{r.description}</p>
            <p className="mt-1 text-xs text-ink/50">
              Reason: {r.reason}
              {r.report_date ? ` · ${new Date(r.report_date).toLocaleString()}` : ''}
            </p>
          </article>
        ))}
        <div className="flex gap-2">
          <button type="button" className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </button>
          <button
            type="button"
            className="btn-secondary"
            disabled={page * 8 >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
