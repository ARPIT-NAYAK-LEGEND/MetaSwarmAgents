

interface ScoreBarProps {
  v1Score: number | null;
  v2Score: number | null;
  winner?: string;
  improvement?: string;
}

export default function ScoreBar({ v1Score, v2Score, winner, improvement }: ScoreBarProps) {
  if (v1Score === null || v2Score === null) return null;

  return (
    <div className="score-bar card" id="score-bar">
      <h2 className="score-bar__title">⚖️ Version Comparison</h2>

      <div className="score-bar__grid">
        {/* v1.0 */}
        <div className="score-bar__version">
          <div className="score-bar__version-header">
            <span className="score-bar__version-label score-bar__version-label--v1">v1.0</span>
            <span className="score-bar__version-score">{v1Score}/100</span>
          </div>
          <div className="score-bar__track">
            <div
              className="score-bar__fill score-bar__fill--v1"
              style={{ width: `${v1Score}%` }}
            />
          </div>
          <div className="score-bar__breakdown">
            <span className={`score-bar__tag ${v1Score >= 70 ? 'score-bar__tag--pass' : 'score-bar__tag--fail'}`}>
              {v1Score >= 70 ? 'PASS' : 'FAIL'}
            </span>
          </div>
        </div>

        {/* VS divider */}
        <div className="score-bar__divider">
          <span className="score-bar__vs">VS</span>
        </div>

        {/* v2.0 */}
        <div className="score-bar__version">
          <div className="score-bar__version-header">
            <span className="score-bar__version-label score-bar__version-label--v2">v2.0</span>
            <span className="score-bar__version-score">{v2Score}/100</span>
          </div>
          <div className="score-bar__track">
            <div
              className="score-bar__fill score-bar__fill--v2"
              style={{ width: `${v2Score}%` }}
            />
          </div>
          <div className="score-bar__breakdown">
            <span className={`score-bar__tag ${v2Score >= 70 ? 'score-bar__tag--pass' : 'score-bar__tag--fail'}`}>
              {v2Score >= 70 ? 'PASS' : 'FAIL'}
            </span>
          </div>
        </div>
      </div>

      {/* Winner banner */}
      {winner && (
        <div className={`score-bar__winner ${winner === 'v2' ? 'score-bar__winner--v2' : ''}`}>
          <span className="score-bar__winner-icon">🏆</span>
          <span className="score-bar__winner-text">
            {winner.toUpperCase()} wins{improvement ? ` — ${improvement}` : ''}
          </span>
          <span className="score-bar__winner-delta">
            +{Math.abs(v2Score - v1Score)} pts
          </span>
        </div>
      )}
    </div>
  );
}
