# vLLM + Supervisor

## Quick start (run as **root** on a fresh GPU box)

> Paste the **entire block below** and run it. It installs deps, sets up a venv, drops a configurable defaults file, creates the launcher, wires up Supervisor, and smoke-tests the API.

```
#!/usr/bin/env bash
set -euo pipefail

# -------- settings you can tweak --------
MODEL_ID="tiiuae/Falcon-H1-34B-Instruct"
PORT=8000
DISK_ROOT="/ephemeral"
VENV_DIR="/opt/vllm-venv"
TP_DEFAULT=2
# export HUGGINGFACE_HUB_TOKEN=hf_xxx   # uncomment if needed

# 1) deps
apt-get update -y
apt-get install -y python3-venv python3-pip git curl jq htop tmux numactl supervisor

# 2) python env + libs
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install -U pip wheel setuptools
pip install -U "vllm" "transformers>=4.44" "accelerate" "hf-transfer"

# 3) defaults file (editable later)
install -d "$DISK_ROOT"/{tmp,hf-cache} "$DISK_ROOT/hf-cache"/{hub,transformers}
cat >/etc/default/vllm <<EOF
MODEL_ID=${MODEL_ID}
PORT=${PORT}
TP=${TP_DEFAULT}
DISK_ROOT=${DISK_ROOT}
VENV_DIR=${VENV_DIR}
# HUGGINGFACE_HUB_TOKEN=hf_xxx
EOF
chmod 600 /etc/default/vllm

# 4) launcher script (sources /etc/default/vllm if present)
cat >/usr/local/bin/vllm-start <<'SH'
#!/usr/bin/env bash
set -euo pipefail

# load overrides
if [[ -f /etc/default/vllm ]]; then set -a; . /etc/default/vllm; set +a; fi

MODEL_ID="${MODEL_ID:-tiiuae/Falcon-H1-34B-Instruct}"
PORT="${PORT:-8000}"
DISK_ROOT="${DISK_ROOT:-/ephemeral}"
VENV_DIR="${VENV_DIR:-/opt/vllm-venv}"
TP_WANTED="${TP:-2}"

mkdir -p "$DISK_ROOT/tmp" "$DISK_ROOT/hf-cache"/{hub,transformers}
export TMPDIR="$DISK_ROOT/tmp"
export HF_HOME="$DISK_ROOT/hf-cache"
export HUGGINGFACE_HUB_CACHE="$DISK_ROOT/hf-cache/hub"
export HF_HUB_ENABLE_HF_TRANSFER=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=1

GPU_CT=$( (nvidia-smi -L 2>/dev/null | wc -l) || echo 1 )
[[ -z "${GPU_CT}" || "${GPU_CT}" -lt 1 ]] && GPU_CT=1
if [[ "${TP_WANTED}" -gt "${GPU_CT}" ]]; then TP="${GPU_CT}"; else TP="${TP_WANTED}"; fi

ulimit -n 65535 || true
pkill -f "vllm serve" || true

exec "$VENV_DIR/bin/vllm" serve "$MODEL_ID" \
  --host 0.0.0.0 --port "${PORT}" \
  --dtype bfloat16 \
  --tensor-parallel-size "${TP}" \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.94 \
  --enable-chunked-prefill \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 64 \
  --download-dir "$HF_HOME"
SH
chmod +x /usr/local/bin/vllm-start

# 5) supervisor program
cat >/etc/supervisor/conf.d/vllm.conf <<'SUP'
[program:vllm]
command=/bin/bash -lc '/usr/local/bin/vllm-start'
directory=/
autostart=true
autorestart=true
startsecs=5
stopsignal=INT
stopwaitsecs=60
stdout_logfile=/var/log/vllm.stdout.log
stderr_logfile=/var/log/vllm.stderr.log
user=root
environment=LC_ALL="C.UTF-8",LANG="C.UTF-8"
SUP

# 6) start / reload supervisor and program
# start supervisord if not already running
pgrep -x supervisord >/dev/null || /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
supervisorctl reread
supervisorctl update
supervisorctl status vllm

# 7) quick test (give it a few seconds to load)
sleep 8
curl -sS http://127.0.0.1:${PORT}/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"'"${MODEL_ID}"'","messages":[{"role":"user","content":"Hello, Falcon!"}],"max_tokens":32}' | jq .
```

## Change config later

Edit `/etc/default/vllm` (MODEL\_ID, PORT, TP, etc.), then:

```bash
supervisorctl restart vllm
```

## Check status & logs

```bash
# status / control
supervisorctl status vllm
supervisorctl restart vllm
supervisorctl stop vllm

# logs
supervisorctl tail -f vllm stdout
supervisorctl tail -f vllm stderr
tail -n 200 /var/log/vllm.stdout.log
tail -n 200 /var/log/vllm.stderr.log
```

## Open the port (optional)

```bash
ufw allow from <YOUR_IP> to any port 8000 proto tcp
```

