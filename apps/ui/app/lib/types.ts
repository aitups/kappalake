export type Role = "user" | "assistant";

export interface Message {
  role: Role;
  content: string;
  sql?: string;
  columns?: string[];
  rows?: (string | number | null)[][];
}

export interface PipelineResponse {
  sql_query: string;
  explanation: string;
}

export interface ExecuteResponse {
  sql_query: string;
  explanation: string;
  columns: string[];
  rows: (string | number | null)[][];
}

export interface AgentRunResponse {
  success: boolean;
  output?: string | null;
  details?: unknown;
  reflection_rounds: number;
  attempts: Array<{ attempt: number; success: boolean; output: string }>;
}


