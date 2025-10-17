bash -lc 'set -euo pipefail

# =========================
# 0) One-shot vLLM + Supervisor installer for Falcon-H1-34B
# =========================

export DEBIAN_FRONTEND=noninteractive

# ---- A) Base deps
apt-get update -y
apt-get install -y python3-venv python3-pip supervisor jq curl git tmux htop lsof psmisc numactl

# ---- B) Ensure supervisord has a sane config & is running
if [ ! -f /etc/supervisor/supervisord.conf ]; then
  cat >/etc/supervisor/supervisord.conf <<'"SUPCONF"'
[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisord]
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor
logfile_maxbytes=10MB
logfile_backups=3

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[include]
files = /etc/supervisor/conf.d/*.conf
"SUPCONF"
fi

mkdir -p /var/log/supervisor /var/run
# Start supervisord even if systemd is unhappy in this environment
pkill -f supervisord 2>/dev/null || true
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf || true

# ---- C) Defaults you can tweak later
install -d -m 0755 /etc/default
cat >/etc/default/vllm <<'"DEFS"'
# ===== vLLM defaults =====
MODEL_ID=tiiuae/Falcon-H1-34B-Instruct
PORT=8000
DISK_ROOT=/ephemeral
VENV_DIR=/opt/vllm-venv

# Parallelism: if TP is empty, we auto-detect GPU count
# TP=2

# Context + perf knobs
MAX_MODEL_LEN=8192
# Either set a conservative GPU mem utilization (recommended), OR pin KV cache size.
GPU_MEM_UTIL=0.70
# Optional: override KV cache size (bytes). If set, it takes precedence over GPU_MEM_UTIL.
# Good examples from your logs for A100 80GB (per GPU):
# KV_CACHE_MEMORY=22850650624      # safer headroom
# KV_CACHE_MEMORY=47824781824      # aggressive / fuller usage
# KV_CACHE_MEMORY=

# Optional HF token for gated models
# HF_TOKEN=

# Batch/prefill knobs (leave as-is unless you know you need to change)
MAX_NUM_BATCHED_TOKENS=4096
MAX_NUM_SEQS=8

# Engine behavior
ENFORCE_EAGER=1
DEFS

# ---- D) Python venv + packages
. /etc/default/vllm
python3 -m venv "$VENV_DIR" || true
source "$VENV_DIR/bin/activate"
python -m pip install -U pip wheel setuptools
pip install -U "vllm==0.10.2" "transformers>=4.44" accelerate hf-transfer

# ---- E) Runtime helper: health check
cat >/usr/local/bin/vllm-health <<'"HLTH"'
#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8000}"
curl -sSf "http://127.0.0.1:${PORT}/health" >/dev/null && echo "OK" || { echo "not healthy" >&2; exit 1; }
echo
curl -s "http://127.0.0.1:${PORT}/v1/models" | jq .
HLTH
chmod +x /usr/local/bin/vllm-health

# ---- F) vLLM launcher used by Supervisor
cat >/usr/local/bin/vllm-start <<'"LAUNCH"'
#!/usr/bin/env bash
set -euo pipefail
[[ -f /etc/default/vllm ]] && set -a && . /etc/default/vllm && set +a

MODEL_ID=${MODEL_ID:-tiiuae/Falcon-H1-34B-Instruct}
PORT=${PORT:-8000}
DISK_ROOT=${DISK_ROOT:-/ephemeral}
VENV_DIR=${VENV_DIR:-/opt/vllm-venv}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}
GPU_MEM_UTIL=${GPU_MEM_UTIL:-0.70}
KV_CACHE_MEMORY=${KV_CACHE_MEMORY:-}
MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-4096}
MAX_NUM_SEQS=${MAX_NUM_SEQS:-8}
TP="${TP:-}"
ENFORCE_EAGER="${ENFORCE_EAGER:-1}"

# Storage & env
mkdir -p "$DISK_ROOT/tmp" "$DISK_ROOT/hf-cache"/{hub,transformers} /var/log/vllm
export TMPDIR="$DISK_ROOT/tmp"
export HF_HOME="$DISK_ROOT/hf-cache"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_ENABLE_HF_TRANSFER=${HF_HUB_ENABLE_HF_TRANSFER:-1}

# Stable CUDA/NCCL & threading defaults
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
export CUDA_DEVICE_MAX_CONNECTIONS=${CUDA_DEVICE_MAX_CONNECTIONS:-1}
export NCCL_P2P_LEVEL=${NCCL_P2P_LEVEL:-NVL}
export NCCL_IB_DISABLE=${NCCL_IB_DISABLE:-1}
ulimit -n 65535 || true

# Tensor parallel: default to GPU count if TP not set
if [[ -z "$TP" ]]; then
  GPU_CT=$(nvidia-smi -L 2>/dev/null | wc -l || echo 1)
  TP="$GPU_CT"
fi

# Optional HF login (non-interactive)
if [[ -n "${HF_TOKEN:-}" ]] && ! grep -q "machine-huggingface" ~/.netrc 2>/dev/null; then
  "$VENV_DIR/bin/huggingface-cli" login --token "$HF_TOKEN" --add-to-git-credential || true
fi

ENFORCE_FLAG=""
[[ "$ENFORCE_EAGER" = "1" ]] && ENFORCE_FLAG="--enforce-eager"

# Prefer explicit KV sizing when provided, else fall back to GPU utilization
MEM_ARGS=()
if [[ -n "$KV_CACHE_MEMORY" ]]; then
  MEM_ARGS+=(--kv-cache-memory "$KV_CACHE_MEMORY")
else
  MEM_ARGS+=(--gpu-memory-utilization "$GPU_MEM_UTIL")
fi

exec "$VENV_DIR/bin/vllm" serve "$MODEL_ID" \
  --host 0.0.0.0 --port "$PORT" \
  --dtype bfloat16 \
  --tensor-parallel-size "$TP" \
  --max-model-len "$MAX_MODEL_LEN" \
  --enable-chunked-prefill \
  --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --served-model-name tiiuae/Falcon-H1-34B-Instruct \
  --download-dir "$HF_HOME" \
  "${MEM_ARGS[@]}" \
  $ENFORCE_FLAG
LAUNCH
chmod +x /usr/local/bin/vllm-start

# ---- G) Supervisor program entry
install -d -m 0755 /var/log/vllm
cat >/etc/supervisor/conf.d/vllm.conf <<'"SUPPROG"'
[program:vllm]
command=/bin/bash -lc /usr/local/bin/vllm-start
directory=/
autostart=true
autorestart=true
startsecs=180
startretries=20
stopsignal=TERM
stopasgroup=true
killasgroup=true
stdout_logfile=/var/log/vllm/stdout.log
stderr_logfile=/var/log/vllm/stderr.log
stdout_logfile_maxbytes=10MB
stderr_logfile_maxbytes=10MB
stdout_logfile_backups=5
stderr_logfile_backups=5
environment=TMPDIR="/ephemeral/tmp",HF_HOME="/ephemeral/hf-cache",HUGGINGFACE_HUB_CACHE="/ephemeral/hf-cache/hub",HF_HUB_ENABLE_HF_TRANSFER="1",PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True",OMP_NUM_THREADS="1",CUDA_DEVICE_MAX_CONNECTIONS="1",NCCL_P2P_LEVEL="NVL",NCCL_IB_DISABLE="1"
SUPPROG

# ---- H) Reload + start under Supervisor
supervisorctl reread || true
supervisorctl update || true
supervisorctl start vllm || true

echo
echo "=== Done ==="
echo "Edit /etc/default/vllm if needed (MODEL_ID, PORT, TP, GPU_MEM_UTIL, KV_CACHE_MEMORY, etc.), then: supervisorctl restart vllm"
echo "Health: vllm-health 8000"
echo "Logs:   supervisorctl tail -f vllm stderr    # or stdout"
'
