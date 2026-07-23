#!/usr/bin/env bash
set -euo pipefail

MOUNT_POINT="${MOUNT_POINT:-/mnt/tagmdl_repo}"
SHARE_PATH="${SHARE_PATH:-\\\\10.1.1.11\\TAGMDL-Repo}"
REPO_RELATIVE="${REPO_RELATIVE:-HomesPlatformRepos/concierge}"
SMOKE_TEST="${SMOKE_TEST:-0}"

if ! mountpoint -q "$MOUNT_POINT"; then
  echo "[bootstrap] Mounting $SHARE_PATH at $MOUNT_POINT"
  sudo mkdir -p "$MOUNT_POINT"
  sudo mount -t drvfs "$SHARE_PATH" "$MOUNT_POINT"
else
  echo "[bootstrap] Mount already available: $MOUNT_POINT"
fi

REPO_DIR="$MOUNT_POINT/$REPO_RELATIVE"
if [[ ! -d "$REPO_DIR" ]]; then
  echo "[bootstrap] ERROR: repo path not found: $REPO_DIR"
  exit 1
fi

VENV_DIR=""
if [[ -d "$HOME/.vens/concierge" ]]; then
  VENV_DIR="$HOME/.vens/concierge"
elif [[ -d "$HOME/.venvs/concierge" ]]; then
  VENV_DIR="$HOME/.venvs/concierge"
else
  VENV_DIR="$HOME/.vens/concierge"
  echo "[bootstrap] Creating venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
cd "$REPO_DIR"

if [[ "$SMOKE_TEST" == "1" ]]; then
  echo "[bootstrap] Running smoke test"
  python -m pytest tests/test_experience_continuity_models.py -q
fi

echo "[bootstrap] Ready"
echo "[bootstrap] Repo: $REPO_DIR"
echo "[bootstrap] Venv: $VENV_DIR"
echo "[bootstrap] Python: $(python --version 2>&1)"
