"use client";

import { useState } from "react";
import { Message } from "../lib/types";
import { executePipeline, generatePipeline, runAgentTask } from "../services/chatService";

type Mode = "copilot" | "agent";

/**
 * ChatInterface: two modes.
 * - Copilot: natural language -> SQL (generated) -> executed -> results table.
 * - Agent: autonomous data-engineering task via the FastPath orchestrator.
 */
export default function ChatInterface() {
  const [mode, setMode] = useState<Mode>("copilot");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const text = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      if (mode === "copilot") {
        const data = await executePipeline(text);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.explanation || "Query executed.",
            sql: data.sql_query,
            columns: data.columns,
            rows: data.rows,
          },
        ]);
      } else {
        const data = await runAgentTask(text);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: String(data.output ?? "") || (data.success ? "Task completed." : "Task failed."),
          },
        ]);
      }
    } catch (error) {
      console.error("Failed to get AI response:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error connecting to the AI API. Please try again later." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-3xl border rounded-lg shadow-lg bg-white overflow-hidden">
      {/* Mode Toggle */}
      <div className="flex border-b bg-gray-50">
        {(
          [
            ["copilot", "AI Copilot"],
            ["agent", "AI Agent"],
          ] as [Mode, string][]
        ).map(([m, label]) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              mode === m
                ? "text-blue-600 border-b-2 border-blue-600 bg-white"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Message List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] p-3 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-200 text-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.sql && (
                <div className="mt-2 bg-gray-900 text-green-400 p-2 rounded text-xs font-mono overflow-x-auto">
                  <pre>{msg.sql}</pre>
                </div>
              )}
              {msg.columns && msg.rows && (
                <div className="mt-2 overflow-x-auto">
                  <table className="min-w-full text-xs border-collapse">
                    <thead>
                      <tr>
                        {msg.columns.map((c) => (
                          <th key={c} className="border border-gray-300 bg-gray-100 px-2 py-1 text-left">
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {msg.rows.map((r, i) => (
                        <tr key={i}>
                          {r.map((cell, j) => (
                            <td key={j} className="border border-gray-300 px-2 py-1">
                              {String(cell)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-500 p-3 rounded-lg animate-pulse">
              {mode === "agent" ? "Agent working..." : "Thinking..."}
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t bg-white flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            mode === "agent"
              ? "Ask the agent, e.g. \"Create a gold table with users per nationality\""
              : "Ask for data, e.g. \"Show top 5 nationalities by users\""
          }
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
        >
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
