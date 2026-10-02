import { useState } from 'react';
import { riskBadgeClass, severityClass, companyStatusClass, DISCLAIMER } from '../utils/helpers';
import TrustGauge from './TrustGauge';
import FeedbackWidget from './FeedbackWidget';
import { Link } from 'react-router-dom';

export default function AnalysisResultView({ data }) {
  if (!data) return null;
  const [showFullDesc, setShowFullDesc] = useState(false);
  const [showOcrText, setShowOcrText] = useState(false);

  const ml = data.ml || {};
  const breakdown = data.score_breakdown || {};
  const dimensions = breakdown.dimensions || {};
  const company = data.company_verification || {};
  const urlA = data.url_analysis || {};
  const dup = data.duplicate_result || {};

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Top Banner: Trust Score & Core Status */}
      <div className="card-panel grid gap-6 md:grid-cols-[200px_1fr] md:items-center">
        <TrustGauge score={data.trust_score} riskLevel={data.risk_level} />
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className={riskBadgeClass(data.risk_level)}>{data.risk_level} Risk</span>
            {data.title ? (
              <span className="text-sm font-medium text-ink/80">
                {data.title} · <span className="text-ink/60">{data.company_name}</span>
              </span>
            ) : null}
            {data.source ? (
              <span className="rounded bg-mist px-2 py-0.5 text-xs uppercase text-ink/60">
                Source: {data.source}
              </span>
            ) : null}
          </div>

          {/* Structured Explanation */}
          <div className="rounded-lg bg-mist/50 p-3 text-sm text-ink/80 whitespace-pre-line leading-relaxed">
            {data.explanation}
          </div>

          {breakdown.cap_applied ? (
            <div className="mt-3 rounded-md border border-warn/40 bg-warn/10 px-3 py-2 text-xs font-medium text-warn">
              🛡️ Evidence Cap Applied: {breakdown.cap_reason}
            </div>
          ) : null}

          <p className="mt-3 text-xs text-ink/50">
            {data.disclaimer || DISCLAIMER}
          </p>
        </div>
      </div>

      {/* 5-Dimensional Evidence-Based Scoring Card */}
      <section className="card-panel">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-ink/10 pb-3">
          <div>
            <h3 className="font-display text-lg font-semibold">Evidence-Based Trust Dimensions</h3>
            <p className="text-xs text-ink/50">
              Evaluated across 5 independent risk dimensions without blind name trust.
            </p>
          </div>
          <div className="text-right">
            <span className="text-xs uppercase text-ink/50">Overall Trust Score</span>
            <div className="font-display text-2xl font-bold text-accent">{data.trust_score}/100</div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {/* Dimension 1: Company Verification */}
          <div className="rounded-lg border border-ink/10 bg-mist/30 p-3">
            <div className="text-xs font-medium text-ink/50">1. Company Verification (25%)</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="font-display text-lg font-bold">
                {dimensions.company_verification?.score ?? 40}
                <span className="text-xs font-normal text-ink/40">/100</span>
              </span>
              <span className={companyStatusClass(company.status || dimensions.company_verification?.status)}>
                {company.status || dimensions.company_verification?.status || 'UNVERIFIED'}
              </span>
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-ink/10">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${Math.min(100, Math.max(0, dimensions.company_verification?.score ?? 40))}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-ink/60 line-clamp-2">
              {company.summary || 'Database and domain consistency check.'}
            </p>
          </div>

          {/* Dimension 2: Source & URL Credibility */}
          <div className="rounded-lg border border-ink/10 bg-mist/30 p-3">
            <div className="text-xs font-medium text-ink/50">2. Source / URL (20%)</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="font-display text-lg font-bold">
                {dimensions.source_credibility?.score ?? 50}
                <span className="text-xs font-normal text-ink/40">/100</span>
              </span>
              <span className="text-xs font-semibold text-ink/70">
                {urlA.url ? urlA.risk_level : (data.source || 'Neutral')}
              </span>
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-ink/10">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${Math.min(100, Math.max(0, dimensions.source_credibility?.score ?? 50))}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-ink/60 line-clamp-2">
              {urlA.url ? (urlA.explanation || 'URL verified.') : 'No URL provided (neutral unverified source).'}
            </p>
          </div>

          {/* Dimension 3: Job Posting Quality */}
          <div className="rounded-lg border border-ink/10 bg-mist/30 p-3">
            <div className="text-xs font-medium text-ink/50">3. Posting Quality (15%)</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="font-display text-lg font-bold">
                {dimensions.job_posting_quality?.score ?? 60}
                <span className="text-xs font-normal text-ink/40">/100</span>
              </span>
              <span className="text-xs text-ink/60">
                {(dimensions.job_posting_quality?.score ?? 60) >= 70 ? 'Detailed' : 'Standard'}
              </span>
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-ink/10">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${Math.min(100, Math.max(0, dimensions.job_posting_quality?.score ?? 60))}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-ink/60 line-clamp-2">
              Clarity of responsibilities, requirements, and realistic terms.
            </p>
          </div>

          {/* Dimension 4: Scam Detection */}
          <div className="rounded-lg border border-ink/10 bg-mist/30 p-3">
            <div className="text-xs font-medium text-ink/50">4. Scam Detection (30%)</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="font-display text-lg font-bold">
                {dimensions.scam_detection?.score ?? 100}
                <span className="text-xs font-normal text-ink/40">/100</span>
              </span>
              <span className="text-xs text-ink/60">
                {(data.red_flags || []).length} flag{(data.red_flags || []).length === 1 ? '' : 's'}
              </span>
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-ink/10">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${Math.min(100, Math.max(0, dimensions.scam_detection?.score ?? 100))}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-ink/60 line-clamp-2">
              Rule and pattern evaluation for fees, urgency, and money channels.
            </p>
          </div>

          {/* Dimension 5: Contact Consistency */}
          <div className="rounded-lg border border-ink/10 bg-mist/30 p-3">
            <div className="text-xs font-medium text-ink/50">5. Contact Domain (10%)</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="font-display text-lg font-bold">
                {dimensions.contact_consistency?.score ?? 50}
                <span className="text-xs font-normal text-ink/40">/100</span>
              </span>
              <span className="text-xs text-ink/60">
                {data.email ? 'Provided' : 'Unspecified'}
              </span>
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-ink/10">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${Math.min(100, Math.max(0, dimensions.contact_consistency?.score ?? 50))}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-ink/60 line-clamp-2">
              {data.email ? data.email : 'No direct recruiter email analyzed.'}
            </p>
          </div>
        </div>
      </section>

      {/* Middle Grid: Detailed Evidence Panels */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Panel 1: Machine Learning Evaluation */}
        <section className="card-panel lg:col-span-1">
          <h3 className="mb-2 font-display text-lg font-semibold">Machine Learning Model</h3>
          {ml.available ? (
            <>
              <p className="text-sm text-ink/70">
                Scam probability:{' '}
                <strong>{((ml.scam_probability || 0) * 100).toFixed(1)}%</strong>
              </p>
              <ul className="mt-2 space-y-1 text-sm">
                {(ml.top_terms || []).slice(0, 6).map((t) => (
                  <li key={t.term} className="flex justify-between gap-2 border-b border-ink/5 py-1">
                    <span>{t.term}</span>
                    <span className="text-ink/50">{t.weight}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-warn">
              ML model unavailable – rule and heuristic analysis only.
            </p>
          )}
        </section>

        {/* Panel 2: Detected Red Flags */}
        <section className="card-panel lg:col-span-1">
          <h3 className="mb-2 font-display text-lg font-semibold">Detected Red Flags</h3>
          <div className="space-y-2">
            {(data.red_flags || []).length === 0 ? (
              <p className="text-sm text-ink/60">No rule-based red flags triggered.</p>
            ) : (
              data.red_flags.map((f) => (
                <div key={f.id} className={`rounded-lg border p-3 ${severityClass(f.severity)}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold">{f.label}</span>
                    <span className="text-xs uppercase text-ink/50">
                      {f.severity} · {f.points} pts
                    </span>
                  </div>
                  {f.evidence ? (
                    <p className="mt-1 text-xs italic text-ink/60">&ldquo;{f.evidence}&rdquo;</p>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </section>

        {/* Panel 3: Company & URL Verification Findings */}
        <section className="card-panel lg:col-span-1">
          <h3 className="mb-2 font-display text-lg font-semibold">Company & URL Evidence</h3>
          <div className="space-y-3 text-sm">
            <div>
              <div className="mb-1 font-semibold">Company Status</div>
              <span className={companyStatusClass(company.status)}>{company.status || 'UNVERIFIED'}</span>
              <p className="mt-1 text-xs text-ink/60">{company.summary}</p>
              {company.reasons && company.reasons.length > 0 ? (
                <ul className="mt-1 space-y-0.5 text-xs text-ink/60">
                  {company.reasons.map((r, i) => (
                    <li key={i}>• {r}</li>
                  ))}
                </ul>
              ) : null}
            </div>

            <div>
              <div className="mb-1 font-semibold">URL / Source Analysis</div>
              {urlA.url ? (
                <>
                  <span className={riskBadgeClass(urlA.risk_level)}>{urlA.risk_level}</span>
                  <p className="mt-1 text-xs text-ink/60 break-all">{urlA.url}</p>
                  <p className="mt-0.5 text-xs text-ink/60">{urlA.explanation}</p>
                </>
              ) : (
                <p className="text-xs text-ink/60">No URL provided.</p>
              )}
            </div>

            <div>
              <div className="mb-1 font-semibold">Duplicate Check</div>
              {dup.is_duplicate ? (
                <ul className="space-y-1">
                  {(dup.matches || []).map((m) => (
                    <li key={`${m.source_type}-${m.matched_id}`} className="rounded border border-warn/30 bg-warn/5 p-2 text-xs">
                      <div className="font-medium text-warn">
                        {m.label || 'Possible duplicate'} – {m.similarity_percent}% similarity
                      </div>
                      <div className="text-ink/60">
                        {m.title} · {m.company}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-ink/60">No duplicate postings identified.</p>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Positive Indicators */}
      <section className="card-panel">
        <h3 className="mb-3 font-display text-lg font-semibold">Positive Evidence Signals</h3>
        <div className="flex flex-wrap gap-2">
          {(data.positive_indicators || []).length === 0 ? (
            <p className="text-sm text-ink/60">No positive indicators detected.</p>
          ) : (
            data.positive_indicators.map((p) => (
              <span key={p.id} className="rounded-md bg-safe/10 px-3 py-1 text-sm text-safe">
                ✓ {p.label}
              </span>
            ))
          )}
        </div>
      </section>

      {/* Stored Job Posting Details Card */}
      <section className="card-panel space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-ink/10 pb-2">
          <h3 className="font-display text-lg font-semibold">Stored Job Details</h3>
          <span className="text-xs text-ink/50">
            {data.created_at ? `Analyzed on ${new Date(data.created_at).toLocaleString()}` : ''}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          <div>
            <span className="text-xs text-ink/50">Company Name</span>
            <p className="font-medium">{data.company_name || '—'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Job Title</span>
            <p className="font-medium">{data.title || '—'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Salary Listed</span>
            <p className="font-medium">{data.salary || 'Not specified'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Recruiter Email</span>
            <p className="font-medium">{data.email || 'None provided'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Location</span>
            <p className="font-medium">{data.location || 'Not specified'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Job Type</span>
            <p className="font-medium">{data.job_type || 'Full-time'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Source / Ingestion</span>
            <p className="font-medium capitalize">{data.source || 'manual'}</p>
          </div>
          <div>
            <span className="text-xs text-ink/50">Website / URL</span>
            <p className="font-medium truncate">
              {data.url ? (
                <a href={data.url} target="_blank" rel="noreferrer" className="text-accent underline">
                  {data.url}
                </a>
              ) : (
                'None'
              )}
            </p>
          </div>
        </div>

        {/* Job Description View */}
        {data.description ? (
          <div className="pt-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase text-ink/50">Job Description</span>
              <button
                type="button"
                onClick={() => setShowFullDesc(!showFullDesc)}
                className="text-xs text-accent hover:underline"
              >
                {showFullDesc ? 'Show less' : 'Expand full description'}
              </button>
            </div>
            <div className={`mt-1 rounded border border-ink/10 bg-mist/20 p-3 text-xs leading-relaxed text-ink/80 whitespace-pre-line ${showFullDesc ? '' : 'max-h-28 overflow-hidden'}`}>
              {data.description}
            </div>
          </div>
        ) : null}

        {/* Extracted OCR Text view if applicable */}
        {data.extracted_ocr_text ? (
          <div className="pt-2">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase text-accent">
                <span>📸 Extracted OCR Text (From Upload)</span>
              </span>
              <button
                type="button"
                onClick={() => setShowOcrText(!showOcrText)}
                className="text-xs text-accent hover:underline"
              >
                {showOcrText ? 'Hide OCR text' : 'Show extracted OCR text'}
              </button>
            </div>
            {showOcrText ? (
              <div className="mt-2 rounded border border-accent/20 bg-accent/5 p-3 text-xs font-mono text-ink/80 whitespace-pre-line">
                {data.extracted_ocr_text}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      {/* Action Bar */}
      <div className="flex flex-wrap gap-3">
        <Link
          to="/reports"
          state={{
            prefill: {
              job_title: data.title || '',
              company_name: data.company_name || '',
              description: data.explanation || '',
            },
          }}
          className="btn-danger"
        >
          Report this posting
        </Link>
        <Link to="/analyze" className="btn-secondary">
          Analyze Another Job
        </Link>
      </div>

      {data.analysis_id ? <FeedbackWidget analysisId={data.analysis_id} /> : null}
    </div>
  );
}
