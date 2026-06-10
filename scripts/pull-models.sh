#!/usr/bin/env bash
# Pull the local AI models Car Finder uses. Safe to re-run (Ollama skips up-to-date layers).
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "✖ ollama not installed. Run scripts/setup.sh first."; exit 1
fi

# Make sure the Ollama server is reachable (on macOS the CLI needs `ollama serve`).
if ! ollama list >/dev/null 2>&1; then
  echo "▶ Starting ollama server in the background…"
  ollama serve >/dev/null 2>&1 &
  sleep 5
fi

echo "▶ qwen2.5:14b — primary text/reasoning model (~9 GB, fits a 16 GB GPU)"
ollama pull qwen2.5:14b

echo "▶ llama3.2-vision:11b — reads odometer / title / damage photos (~8 GB)"
ollama pull llama3.2-vision:11b

echo "▶ nomic-embed-text — embeddings for dedup & semantic search (~0.3 GB)"
ollama pull nomic-embed-text

# Optional higher-quality reasoning model. On a 16 GB GPU it partially offloads to
# CPU/RAM (slower but usable thanks to your 64 GB). Uncomment to use it:
# ollama pull qwen2.5:32b

echo ""
echo "✓ Models ready:"
ollama list
