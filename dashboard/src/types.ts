

export interface VersionEntry {
  version: string;
  system_prompt: string;
  eval_score: number | null;
  promoted_at: string;
}

export interface Agent {
  id: string;
  name: string;
  current_version: string;
  system_prompt: string;
  version_history: VersionEntry[];
  updated_at: string;
}

export interface SwarmEvent {
  type: string;
  timestamp?: string;
  message?: string;
  run_id?: string;

  // Observer events
  scores?: Record<string, number>;
  analysis?: Record<string, string>;

  // Bottleneck events
  agent?: string;
  root_cause?: string;
  missing?: string;

  // Eval events
  v1_score?: number;
  v2_score?: number;
  winner?: string;
  improvement?: string;

  // Promotion events
  agent_id?: string;
  old_version?: string;
  new_version?: string;
  score?: number;

  // Run events
  status?: string;
  passed?: number;
  total?: number;

  // Refactor
  new_prompt_preview?: string;

  // Promotion rejected
  threshold?: number;
  reason?: string;
}
