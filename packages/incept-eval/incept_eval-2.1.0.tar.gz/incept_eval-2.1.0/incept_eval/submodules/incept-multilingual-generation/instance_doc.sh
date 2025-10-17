#!/usr/bin/env bash
set -euo pipefail

# ===== 0) Vars you might tweak =====
MODEL_ID="tiiuae/Falcon-H1-34B-Instruct"
PORT=8000
TP=2                               # two GPUs
DISK_ROOT="/ephemeral"             # the large attached disk
VENV_DIR="/opt/vllm-venv"
HF_TOKEN=""                        # optional: put a HF token if the model is gated

# ===== 1) Base OS deps (Ubuntu 22.04) =====
apt-get update -y
apt-get install -y python3-venv python3-pip git curl htop tmux numactl jq

# ===== 2) Python env =====
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install -U pip wheel setuptools
# Pin to the version you validated
pip install -U "vllm==0.10.2" "transformers>=4.44" "accelerate" "hf-transfer"

# ===== 3) Storage layout (put tmp + HF cache on big disk) =====
mkdir -p "$DISK_ROOT/tmp" "$DISK_ROOT/hf-cache"/{hub,transformers}
export TMPDIR="$DISK_ROOT/tmp"
export HF_HOME="$DISK_ROOT/hf-cache"
export HUGGINGFACE_HUB_CACHE="$DISK_ROOT/hf-cache/hub"
# Faster HF downloads:
export HF_HUB_ENABLE_HF_TRANSFER=1
# More stable CUDA allocations for long runs:
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# Keep CPU threads tame so uvloop / tokenization don't thrash
export OMP_NUM_THREADS=1

# (optional) login to HF if needed
if [[ -n "$HF_TOKEN" ]]; then
  huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential
fi

# Allow many inbound sockets (useful under load)
ulimit -n 65535 || true

# ===== 4) Stop any old vLLM =====
pkill -f "vllm serve" || true

# ===== 5) Run the server =====
# Falcon-H1 uses hybrid/mamba; prefix caching is auto-disabled internally.
# Stability-friendly knobs that worked well for you:
GPU_MEM_UTIL=0.88
MAX_NUM_BATCHED_TOKENS=12000
MAX_NUM_SEQS=6

exec vllm serve "$MODEL_ID" \
  --host 0.0.0.0 --port "$PORT" \
  --dtype bfloat16 \
  --tensor-parallel-size "$TP" \
  --max-model-len 8192 \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --enable-chunked-prefill \
  --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --download-dir "$HF_HOME"

# ===== 6) (Optional) quick test from this box =====
# curl -s http://127.0.0.1:$PORT/v1/chat/completions \
#   -H "Content-Type: application/json" \
#   -d '{"model":"'"$MODEL_ID"'","messages":[{"role":"user","content":"Reply with the number 7 only."}],"max_tokens":8,"temperature":0}' | jq .
