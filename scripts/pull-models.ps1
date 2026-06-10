# Pull the local AI models Car Finder uses. Safe to re-run.
# On Windows, Ollama runs as a background service after install, so no `serve` needed.
$ErrorActionPreference = "Stop"

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Write-Error "ollama not installed. Run scripts\setup.ps1 first."
  exit 1
}

Write-Host ">> qwen2.5:14b — primary text/reasoning model (~9 GB)" -ForegroundColor Cyan
ollama pull qwen2.5:14b

Write-Host ">> llama3.2-vision:11b — reads odometer / title / damage photos (~8 GB)" -ForegroundColor Cyan
ollama pull llama3.2-vision:11b

Write-Host ">> nomic-embed-text — embeddings for dedup & semantic search (~0.3 GB)" -ForegroundColor Cyan
ollama pull nomic-embed-text

# Optional higher-quality reasoning model (uses your 5080 + spills to RAM):
# ollama pull qwen2.5:32b

Write-Host ""
Write-Host "Models ready:" -ForegroundColor Green
ollama list
