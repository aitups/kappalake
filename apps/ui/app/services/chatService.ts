"use server";

import { cookies } from "next/headers";
import { CONFIG } from "../lib/config";
import { AgentRunResponse, ExecuteResponse, PipelineResponse } from "../lib/types";

/**
 * Sends a prompt to the AI API to generate a SQL pipeline.
 * This runs on the server side (Next.js Server Action), allowing use of internal Docker networking.
 * 
 * @param prompt The user's natural language prompt.
 * @returns The AI's response containing the SQL query and explanation.
 * @throws Error if the API request fails.
 */
/**
 * Builds request headers, attaching the Keycloak bearer token when present.
 */
async function authHeaders(): Promise<Record<string, string>> {
  const token = (await cookies()).get("kappalake_token")?.value;
  return token
    ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    : { "Content-Type": "application/json" };
}

export async function generatePipeline(prompt: string): Promise<PipelineResponse> {
  // Use the internal URL when running on the server
  const url = `${CONFIG.INTERNAL_API_URL}${CONFIG.ENDPOINTS.GENERATE_PIPELINE}`;
  
  console.log(`[ServerAction] Connecting to API at: ${url}`);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify({ prompt }),
      cache: "no-store", // Ensure we don't cache API responses
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error(`[ServerAction] API Error (${res.status}): ${errorText}`);
      throw new Error(`API Request failed with status: ${res.status}`);
    }

    const data: PipelineResponse = await res.json();
    return data;
  } catch (error) {
    console.error("[ServerAction] Error in generatePipeline:", error);
    throw error;
  }
}

/**
 * Sends a prompt to the AI API which generates and executes a SQL query.
 */
export async function executePipeline(prompt: string): Promise<ExecuteResponse> {
  const url = `${CONFIG.INTERNAL_API_URL}${CONFIG.ENDPOINTS.EXECUTE}`;
  const res = await fetch(url, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ prompt }),
    cache: "no-store",
  });
  if (!res.ok) {
    const errorText = await res.text();
    console.error(`[ServerAction] Execute error (${res.status}): ${errorText}`);
    throw new Error(`Execute failed with status: ${res.status}`);
  }
  return res.json();
}

/**
 * Runs an autonomous data-engineering task through the FastPath orchestrator.
 */
export async function runAgentTask(task: string): Promise<AgentRunResponse> {
  const url = `${CONFIG.INTERNAL_API_URL}${CONFIG.ENDPOINTS.AGENT_RUN}`;
  const res = await fetch(url, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ task }),
    cache: "no-store",
  });
  if (!res.ok) {
    const errorText = await res.text();
    console.error(`[ServerAction] Agent error (${res.status}): ${errorText}`);
    throw new Error(`Agent run failed with status: ${res.status}`);
  }
  return res.json();
}
