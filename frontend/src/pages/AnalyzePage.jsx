import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeJob } from '../api/client';
import AnalysisResultView from '../components/AnalysisResultView';
import { SAMPLE_LEGIT, SAMPLE_SCAM } from '../utils/helpers';

const empty = {
  title: '',
  company_name: '',
  description: '',
  salary: '',
  email: '',
  url: '',
  location: '',
  job_type: 'Full-time',
};

export default function AnalyzePage() {
  const [form, setForm] = useState(empty);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  function update(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  function validate() {
    const errs = {};
    if (!form.title.trim()) errs.title = 'Required';
    if (!form.company_name.trim()) errs.company_name = 'Required';
    if (form.description.trim().length < 30) errs.description = 'At least 30 characters';
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach((k) => {
        if (payload[k] === '') payload[k] = undefined;
      });
      const data = await analyzeJob(payload);
      setResult(data);
      navigate(`/result/${data.analysis_id}`, { state: { analysis: data } });
    } catch (ex) {
      setError(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">Analyze job posting</h1>
        <p className="text-sm text-ink/60">
          Runs ML prediction, rule-based red flags, and heuristic checks (URL / company / duplicates).
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-secondary" onClick={() => setForm(SAMPLE_SCAM)}>
          Load sample scam
        </button>
        <button type="button" className="btn-secondary" onClick={() => setForm(SAMPLE_LEGIT)}>
          Load sample legit
        </button>
      </div>

      <form className="card-panel grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
        {[
          ['title', 'Job title', 'text'],
          ['company_name', 'Company name', 'text'],
          ['salary', 'Salary', 'text'],
          ['email', 'Contact email', 'email'],
          ['url', 'Website / URL', 'url'],
          ['location', 'Location', 'text'],
        ].map(([name, label, type]) => (
          <div key={name} className={name === 'title' || name === 'company_name' ? 'sm:col-span-1' : ''}>
            <label className="label" htmlFor={name}>
              {label}
            </label>
            <input
              id={name}
              name={name}
              type={type}
              className="input"
              value={form[name]}
              onChange={update}
            />
            {fieldErrors[name] ? <p className="mt-1 text-xs text-danger">{fieldErrors[name]}</p> : null}
          </div>
        ))}
        <div>
          <label className="label" htmlFor="job_type">
            Job type
          </label>
          <select id="job_type" name="job_type" className="input" value={form.job_type} onChange={update}>
            {['Full-time', 'Part-time', 'Internship', 'Contract', 'Freelance'].map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="label" htmlFor="description">
            Job description
          </label>
          <textarea
            id="description"
            name="description"
            className="input min-h-[160px]"
            value={form.description}
            onChange={update}
          />
          {fieldErrors.description ? (
            <p className="mt-1 text-xs text-danger">{fieldErrors.description}</p>
          ) : null}
        </div>
        {error ? <p className="sm:col-span-2 text-sm text-danger">{error}</p> : null}
        <div className="sm:col-span-2">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze job'}
          </button>
        </div>
      </form>

      {result ? <AnalysisResultView data={result} /> : null}
    </div>
  );
}
