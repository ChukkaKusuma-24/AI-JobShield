import { useState } from 'react';
import { submitFeedback } from '../api/client';

export default function FeedbackWidget({ analysisId }) {
  const [label, setLabel] = useState('');
  const [comment, setComment] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErr('');
    setMsg('');
    if (!label) {
      setErr('Choose Correct, Incorrect, or Report.');
      return;
    }
    setLoading(true);
    try {
      await submitFeedback({ analysis_id: analysisId, label, comment: comment || undefined });
      setMsg('Thanks — feedback saved for future model improvement.');
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card-panel space-y-3">
      <h3 className="font-display text-lg font-semibold">Was this analysis helpful?</h3>
      <p className="text-sm text-ink/60">
        Feedback is stored locally for future retraining — it does not change this result.
      </p>
      <div className="flex flex-wrap gap-2">
        {[
          ['correct', 'Correct'],
          ['incorrect', 'Incorrect'],
          ['report', 'Report issue'],
        ].map(([v, t]) => (
          <button
            key={v}
            type="button"
            className={`btn-secondary !py-1.5 ${label === v ? '!border-accent !bg-accent/10' : ''}`}
            onClick={() => setLabel(v)}
          >
            {t}
          </button>
        ))}
      </div>
      <textarea
        className="input min-h-[80px]"
        placeholder="Optional comment"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
      {err ? <p className="text-sm text-danger">{err}</p> : null}
      {msg ? <p className="text-sm text-safe">{msg}</p> : null}
      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? 'Saving…' : 'Submit feedback'}
      </button>
    </form>
  );
}
