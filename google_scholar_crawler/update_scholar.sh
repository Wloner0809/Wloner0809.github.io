#!/bin/bash
#
# update_scholar.sh — Refresh Google Scholar data and push it to GitHub.
#
# Why this runs locally: Google serves GitHub Actions runners a CAPTCHA, so the
# cloud workflow could never finish. This machine reaches Scholar fine.
#
# Everything is resolved at runtime, so the script works unchanged on any Mac:
#   - repo root  -> derived from this file's location
#   - python     -> first non-SIP interpreter found (launchd can't use /usr/bin)
#   - git        -> same rule
#
# Usage:
#   ./update_scholar.sh              # direct connection (default)
#   USE_PROXY=1 ./update_scholar.sh  # route through a local proxy (see PROXY_URL)

set -euo pipefail

# --- Resolve paths (no hardcoding) --------------------------------------
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
done
CRAWLER_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
REPO_DIR="$(cd "${CRAWLER_DIR}/.." && pwd)"
RESULTS_DIR="${CRAWLER_DIR}/results"

export GOOGLE_SCHOLAR_ID="${GOOGLE_SCHOLAR_ID:-w55OAegAAAAJ}"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:7890}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# --- Pick interpreters launchd is actually allowed to run ---------------
# /usr/bin/python3 and /usr/bin/git are SIP-restricted: macOS refuses to pass
# Full Disk Access through to them, so a launchd job using them hangs or dies
# with "Operation not permitted". Prefer Homebrew/conda builds.
find_binary() {
  local name="$1"
  shift
  for candidate in "$@"; do
    [ -x "$candidate" ] && { echo "$candidate"; return 0; }
  done
  # Fall back to PATH lookup, skipping SIP-protected system copies.
  local from_path
  from_path="$(command -v "$name" 2>/dev/null || true)"
  if [ -n "$from_path" ] && [[ "$from_path" != /usr/bin/* ]]; then
    echo "$from_path"
    return 0
  fi
  return 1
}

PYTHON="$(find_binary python3 \
  /opt/homebrew/bin/python3 \
  /usr/local/bin/python3 \
  "${HOME}/miniconda3/bin/python3" \
  "${HOME}/anaconda3/bin/python3")" || {
  log "ERROR: no non-SIP python3 found. Install one, e.g. 'brew install python'."
  exit 1
}

GIT="$(find_binary git \
  /opt/homebrew/bin/git \
  /usr/local/bin/git)" || {
  log "ERROR: no non-SIP git found. Install one, e.g. 'brew install git'."
  exit 1
}

# --- Optional proxy -----------------------------------------------------
if [ "${USE_PROXY:-0}" = "1" ]; then
  log "Routing through proxy ${PROXY_URL}"
  export HTTP_PROXY="${PROXY_URL}" HTTPS_PROXY="${PROXY_URL}"
  export http_proxy="${PROXY_URL}" https_proxy="${PROXY_URL}"
else
  log "Using direct connection (no proxy)"
fi

log "repo=${REPO_DIR}"
log "python=${PYTHON}"
log "git=${GIT}"

# --- Run the crawler ----------------------------------------------------
cd "${CRAWLER_DIR}"
log "Running crawler for GOOGLE_SCHOLAR_ID=${GOOGLE_SCHOLAR_ID}"
if ! "${PYTHON}" main.py > /tmp/scholar_crawl.log 2>&1; then
  log "ERROR: crawler failed. Tail of log:"
  tail -20 /tmp/scholar_crawl.log
  exit 1
fi

CITEDBY="$("${PYTHON}" -c "import json;print(json.load(open('${RESULTS_DIR}/gs_data.json'))['citedby'])")"
log "Crawler OK. Total citedby=${CITEDBY}"

# --- Commit & push only when the data actually changed ------------------
cd "${REPO_DIR}"
if "${GIT}" diff --quiet -- google_scholar_crawler/results/; then
  log "No change in scholar data. Nothing to commit."
  exit 0
fi

log "Scholar data changed. Committing and pushing."
"${GIT}" add google_scholar_crawler/results/gs_data.json \
             google_scholar_crawler/results/gs_data_shieldsio.json
"${GIT}" commit -m "chore: update Google Scholar data (citedby=${CITEDBY})"
"${GIT}" push origin main
log "Pushed successfully."
