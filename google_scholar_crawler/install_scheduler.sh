#!/bin/bash
#
# install_scheduler.sh — Set up the daily Google Scholar refresh on this Mac.
#
# Generates a launchd agent pointing at update_scholar.sh in this repo, then
# loads it. Safe to re-run: it replaces any previous copy.
#
# Usage:
#   ./install_scheduler.sh              # daily at 11:11
#   ./install_scheduler.sh 9 30         # daily at 09:30
#   ./install_scheduler.sh --uninstall  # remove the scheduled job

set -euo pipefail

LABEL="com.yuwang.scholar-update"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
LOG="${HOME}/Library/Logs/scholar-update.log"

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"; done
CRAWLER_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
RUNNER="${CRAWLER_DIR}/update_scholar.sh"

if [ "${1:-}" = "--uninstall" ]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed ${LABEL}."
  exit 0
fi

HOUR="${1:-11}"
MINUTE="${2:-11}"

[ -x "$RUNNER" ] || chmod +x "$RUNNER"

mkdir -p "${HOME}/Library/LaunchAgents"
cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${RUNNER}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>${HOUR}</integer>
        <key>Minute</key><integer>${MINUTE}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${LOG}</string>
    <key>StandardErrorPath</key>
    <string>${LOG}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key><false/>
</dict>
</plist>
PLIST_EOF

plutil -lint "$PLIST" >/dev/null
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed ${LABEL}"
echo "  runs   : daily at $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
echo "  script : ${RUNNER}"
echo "  log    : ${LOG}"
echo
echo "One manual step remains — macOS Full Disk Access."
echo "launchd cannot read this repo until you grant it to your python binary:"
PY="$(command -v python3 || true)"
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  [ -x "$c" ] && PY="$c" && break
done
if [ -n "$PY" ]; then
  REAL="$(python3 -c "import os,sys;print(os.path.realpath('$PY'))" 2>/dev/null || echo "$PY")"
  echo "  System Settings > Privacy & Security > Full Disk Access > +"
  echo "  ${REAL}"
fi
echo
echo "Test it now with:  launchctl start ${LABEL} && sleep 30 && cat '${LOG}'"
