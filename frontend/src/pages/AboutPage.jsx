import { useEffect, useState } from 'react';
import { health } from '../api/client';

export default function AboutPage() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    health()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">About AI JobShield</h1>
        <p className="mt-2 text-ink/70">
          Intelligent Fake Job & Internship Detection System — a fully local college mini project
          (React + FastAPI + SQLite). Cloud deployment is a future scope item, not part of this build.
        </p>
      </div>

      <section className="card-panel space-y-2 text-sm text-ink/75">
        <h2 className="font-display text-xl font-semibold text-ink">Disclaimer</h2>
        <p>
          AI JobShield gives guidance, not a verdict. Always verify through official channels. The
          system never labels a posting as simply &ldquo;FAKE&rdquo; or &ldquo;REAL&rdquo;. Unable to
          verify a company does not mean it is fake.
        </p>
      </section>

      <section className="card-panel space-y-2 text-sm text-ink/75">
        <h2 className="font-display text-xl font-semibold text-ink">How scoring works</h2>
        <ol className="list-decimal space-y-1 pl-5">
          <li>
            <strong>ML prediction</strong> — TF-IDF + Logistic Regression (or Naive Bayes) on demo
            synthetic text; probability of suspicious class.
          </li>
          <li>
            <strong>Rule-based red flags</strong> — fees, money asks, sensitive data, urgency,
            WhatsApp-only, free email, vague JD, etc., with evidence snippets.
          </li>
          <li>
            <strong>Heuristics</strong> — URL characteristics, company domain/email consistency,
            duplicate similarity against local history/reports.
          </li>
        </ol>
        <p>
          Formula: <code>rule_risk = clamp(sum(flags) − bonus, 0, 100)</code>;{' '}
          <code>combined = 0.6×rule + 0.4×ml</code>; <code>trust = 100 − combined</code>; critical
          flags cap trust at 45.
        </p>
      </section>

      <section className="card-panel space-y-2 text-sm text-ink/75">
        <h2 className="font-display text-xl font-semibold text-ink">ML metrics note</h2>
        <p>
          Metrics come from a small synthetic demo dataset and do NOT represent real-world
          performance. Swap in a real CSV later via{' '}
          <code>python ml/train.py --data your.csv</code>.
        </p>
      </section>

      <section className="card-panel space-y-2 text-sm text-ink/75">
        <h2 className="font-display text-xl font-semibold text-ink">Privacy</h2>
        <p>
          Data stays on your laptop (SQLite + local uploads). Only fields needed for analysis and
          history are stored. Passwords are bcrypt-hashed. Do not paste secrets you would not keep
          offline.
        </p>
      </section>

      <section className="card-panel space-y-2 text-sm text-ink/75">
        <h2 className="font-display text-xl font-semibold text-ink">Local service status</h2>
        {status ? (
          <ul className="space-y-1">
            <li>API: {status.status}</li>
            <li>ML available: {String(status.ml_available)}</li>
            <li>OCR available: {String(status.ocr_available)}</li>
            <li>Online company lookup: {String(status.online_lookup_enabled)}</li>
          </ul>
        ) : (
          <p>Could not reach backend health endpoint. Start the API on port 8000.</p>
        )}
      </section>

      <section className="card-panel space-y-2 text-sm text-ink/75">
        <h2 className="font-display text-xl font-semibold text-ink">Risks & limitations</h2>
        <p>
          False positives/negatives, OCR noise, evolving scam tactics, and optional internet lookups
          that may fail offline. Treat results as a teaching aid for scam awareness — not a
          compliance or legal decision system.
        </p>
      </section>
    </div>
  );
}
