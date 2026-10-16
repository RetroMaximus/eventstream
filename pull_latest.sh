
#!/usr/bin/env bash
# pull_latest.sh - clone or update eventstream on a headless Raspberry Pi.
# Safe to run repeatedly. Generates an SSH key on first run if missing.

set -euo pipefail

REPO_URL="${1:-git@github.com:RetroMaximus/eventstream.git}"
TARGET_DIR="${2:-$HOME/eventstream}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
KEY_PATH="${KEY_PATH:-$HOME/.ssh/id_ed25519_eventstream}"
GIT_NAME="${GIT_NAME:-RetroMaximus}"
GIT_EMAIL="${GIT_EMAIL:-retromaximus@github}"

echo "[pull_latest] repo:   $REPO_URL"
echo "[pull_latest] target: $TARGET_DIR"
echo "[pull_latest] key:    $KEY_PATH"

# ---------------------------------------------------------------------------
# 1. SSH key
# ---------------------------------------------------------------------------
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY_PATH" ]; then
  echo "[pull_latest] generating SSH key"
  ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$KEY_PATH" -N ""
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
# 4. Clone or pull
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
# 5. venv + deps
# ---------------------------------------------------------------------------
if [ ! -d ".venv" ]; then
  echo "[pull_latest] creating venv"
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -e . >/dev/null

# ---------------------------------------------------------------------------
# 6. .env
# ---------------------------------------------------------------------------
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[pull_latest] created .env - edit it before first run"
fi

# ---------------------------------------------------------------------------
# 7. Layout
# ---------------------------------------------------------------------------
python install_init.py

echo "[pull_latest] done"
echo "[pull_latest] activate with: source .venv/bin/activate"
echo "[pull_latest] run with:      python main.py --check"


