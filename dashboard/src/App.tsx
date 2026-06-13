

import { useMemo } from 'react';
import './App.css';
import { useRegistry } from './hooks/useRegistry';
import AgentCard from './components/AgentCard';
import VersionTimeline from './components/VersionTimeline';
import LiveLog from './components/LiveLog';
import ScoreBar from './components/ScoreBar';
import type { SwarmEvent } from './types';

function getPhaseLabel(phase: string): string {
  const labels: Record<string, string> = {
    idle: 'Ready',
    starting: 'Initializing...',
    running: 'Worker Swarm Running',
    failed: 'Pipeline Failed — Triggering Meta-Swarm',
    observing: 'Observer Scoring Agents',
    diagnosing: 'Bottleneck Analyzing Root Cause',
    refactoring: 'Refactor Rewriting Prompt',
    shadow_testing: 'Shadow A/B Testing',
    evaluating: 'Eval Comparing Versions',
    promoted: 'Agent Promoted!',
    rejected: 'Promotion Rejected',
    passed: 'Pipeline Passed ✓',
  };
  return labels[phase] || phase;
}

function getPhaseColor(phase: string): string {
  if (['passed', 'promoted'].includes(phase)) return 'var(--color-success)';
  if (['failed', 'rejected'].includes(phase)) return 'var(--color-failure)';
  if (['observing', 'diagnosing', 'refactoring', 'shadow_testing', 'evaluating'].includes(phase))
    return 'var(--text-accent)';
  return 'var(--text-secondary)';
}

function App() {
  const { agents, events, connected, runPhase, triggerRun, resetDemo } = useRegistry();

  // Extract eval data from events for ScoreBar
  const evalData = useMemo(() => {
    const evalEvent = [...events].reverse().find(
      (e: SwarmEvent) => e.type === 'eval_complete'
    );
    if (!evalEvent) return null;
    return {
      v1Score: evalEvent.v1_score ?? null,
      v2Score: evalEvent.v2_score ?? null,
      winner: evalEvent.winner,
      improvement: evalEvent.improvement,
    };
  }, [events]);

  // Extract observer scores
  const observerScores = useMemo(() => {
    const obsEvent = [...events].reverse().find(
      (e: SwarmEvent) => e.type === 'observer_complete'
    );
    return obsEvent?.scores || null;
  }, [events]);

  // Extract observer analysis
  const observerAnalysis = useMemo(() => {
    const obsEvent = [...events].reverse().find(
      (e: SwarmEvent) => e.type === 'observer_complete'
    );
    return obsEvent?.analysis || null;
  }, [events]);

  // Get bottleneck agent
  const bottleneckAgent = useMemo(() => {
    const bnEvent = [...events].reverse().find(
      (e: SwarmEvent) => e.type === 'bottleneck_found'
    );
    return bnEvent?.agent || null;
  }, [events]);

  // Find the controller agent for the version timeline
  const controllerAgent = agents.find((a) => a.id === 'controller_agent');

  return (
    <div className="dashboard" id="dashboard">

      <header className="dashboard__header" id="dashboard-header">
        <div className="dashboard__header-left">
          <h1 className="dashboard__title">
            <span className="dashboard__title-icon">🧬</span>
            MetaSwarm
          </h1>
          <p className="dashboard__subtitle">Self-Evolving Multi-Agent System</p>
        </div>

        <div className="dashboard__header-right">
          {/* Connection indicator */}
          <div className={`dashboard__connection ${connected ? 'dashboard__connection--live' : ''}`}>
            <span className="dashboard__connection-dot" />
            {connected ? 'Connected' : 'Disconnected'}
          </div>

          {/* Phase indicator */}
          <div className="dashboard__phase" style={{ color: getPhaseColor(runPhase) }}>
            {runPhase !== 'idle' && (
              <span className="dashboard__phase-pulse" style={{ background: getPhaseColor(runPhase) }} />
            )}
            {getPhaseLabel(runPhase)}
          </div>

          {/* Controls */}
          <div className="dashboard__controls">
            <button
              className="dashboard__btn dashboard__btn--primary"
              onClick={() => triggerRun(true)}
              disabled={!['idle', 'passed', 'promoted', 'rejected', 'failed'].includes(runPhase)}
              id="btn-run-full"
            >
              🚀 Run Full Demo
            </button>
            <button
              className="dashboard__btn dashboard__btn--secondary"
              onClick={resetDemo}
              id="btn-reset"
            >
              🔄 Reset
            </button>
          </div>
        </div>
      </header>


      <main className="dashboard__main">
        {/* Left: Agent Grid + Version Timeline + ScoreBar */}
        <div className="dashboard__left">
          {/* Version Timeline (Controller Agent) */}
          {controllerAgent && controllerAgent.version_history.length > 0 && (
            <section className="dashboard__section">
              <h2 className="dashboard__section-title">
                🔄 Controller Agent Version Timeline
              </h2>
              <VersionTimeline
                versionHistory={controllerAgent.version_history}
                currentVersion={controllerAgent.current_version}
              />
            </section>
          )}

          {/* ScoreBar (shows during eval) */}
          {evalData && (
            <section className="dashboard__section">
              <ScoreBar
                v1Score={evalData.v1Score}
                v2Score={evalData.v2Score}
                winner={evalData.winner}
                improvement={evalData.improvement}
              />
            </section>
          )}

          {/* Agent Grid */}
          <section className="dashboard__section">
            <h2 className="dashboard__section-title">🤖 Agent Registry</h2>
            {agents.length === 0 ? (
              <div className="dashboard__empty">
                <p>No agents registered yet.</p>
                <p className="dashboard__empty-hint">
                  Run <code>python -m demo.seed_registry</code> to seed initial agent data.
                </p>
              </div>
            ) : (
              <div className="dashboard__agent-grid">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    score={observerScores?.[agent.id]}
                    analysis={observerAnalysis?.[agent.id]}
                    isBottleneck={bottleneckAgent === agent.id}
                  />
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Right: Live Log */}
        <div className="dashboard__right">
          <LiveLog events={events} />
        </div>
      </main>
    </div>
  );
}

export default App;
