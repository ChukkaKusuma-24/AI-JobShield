import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const features = [
  {
    title: 'NLP scam signals',
    body: 'TF-IDF model estimates how similar a posting is to suspicious demo patterns.',
  },
  {
    title: 'Rule-based red flags',
    body: 'Transparent fee, pressure, contact, and salary heuristics with evidence quotes.',
  },
  {
    title: 'OCR screenshot analysis',
    body: 'Extract text from posters locally with Tesseract, then edit before analyzing.',
  },
  {
    title: 'Trust score + XAI',
    body: 'Combined score with ML vs rules vs heuristics clearly separated for demos.',
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();
  return (
    <div>
      <section className="relative overflow-hidden border-b border-ink/5">
        <div
          className="absolute inset-0 -z-10 opacity-90"
          style={{
            backgroundImage:
              'linear-gradient(120deg, rgba(15,28,46,0.88), rgba(26,122,109,0.55)), url(https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=1600&q=80)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        />
        <div className="mx-auto flex min-h-[78vh] max-w-6xl flex-col justify-end px-4 pb-16 pt-24 text-white animate-fade-up">
          <p className="font-display text-5xl font-bold tracking-tight sm:text-6xl md:text-7xl">
            AI JobShield
          </p>
          <h1 className="mt-4 max-w-2xl text-xl font-medium text-white/90 sm:text-2xl">
            Spot suspicious job and internship postings before you share personal data or pay a fee.
          </h1>
          <p className="mt-3 max-w-xl text-sm text-white/75">
            Fully local college mini project — guidance only, not a verdict. Always verify through
            official channels.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={isAuthenticated ? '/analyze' : '/auth'} className="btn-primary">
              Try it
            </Link>
            <Link to="/about" className="btn-secondary !bg-white/15 !text-white !border-white/30">
              How it works
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="font-display text-3xl font-semibold">The problem</h2>
        <p className="mt-3 max-w-3xl text-ink/70">
          Fraudsters post fake offers to collect fees, steal identity documents, or phish applicants.
          Manual checks are slow and rarely explain why a posting feels wrong. JobShield combines
          local ML, rules, OCR, URL heuristics, and optional company checks into one explainable
          trust score.
        </p>
        <div className="mt-10 grid gap-5 sm:grid-cols-2">
          {features.map((f, i) => (
            <article
              key={f.title}
              className="card-panel animate-fade-up"
              style={{ animationDelay: `${0.08 * i}s` }}
            >
              <h3 className="font-display text-xl font-semibold text-accent">{f.title}</h3>
              <p className="mt-2 text-sm text-ink/70">{f.body}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
