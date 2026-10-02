export default function TrustGauge({ score = 0, riskLevel = 'MEDIUM' }) {
  const size = 160;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, Math.max(0, score)) / 100) * c;
  const color =
    riskLevel === 'HIGH' ? '#b33a3a' : riskLevel === 'LOW' ? '#2d7a46' : '#c47a1a';

  return (
    <div className="relative mx-auto h-40 w-40 animate-pulse-ring rounded-full">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <circle
          className="score-ring"
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="font-display text-4xl font-bold" style={{ color }}>
          {score}
        </div>
        <div className="text-xs font-semibold uppercase tracking-wider text-ink/50">
          Trust score
        </div>
      </div>
    </div>
  );
}
