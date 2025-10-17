bash -lc 'set -euo pipefail; cat >/root/vllm-supervisor-install.sh << "EOF"
#!/usr/bin/env bash
set -euo pipefail

# ---- 0) Base deps
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3-venv python3-pip supervisor jq git curl htop tmux numactl lsof psmisc

# Ensure Supervisor is running
systemctl enable --now supervisor || true

# ---- 1) Defaults file (edit later to change model/ports)
install -d -m 0755 /etc/default
cat >/etc/default/vllm <<EOD
MODEL_ID=tiiuae/Falcon-H1-34B-Instruct
PORT=8000
# Optional: set TP to pin tensor-parallel, else it auto-detects GPUs
# TP=2
DISK_ROOT=/ephemeral
VENV_DIR=/opt/vllm-venv

# Stable knobs that worked well with Falcon-H1
MAX_MODEL_LEN=8192
GPU_MEM_UTIL=0.88
MAX_NUM_BATCHED_TOKENS=12000
MAX_NUM_SEQS=6

# Optional HF token for gated models:
# HF_TOKEN=
EOD

# ---- 2) Python env + packages
. /etc/default/vllm
python3 -m venv "$VENV_DIR" || true
source "$VENV_DIR/bin/activate"
python -m pip install -U pip wheel setuptools
pip install -U "vllm==0.10.2" "transformers>=4.44" "accelerate" "hf-transfer"

# ---- 3) Launcher script for vLLM (Supervisor will run this)
cat >/usr/local/bin/vllm-start << "EOD"
#!/usr/bin/env bash
set -euo pipefail
[[ -f /etc/default/vllm ]] && set -a && . /etc/default/vllm && set +a

# Defaults if not in /etc/default/vllm
MODEL_ID=${MODEL_ID:-tiiuae/Falcon-H1-34B-Instruct}
PORT=${PORT:-8000}
DISK_ROOT=${DISK_ROOT:-/ephemeral}
VENV_DIR=${VENV_DIR:-/opt/vllm-venv}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}
GPU_MEM_UTIL=${GPU_MEM_UTIL:-0.88}
MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-12000}
MAX_NUM_SEQS=${MAX_NUM_SEQS:-6}

# Storage & env
mkdir -p "$DISK_ROOT/tmp" "$DISK_ROOT/hf-cache"/{hub,transformers}
export TMPDIR="$DISK_ROOT/tmp"
export HF_HOME="$DISK_ROOT/hf-cache"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_ENABLE_HF_TRANSFER=${HF_HUB_ENABLE_HF_TRANSFER:-1}
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
ulimit -n 65535 || true

# Tensor-parallel: use TP from defaults if set, else auto = GPU count
GPU_CT=$(nvidia-smi -L 2>/dev/null | wc -l || echo 1)
TP="${TP:-}"
if [[ -z "$TP" ]]; then TP="$GPU_CT"; fi
(( TP < 1 )) && TP=1
(( TP > GPU_CT )) && TP=$GPU_CT

# Optional HF login (non-interactive) if token provided
if [[ -n "${HF_TOKEN:-}" ]] && ! grep -q "machine-huggingface" ~/.netrc 2>/dev/null; then
  "$VENV_DIR/bin/huggingface-cli" login --token "$HF_TOKEN" --add-to-git-credential || true
fi

exec "$VENV_DIR/bin/vllm" serve "$MODEL_ID" \
  --host 0.0.0.0 --port "$PORT" \
  --dtype bfloat16 \
  --tensor-parallel-size "$TP" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --enable-chunked-prefill \
  --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --download-dir "$HF_HOME"
EOD
chmod +x /usr/local/bin/vllm-start

# ---- 4) Supervisor program
install -d -m 0755 /var/log/vllm
cat >/etc/supervisor/conf.d/vllm.conf << "EOD"
[program:vllm]
command=/usr/local/bin/vllm-start
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
environment=TMPDIR="/ephemeral/tmp",HF_HOME="/ephemeral/hf-cache",HUGGINGFACE_HUB_CACHE="/ephemeral/hf-cache/hub",HF_HUB_ENABLE_HF_TRANSFER="1",PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True",OMP_NUM_THREADS="1"
EOD

# ---- 5) Start/reload
supervisorctl reread || true
supervisorctl update || true
supervisorctl start vllm || true

echo
echo "=== Done ==="
echo "Edit settings in /etc/default/vllm (MODEL_ID, PORT, TP, etc.), then: supervisorctl restart vllm"
echo "Watch logs:"
echo "  supervisorctl tail -f vllm stdout"
echo "  supervisorctl tail -f vllm stderr"
EOF
bash /root/vllm-supervisor-install.sh'
