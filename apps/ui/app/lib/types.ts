export type Role = "user" | "assistant";

export interface Message {
  role: Role;
  content: string;
  sql?: string;
}

export interface PipelineResponse {
  sql_query: string;
  explanation: string;
}

