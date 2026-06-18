#!/bin/bash
CONFIG="$HOME/.portable_ai_environment/claude.env"

echo "[clean] Removing API configuration..."
echo ""

if [ ! -f "$CONFIG" ]; then
  echo "[info] No configuration found at:"
  echo "       $CONFIG"
  echo ""
  echo "Nothing to remove."
else
  rm -f "$CONFIG"
  echo "[done] Removed: $CONFIG"
  echo ""
  echo "Run ai-env/init.sh to set up a new configuration."
fi
