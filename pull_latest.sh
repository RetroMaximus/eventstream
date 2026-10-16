#!/usr/bin/env bash
# pull_latest.sh - clone or update eventstream on a headless Raspberry Pi.
# Safe to run repeatedly. Generates an SSH key on first run if missing.
# Bootstraps the venv, dependencies, .env.eventstream, layout, and health check.

set -euo pipefail

# ---------------------------------------------------------------------------
# 0. Self-heal CRLF if this file was checked out on Windows.
# ---------------------------------------------------------------------------
if grep -q $'\r' "$0" 2>/dev/null; then
  echo "[pull_latest] CRLF detected, fixing line endings"
  sed -i 's/\r$//' "$0"
  exec "$0" "$@"
fi

REPO_URL="${1:-git@github.com:RetroMaximus/eventstream.git}"
TARGET_DIR="${2:-$HOME/eventstream}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
KEY_PATH="${KEY_PATH:-$HOME/.ssh/id_ed25519_eventstream}"
GIT_NAME="${GIT_NAME:-RetroMaximus}"
GIT_EMAIL="${GIT_EMAIL:-retromaximus@github}"
VENV_DIR="${VENV_DIR:-.venv}"
ENV_FILE="${ENV_FILE:-.env.eventstream}"

echo "[pull_latest] repo:   $REPO_URL"
echo "[pull_latest] target: $TARGET_DIR"
echo "[pull_latest] key:    $KEY_PATH"
echo "[pull_latest] venv:   $VENV_DIR"
echo "[pull_latest] env:    $ENV_FILE"

# ---------------------------------------------------------------------------
# 1. SSH key
# ---------------------------------------------------------------------------
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY_PATH" ]; then
  echo "[pull_latest] generating SSH key"
  ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$KEY_PATH" -N ""
  echo
  echo "[pull_latest] -------------------------------------------------------------------"
  echo "[pull_latest] PUBLIC KEY - paste into https://github.com/settings/keys"
  echo "[pull_latest] -------------------------------------------------------------------"
  cat "$KEY_PATH.pub"
  echo "[pull_latest] -------------------------------------------------------------------"
  echo
  read -r -p "[pull_latest] press Enter once the key is added to GitHub: " _
else
  echo "[pull_latest] SSH key already exists"
fi

chmod 600 "$KEY_PATH"
chmod 644 "$KEY_PATH.pub"

# ---------------------------------------------------------------------------
# 2. SSH config
# ---------------------------------------------------------------------------
SSH_CONFIG="$HOME/.ssh/config"
touch "$SSH_CONFIG"
chmod 600 "$SSH_CONFIG"

if ! grep -q "IdentityFile $KEY_PATH" "$SSH_CONFIG" 2>/dev/null; then
  echo "[pull_latest] adding github.com host block to $SSH_CONFIG"
  cat >> "$SSH_CONFIG" <<EOF

Host github.com
    HostName github.com
    User git
    IdentityFile $KEY_PATH
    IdentitiesOnly yes
EOF
fi

# ---------------------------------------------------------------------------
# 3. ssh-agent
# ---------------------------------------------------------------------------
if [ -z "${SSH_AUTH_SOCK:-}" ]; then
  eval "$(ssh-agent -s)" >/dev/null
fi
ssh-add "$KEY_PATH" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 4. SSH connectivity test
# ---------------------------------------------------------------------------
echo "[pull_latest] testing SSH to github.com"
if ! ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
  echo "[pull_latest] WARNING: SSH test did not confirm authentication"
  echo "[pull_latest] continuing anyway; git clone may fail"
fi

# ---------------------------------------------------------------------------
# 5. Clone or pull
# ---------------------------------------------------------------------------
if [ ! -d "$TARGET_DIR/.git" ]; then
  echo "[pull_latest] cloning"
  git clone "$REPO_URL" "$TARGET_DIR"
else
  echo "[pull_latest] pulling latest"
  git -C "$TARGET_DIR" pull --ff-only
fi

cd "$TARGET_DIR"

# ---------------------------------------------------------------------------
# 6. venv + deps
# ---------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
  echo "[pull_latest] creating venv at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -e . >/dev/null

# ---------------------------------------------------------------------------
# 7. env file
# ---------------------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
  cp .env.example "$ENV_FILE"
  echo "[pull_latest] created $ENV_FILE"
  echo "[pull_latest] generating EVENTSTREAM_MASTER_KEY and EVENTSTREAM_SESSION_SECRET"

  MASTER_KEY="$(python -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
  SESSION_SECRET="$(python -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"

  # replace placeholder values
  python - "$ENV_FILE" "$MASTER_KEY" "$SESSION_SECRET" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
master = sys.argv[2]
session = sys.argv[3]

text = path.read_text(encoding="utf-8")
text = text.replace("EVENTSTREAM_MASTER_KEY=REPLACE_ME",
                    f"EVENTSTREAM_MASTER_KEY={master}")
text = text.replace("EVENTSTREAM_SESSION_SECRET=REPLACE_ME",
                    f"EVENTSTREAM_SESSION_SECRET={session}")
path.write_text(text, encoding="utf-8")
PY

  echo "[pull_latest] wrote secrets to $ENV_FILE"
  echo "[pull_latest] back up $ENV_FILE somewhere safe; losing the master key loses encrypted data"
else
  echo "[pull_latest] $ENV_FILE already exists, leaving as is"
fi

# ---------------------------------------------------------------------------
# 8. Layout
# ---------------------------------------------------------------------------
python install_init.py

# ---------------------------------------------------------------------------
# 9. Health check
# ---------------------------------------------------------------------------
echo "[pull_latest] running health check"
python main.py --check || {
  echo "[pull_latest] health check failed, see output above"
  exit 1
}

echo
echo "[pull_latest] done"
echo "[pull_latest] activate with: source $VENV_DIR/bin/activate"
echo "[pull_latest] run with:      python main.py"