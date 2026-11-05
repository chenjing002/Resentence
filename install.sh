#!/bin/bash
# Install the launchd agent that runs sync.sh when the Rewords export changes,
# when the network changes, and every 15 minutes (retries pushes made while offline).
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
SRC="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Rewords/rewords-vocabulary.json"
LABEL="com.chenjing002.resentence"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$REPO/sync.sh</string></array>
  <key>WatchPaths</key>
  <array>
    <string>$SRC</string>
    <string>$(dirname "$SRC")</string>
    <string>/Library/Preferences/SystemConfiguration</string>
  </array>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$REPO/sync.log</string>
  <key>StandardErrorPath</key><string>$REPO/sync.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $PLIST — log: $REPO/sync.log"
