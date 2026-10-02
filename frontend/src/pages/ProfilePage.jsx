import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getDashboard } from '../api/client';

export default function ProfilePage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then((d) => setStats(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">User Profile</h1>
        <p className="text-sm text-ink/60">
          Account details, security overview, and personal analysis statistics.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* User Identity Card */}
        <div className="card-panel md:col-span-1 space-y-4 text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-accent/15 font-display text-3xl font-bold text-accent">
            {(user?.name || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">{user?.name || 'Authenticated User'}</h2>
            <p className="text-xs text-ink/60 break-all">{user?.email}</p>
          </div>
          <div>
            <span className="inline-flex items-center rounded-full bg-safe/15 px-3 py-1 text-xs font-semibold text-safe">
              ✓ Verified Account
            </span>
          </div>
          <div className="border-t border-ink/10 pt-3 text-xs text-ink/50">
            Role: <span className="font-medium uppercase text-ink/80">{user?.role || 'user'}</span>
          </div>
        </div>

        {/* Account Details & Activity Card */}
        <div className="card-panel md:col-span-2 space-y-4">
          <h3 className="font-display text-lg font-semibold border-b border-ink/10 pb-2">
            Account Information
          </h3>

          <div className="grid gap-4 sm:grid-cols-2 text-sm">
            <div>
              <span className="text-xs text-ink/50">Full Name</span>
              <p className="font-medium text-ink/90">{user?.name || '—'}</p>
            </div>
            <div>
              <span className="text-xs text-ink/50">Email Address</span>
              <p className="font-medium text-ink/90">{user?.email || '—'}</p>
            </div>
            <div>
              <span className="text-xs text-ink/50">Member Since</span>
              <p className="font-medium text-ink/90">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : 'Active Session'}
              </p>
            </div>
            <div>
              <span className="text-xs text-ink/50">Total Analyses Performed</span>
              <p className="font-display text-xl font-bold text-accent">
                {loading ? '…' : (stats?.total_analyses ?? 0)}
              </p>
            </div>
          </div>

          <div className="border-t border-ink/10 pt-3">
            <h4 className="mb-2 text-xs font-semibold uppercase text-ink/50">
              Risk Scan Breakdown
            </h4>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg border border-safe/30 bg-safe/5 p-2">
                <div className="font-display text-lg font-bold text-safe">{stats?.low_risk ?? 0}</div>
                <div className="text-ink/60">Low Risk</div>
              </div>
              <div className="rounded-lg border border-warn/30 bg-warn/5 p-2">
                <div className="font-display text-lg font-bold text-warn">{stats?.medium_risk ?? 0}</div>
                <div className="text-ink/60">Medium Risk</div>
              </div>
              <div className="rounded-lg border border-danger/30 bg-danger/5 p-2">
                <div className="font-display text-lg font-bold text-danger">{stats?.high_risk ?? 0}</div>
                <div className="text-ink/60">High Risk</div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-ink/10 bg-mist/30 p-3 text-xs text-ink/70">
            <span className="font-semibold text-ink/90">Security Note:</span> Password credentials are permanently hashed using strong industry-standard bcrypt salt hashing and never stored or returned in plaintext.
          </div>

          <div className="flex flex-wrap gap-2 pt-2">
            <Link to="/analyze" className="btn-primary text-xs">
              Analyze New Job
            </Link>
            <Link to="/history" className="btn-secondary text-xs">
              View Scan History
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
