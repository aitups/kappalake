"use server";

import { CONFIG } from "../lib/config";
import { PipelineResponse } from "../lib/types";

/**
 * Sends a prompt to the AI API to generate a SQL pipeline.
 * This runs on the server side (Next.js Server Action), allowing use of internal Docker networking.
 * 
 * @param prompt The user's natural language prompt.
 * @returns The AI's response containing the SQL query and explanation.
 * @throws Error if the API request fails.
 */
export async function generatePipeline(prompt: string): Promise<PipelineResponse> {
  // Use the internal URL when running on the server
  const url = `${CONFIG.INTERNAL_API_URL}${CONFIG.ENDPOINTS.GENERATE_PIPELINE}`;
  
  console.log(`[ServerAction] Connecting to API at: ${url}`);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
