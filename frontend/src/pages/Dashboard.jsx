import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { getDashboard } from '../api/client';
import { riskBadgeClass } from '../utils/helpers';

const COLORS = { HIGH: '#b33a3a', MEDIUM: '#c47a1a', LOW: '#2d7a46' };

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="p-6 text-danger">{error}</p>;
  if (!data) return <p className="p-6 text-ink/60">Loading dashboard…</p>;

  const stats = [
    { label: 'Total analyses', value: data.total_analyses },
    { label: 'High risk', value: data.high_risk },
    { label: 'Medium risk', value: data.medium_risk },
    { label: 'Low risk', value: data.low_risk },
    { label: 'Scam reports', value: data.total_reports },
    { label: 'Companies checked', value: data.companies_checked },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-bold">Dashboard</h1>
        <p className="text-sm text-ink/60">Your local analysis activity at a glance.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((s) => (
          <div key={s.label} className="card-panel">
            <div className="text-sm text-ink/55">{s.label}</div>
            <div className="font-display text-3xl font-bold text-accent">{s.value}</div>
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card-panel h-80">
          <h2 className="mb-2 font-display text-lg font-semibold">Risk distribution</h2>
          <ResponsiveContainer width="100%" height="90%">
            <PieChart>
              <Pie data={data.risk_distribution} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3}>
                {data.risk_distribution.map((d) => (
                  <Cell key={d.name} fill={COLORS[d.name] || '#888'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="card-panel h-80">
          <h2 className="mb-2 font-display text-lg font-semibold">Analyses (14 days)</h2>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={data.analyses_per_day}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#1a7a6d" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card-panel overflow-x-auto">
        <h2 className="mb-3 font-display text-lg font-semibold">Recent analyses</h2>
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="border-b border-ink/10 text-ink/50">
              <th className="py-2 font-medium">Title</th>
              <th className="py-2 font-medium">Company</th>
              <th className="py-2 font-medium">Score</th>
              <th className="py-2 font-medium">Risk</th>
              <th className="py-2 font-medium">When</th>
            </tr>
          </thead>
          <tbody>
            {(data.recent_analyses || []).map((a) => (
              <tr key={a.analysis_id} className="border-b border-ink/5">
                <td className="py-2">
                  <Link className="text-accent hover:underline" to={`/result/${a.analysis_id}`}>
                    {a.title}
                  </Link>
                </td>
                <td className="py-2">{a.company_name}</td>
                <td className="py-2 font-semibold">{a.trust_score}</td>
                <td className="py-2">
                  <span className={riskBadgeClass(a.risk_level)}>{a.risk_level}</span>
                </td>
                <td className="py-2 text-ink/50">
                  {a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                </td>
              </tr>
            ))}
            {(data.recent_analyses || []).length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-ink/50">
                  No analyses yet.{' '}
                  <Link to="/analyze" className="text-accent underline">
                    Analyze a job
                  </Link>
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
