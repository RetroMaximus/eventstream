
#!/usr/bin/env bash
# push_to_git.sh - commit and push eventstream from the dev machine.
# Usage:
#   bash push_to_git.sh "commit message"
#   bash push_to_git.sh "commit message" git@github.com:RetroMaximus/eventstream.git

set -euo pipefail

COMMIT_MSG="${1:-update}"
REPO_URL="${2:-git@github.com:RetroMaximus/eventstream.git}"
KEY_PATH="${KEY_PATH:-$HOME/.ssh/id_ed25519_eventstream}"
BRANCH="${BRANCH:-main}"

echo "[push_to_git] commit: $COMMIT_MSG"
echo "[push_to_git] remote: $REPO_URL"

# ---------------------------------------------------------------------------
# 1. SSH key check
# ---------------------------------------------------------------------------
if [ ! -f "$KEY_PATH" ]; then
  echo "[push_to_git] ERROR: SSH key not found at $KEY_PATH"
  echo "[push_to_git] run pull_latest.sh first, or generate a key"
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. SSH config
# ---------------------------------------------------------------------------
SSH_CONFIG="$HOME/.ssh/config"
mkdir -p "$HOME/.ssh"
touch "$SSH_CONFIG"
chmod 600 "$SSH_CONFIG"

if ! grep -q "IdentityFile $KEY_PATH" "$SSH_CONFIG" 2>/dev/null; then
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
# 4. Remote setup
# ---------------------------------------------------------------------------
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "[push_to_git] initializing repo"
  git init
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

git branch -M "$BRANCH"

# ---------------------------------------------------------------------------
# 5. Commit
# ---------------------------------------------------------------------------
git add -A

if git diff --cached --quiet; then
  echo "[push_to_git] nothing to commit"
else
  git commit -m "$COMMIT_MSG"
fi

# ---------------------------------------------------------------------------
# 6. Pull then push
# ---------------------------------------------------------------------------
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  git pull --rebase origin "$BRANCH"
fi

git push -u origin "$BRANCH"

echo "[push_to_git] done"

