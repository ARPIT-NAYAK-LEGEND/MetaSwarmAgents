

import type { Agent } from '../types';

interface AgentCardProps {
  agent: Agent;
  score?: number;
  analysis?: string;
  isBottleneck?: boolean;
}

export default function AgentCard({ agent, score, analysis, isBottleneck }: AgentCardProps) {
  const latestVersion = agent.version_history[agent.version_history.length - 1];
  const evalScore = latestVersion?.eval_score;
  const isEvolved = agent.current_version !== '1.0';

  return (
    <div
      id={`agent-card-${agent.id}`}
      className={`agent-card card ${isBottleneck ? 'agent-card--bottleneck' : ''} ${
        isEvolved ? 'agent-card--evolved' : ''
      }`}
    >
      {/* Header */}
      <div className="agent-card__header">
        <div className="agent-card__name-row">
          <span className="agent-card__icon">
            {isBottleneck ? '🔴' : isEvolved ? '✨' : '🤖'}
          </span>
          <h3 className="agent-card__name">{agent.name}</h3>
        </div>
        <span
          className={`agent-card__version ${isEvolved ? 'agent-card__version--evolved' : ''}`}
        >
          v{agent.current_version}
        </span>
      </div>

      {/* Score */}
      {score !== undefined && (
        <div className="agent-card__score-section">
          <div className="agent-card__score-bar-container">
            <div
              className={`agent-card__score-bar ${
                score >= 70 ? 'agent-card__score-bar--success' : 'agent-card__score-bar--failure'
              }`}
              style={{ width: `${score}%` }}
            />
          </div>
          <span className="agent-card__score-value">{score}</span>
        </div>
      )}

      {/* Eval score from version history */}
      {evalScore !== null && evalScore !== undefined && score === undefined && (
        <div className="agent-card__eval">
          <span className="agent-card__eval-label">Eval Score</span>
          <span className="agent-card__eval-value">{evalScore}/100</span>
        </div>
      )}

      {/* Analysis */}
      {analysis && (
        <p className="agent-card__analysis">{analysis}</p>
      )}

      {/* Prompt preview */}
      <div className="agent-card__prompt-preview">
        <span className="agent-card__prompt-label">System Prompt</span>
        <p className="agent-card__prompt-text">
          {agent.system_prompt.slice(0, 120)}...
        </p>
      </div>
    </div>
  );
}
