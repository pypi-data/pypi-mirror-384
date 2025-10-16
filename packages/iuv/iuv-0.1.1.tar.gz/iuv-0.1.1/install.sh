#!/usr/bin/env bash
set -euo pipefail

# Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
  echo "[install] 'uv' not found. Installing via official installer..."
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  else
    echo "Error: curl is required to download uv installer." >&2
    exit 1
  fi
else
  echo "[install] 'uv' already present: $(command -v uv)"
fi

# Ensure typical install location is on PATH for this session
if ! command -v uv >/dev/null 2>&1; then
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv still not found on PATH after installation. Add $HOME/.local/bin to PATH and retry." >&2
  exit 1
fi

echo "[install] Installing iuv as a uv tool"
uv tool install --force .

echo "[install] Done. You can now run:"
echo "  iuv <uv / uvx command ...>"
