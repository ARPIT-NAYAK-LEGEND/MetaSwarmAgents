

import { useState, useEffect, useCallback, useRef } from 'react';
import type { Agent, SwarmEvent } from '../types';

const API_BASE = '/api';

export function useRegistry() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [events, setEvents] = useState<SwarmEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [runPhase, setRunPhase] = useState<string>('idle');
  const eventSourceRef = useRef<EventSource | null>(null);

  // Initial load of agents
  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/registry`);
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
    }
  }, []);

  // Connect to SSE stream
  useEffect(() => {
    fetchAgents();

    const es = new EventSource(`${API_BASE}/stream`);
    eventSourceRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);

    es.onmessage = (e) => {
      try {
        const event: SwarmEvent = JSON.parse(e.data);

        // Skip heartbeat pings
        if (event.type === 'ping') return;

        // Update events list
        setEvents((prev) => [...prev, event]);

        // Update run phase based on event type
        switch (event.type) {
          case 'run_started':
            setRunPhase('running');
            break;
          case 'run_complete':
            if (event.status === 'failed') setRunPhase('failed');
            else setRunPhase('passed');
            break;
          case 'observer_complete':
            setRunPhase('observing');
            break;
          case 'bottleneck_found':
            setRunPhase('diagnosing');
            break;
          case 'refactor_complete':
            setRunPhase('refactoring');
            break;
          case 'shadow_complete':
            setRunPhase('shadow_testing');
            break;
          case 'eval_complete':
            setRunPhase('evaluating');
            break;
          case 'promotion':
            setRunPhase('promoted');
            // Refresh agents to get updated version
            fetchAgents();
            break;
          case 'promotion_rejected':
            setRunPhase('rejected');
            break;
          case 'reset':
            setRunPhase('idle');
            setEvents([]);
            fetchAgents();
            break;
        }

        // Update agent data on promotion
        if (event.type === 'promotion' && event.agent_id) {
          setAgents((prev) =>
            prev.map((a) =>
              a.id === event.agent_id
                ? {
                    ...a,
                    current_version: event.new_version || a.current_version,
                  }
                : a
            )
          );
        }
      } catch {
        // Ignore parse errors
      }
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [fetchAgents]);

  // Trigger a run
  const triggerRun = useCallback(async (full: boolean = true) => {
    try {
      setEvents([]);
      setRunPhase('starting');
      await fetch(`${API_BASE}/run?full=${full}`, { method: 'POST' });
    } catch (err) {
      console.error('Failed to trigger run:', err);
    }
  }, []);

  // Reset demo
  const resetDemo = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/reset`, { method: 'POST' });
      setEvents([]);
      setRunPhase('idle');
      await fetchAgents();
    } catch (err) {
      console.error('Failed to reset:', err);
    }
  }, [fetchAgents]);

  return {
    agents,
    events,
    connected,
    runPhase,
    triggerRun,
    resetDemo,
    refreshAgents: fetchAgents,
  };
}
