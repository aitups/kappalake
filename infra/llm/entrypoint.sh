#!/bin/bash
set -e

MODEL_URL="https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf"
MODEL_PATH="/models/Qwen3-1.7B-Q4_K_M.gguf"

if [ ! -f "$MODEL_PATH" ]; then
    echo "Model not found. Downloading Qwen3-1.7B (GGUF)..."
    apt-get update && apt-get install -y curl
    curl -L -o "$MODEL_PATH" "$MODEL_URL"
    echo "Download complete."
else
    echo "Model already exists."
fi

# Start server
echo "Starting llama.cpp server..."
/app/llama-server -m "$MODEL_PATH" --host 0.0.0.0 --port 8080 -t 8 --mlock -c 2048 -b 2048

