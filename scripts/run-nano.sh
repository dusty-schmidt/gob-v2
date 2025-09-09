#!/usr/bin/env bash
set -euo pipefail

# Conda activation (optional)
CONDA_SH="/home/ds/miniconda3/etc/profile.d/conda.sh"
if [ -f "$CONDA_SH" ]; then source "$CONDA_SH"; fi
if command -v conda >/dev/null 2>&1; then
  conda activate gobv2 || true
fi

# Env defaults
export NEXUS_HOST=${NEXUS_HOST:-127.0.0.1}
export NEXUS_PORT=${NEXUS_PORT:-7000}
export NEXUS_URL=${NEXUS_URL:-ws://${NEXUS_HOST}:${NEXUS_PORT}}
export INTERFACE_ID=${INTERFACE_ID:-nano}
export INTERFACE_TARGET=${INTERFACE_TARGET:-mini}
export GRID_TICK_MS=${GRID_TICK_MS:-1000}

# Lightweight dependency ensure
python3 -m pip -q install -r requirements.txt || true

# Start gateway
python3 nexus/gateway/server.py &
GW_PID=$!
trap 'kill $GW_PID 2>/dev/null || true' EXIT
sleep 0.3

# Start grid ticker
python3 grid/loop/ticker.py &
GRID_PID=$!
trap 'kill $GRID_PID 2>/dev/null || true' EXIT
sleep 0.2

# Start nano interface (WS client CLI)
python3 mesh/nodes/ops/nano/cli.py
