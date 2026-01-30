"use client";

import { useState } from "react";
import { Message } from "../lib/types";
import { generatePipeline } from "../services/chatService";

/**
 * ChatInterface Component
 * 
 * Displays a chat window for interacting with the AI data pipeline generator.
 * Handles user input, displays messages, and communicates with the backend API.
 */
export default function ChatInterface() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  /**
   * Handles form submission to send a message to the AI.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to state
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Call the service to generate the pipeline
      const data = await generatePipeline(userMsg.content);
      
      const aiMsg: Message = {
        role: "assistant",
        content: data.explanation,
        sql: data.sql_query,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error("Failed to get AI response:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error connecting to AI API. Please try again later." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-2xl border rounded-lg shadow-lg bg-white overflow-hidden">
      {/* Message List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
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
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-500 p-3 rounded-lg animate-pulse">
              Thinking...
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
          placeholder="Ask for data (e.g., 'Show total sales by region')"
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
