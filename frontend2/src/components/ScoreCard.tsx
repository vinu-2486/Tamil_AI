type ScoreCardProps = {
  score: number | null;
};

export default function ScoreCard({ score }: ScoreCardProps) {
  if (score === null || Number.isNaN(score)) {
    return null;
  }

  const clamped = Math.max(0, Math.min(100, score));
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (circumference * clamped) / 100;

  const color =
    clamped >= 75 ? "var(--jade)" : clamped >= 50 ? "var(--gold)" : "var(--vermillion)";

  return (
    <div className="card score-card">
      <div className="dial">
        <svg viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="var(--surface-2)" strokeWidth="10" />
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="dial-value" style={{ color }}>
          {Math.round(clamped)}
        </div>
      </div>
      <div className="dial-sub">Pronunciation score / 100</div>
    </div>
  );
}