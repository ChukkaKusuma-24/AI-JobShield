import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ocrAnalyze } from '../api/client';
import AnalysisResultView from '../components/AnalysisResultView';

const JOB_REJECT_MSG =
  "This doesn't appear to be a job or recruitment-related document. Please upload a job posting, recruiter message, resume/CV, or similar document.";

export default function OcrPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [extracted, setExtracted] = useState('');
  const [hints, setHints] = useState({});
  const [meta, setMeta] = useState({ title: '', company_name: '', email: '', url: '' });
  const [ocrDone, setOcrDone] = useState(false);
  const [install, setInstall] = useState(null);
  const [error, setError] = useState('');
  const [rejectInfo, setRejectInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [result, setResult] = useState(null);
  const inputRef = useRef(null);

  function onFile(f) {
    setFile(f);
    setOcrDone(false);
    setExtracted('');
    setResult(null);
    setInstall(null);
    setError('');
    setRejectInfo(null);
    if (f) setPreview(URL.createObjectURL(f));
    else setPreview('');
  }

  async function runOcrAnalyze(e) {
    e.preventDefault();
    setError('');
    setInstall(null);
    setRejectInfo(null);
    setResult(null);
    if (!file) {
      setError('Choose a PNG, JPG, or WEBP image to upload.');
      return;
    }
    setLoading(true);
    setLoadingMsg(ocrDone ? 'Re-analyzing edited text…' : 'Extracting text…');
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (meta.company_name) fd.append('company_name', meta.company_name);
      if (meta.email) fd.append('email', meta.email);
      if (meta.url) fd.append('url', meta.url);
      if (meta.title) fd.append('title', meta.title);
      if (ocrDone && extracted) fd.append('text_override', extracted);

      const data = await ocrAnalyze(fd);
      setLoadingMsg('Running analysis…');
      setExtracted(data.extracted_text || data.ocr?.extracted_text || '');
      setHints(data.ocr?.hints || {});
      setOcrDone(true);
      setResult(data.analysis);
      if (data.ocr?.hints) {
        setMeta((m) => ({
          title: m.title || data.ocr.hints.title || '',
          company_name: m.company_name || data.ocr.hints.company_name || '',
          email: m.email || (data.ocr.hints.emails || [])[0] || '',
          url: m.url || (data.ocr.hints.urls || [])[0] || '',
        }));
      }
    } catch (ex) {
      if (ex.code === 'OCR_UNAVAILABLE') {
        setInstall(ex.details?.[0] || {});
        setError(ex.message);
      } else if (ex.code === 'NOT_JOB_RELATED' || ex.raw?.valid === false) {
        const detail = ex.details?.[0] || {};
        const text = detail.extracted_text || ex.raw?.extracted_text || '';
        setExtracted(text);
        setOcrDone(false);
        setResult(null);
        setRejectInfo({
          message: JOB_REJECT_MSG,
          score: detail.score ?? ex.raw?.score,
          signals: detail.signals || ex.raw?.signals || [],
        });
        setError(JOB_REJECT_MSG);
      } else {
        setError(ex.message);
      }
    } finally {
      setLoading(false);
      setLoadingMsg('');
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">Screenshot / OCR analysis</h1>
        <p className="text-sm text-ink/60">
          Local Tesseract OCR only. Uploads must look like a job posting, recruiter message, or resume/CV.
        </p>
      </div>

      <form className="card-panel space-y-4" onSubmit={runOcrAnalyze}>
        <div
          className="cursor-pointer rounded-lg border border-dashed border-ink/20 bg-mist/40 px-4 py-10 text-center"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) onFile(f);
          }}
        >
          <p className="font-medium">Drag & drop PNG/JPG/WEBP or click to browse</p>
          <p className="mt-1 text-xs text-ink/50">Max size configured on server (default 5 MB)</p>
          <input
            ref={inputRef}
            type="file"
            accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0] || null)}
          />
        </div>
        {preview ? (
          <img src={preview} alt="Upload preview" className="max-h-56 rounded-lg border border-ink/10" />
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          {['title', 'company_name', 'email', 'url'].map((k) => (
            <div key={k}>
              <label className="label" htmlFor={k}>
                {k.replace('_', ' ')} (optional)
              </label>
              <input
                id={k}
                className="input"
                value={meta[k]}
                onChange={(e) => setMeta((m) => ({ ...m, [k]: e.target.value }))}
              />
            </div>
          ))}
        </div>

        {ocrDone || extracted ? (
          <div>
            <label className="label" htmlFor="extracted">
              Extracted text {rejectInfo ? '(from rejected upload — shown for reference)' : '(editable)'}
            </label>
            <textarea
              id="extracted"
              className="input min-h-[160px]"
              value={extracted}
              onChange={(e) => setExtracted(e.target.value)}
              readOnly={Boolean(rejectInfo)}
            />
          </div>
        ) : null}

        {rejectInfo ? (
          <div className="rounded-md border border-danger/30 bg-danger/5 p-3 text-sm">
            <p className="font-semibold text-danger">{rejectInfo.message}</p>
            {typeof rejectInfo.score === 'number' ? (
              <p className="mt-1 text-xs text-ink/55">
                Validation score: {rejectInfo.score} (job-related signals were insufficient)
              </p>
            ) : null}
          </div>
        ) : null}

        {error && !rejectInfo ? <p className="text-sm text-danger">{error}</p> : null}
        {install ? (
          <div className="rounded-md border border-warn/30 bg-warn/5 p-3 text-sm">
            <p className="font-semibold text-warn">Install Tesseract locally</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-ink/70">
              <li>Windows: {install.windows}</li>
              <li>macOS: {install.macos}</li>
              <li>Linux: {install.linux}</li>
            </ul>
            <p className="mt-3">
              Or{' '}
              <Link to="/analyze" className="text-accent underline">
                paste the text manually on Analyze
              </Link>
              .
            </p>
          </div>
        ) : null}

        <button type="submit" className="btn-primary" disabled={loading || !file || Boolean(rejectInfo)}>
          {loading
            ? loadingMsg || 'Working…'
            : ocrDone
              ? 'Analyze extracted text'
              : 'Upload & analyze'}
        </button>
        {rejectInfo ? (
          <p className="text-xs text-ink/50">
            Choose a different image (job posting / recruiter message / resume) to try again.
          </p>
        ) : null}
      </form>

      {result ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-sm text-ink/60">
              Analysis saved. It will appear on Dashboard and History after refresh.
            </p>
            {result.analysis_id ? (
              <Link className="btn-secondary !py-1.5" to={`/result/${result.analysis_id}`}>
                Open full result
              </Link>
            ) : null}
          </div>
          <AnalysisResultView data={result} />
        </div>
      ) : null}
    </div>
  );
}
