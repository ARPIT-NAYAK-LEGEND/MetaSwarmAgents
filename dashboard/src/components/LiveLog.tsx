

import { useEffect, useRef } from 'react';
import type { SwarmEvent } from '../types';

interface LiveLogProps {
  events: SwarmEvent[];
}

function getEventIcon(type: string): string {
  const icons: Record<string, string> = {
    run_started: '🚀',
    run_complete: '🏁',
    observer_complete: '👁️',
    bottleneck_found: '🔍',
    refactor_complete: '🔧',
    shadow_complete: '👤',
    eval_complete: '⚖️',
    promotion: '🎉',
    promotion_rejected: '❌',
    reset: '🔄',
    error: '⚠️',
  };
  return icons[type] || '📌';
}

function getEventLabel(type: string): string {
  const labels: Record<string, string> = {
    run_started: 'Pipeline Started',
    run_complete: 'Pipeline Complete',
    observer_complete: 'Observer Scored',
    bottleneck_found: 'Bottleneck Found',
    refactor_complete: 'Prompt Rewritten',
    shadow_complete: 'Shadow A/B Test',
    eval_complete: 'Eval Complete',
    promotion: 'Agent Promoted',
    promotion_rejected: 'Promotion Rejected',
    reset: 'Demo Reset',
    error: 'Error',
  };
  return labels[type] || type;
}

function formatEventMessage(event: SwarmEvent): string {
  switch (event.type) {
    case 'run_started':
      return event.message || 'Worker swarm pipeline starting...';
    case 'run_complete':
      return `Score: ${event.score ?? '?'}/100 — ${event.passed ?? '?'}/${event.total ?? '?'} tests — ${event.status?.toUpperCase()}`;
    case 'observer_complete':
      if (event.scores) {
        const entries = Object.entries(event.scores);
        return entries.map(([k, v]) => `${k}: ${v}`).join(' · ');
      }
      return 'Agents scored';
    case 'bottleneck_found':
      return `${event.agent}: ${event.root_cause || 'Root cause identified'}`;
    case 'refactor_complete':
      return `${event.agent}'s system prompt rewritten`;
    case 'shadow_complete':
      return `Shadow run complete for ${event.agent}`;
    case 'eval_complete':
      return `v1.0: ${event.v1_score}/100 vs v2.0: ${event.v2_score}/100 → ${event.winner} wins`;
    case 'promotion':
      return `${event.agent_id} promoted ${event.old_version} → ${event.new_version} (score: ${event.score})`;
    case 'promotion_rejected':
      return `Score ${event.score} below threshold ${event.threshold}`;
    case 'reset':
      return event.message || 'System reset to initial state';
    default:
      return event.message || JSON.stringify(event);
  }
}

export default function LiveLog({ events }: LiveLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="live-log card" id="live-log">
      <div className="live-log__header">
        <h2 className="live-log__title">
          <span className="live-log__indicator" />
          Live Event Log
        </h2>
        <span className="live-log__count">{events.length} events</span>
      </div>

      <div className="live-log__scroll" ref={scrollRef}>
        {events.length === 0 ? (
          <div className="live-log__empty">
            <p>Waiting for events...</p>
            <p className="live-log__empty-hint">Start a pipeline run to see events here</p>
          </div>
        ) : (
          events.map((event, idx) => (
            <div
              key={idx}
              className={`live-log__entry live-log__entry--${event.type}`}
              style={{ animationDelay: `${idx * 0.03}s` }}
            >
              <span className="live-log__icon">{getEventIcon(event.type)}</span>
              <div className="live-log__content">
                <span className="live-log__label">{getEventLabel(event.type)}</span>
                <span className="live-log__message">{formatEventMessage(event)}</span>
              </div>
              {event.timestamp && (
                <span className="live-log__time">
                  {new Date(event.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
