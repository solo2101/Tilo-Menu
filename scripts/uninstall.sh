#!/usr/bin/env bash
set -euo pipefail
data="${XDG_DATA_HOME:-$HOME/.local/share}"
rm -rf "$data/tilo-menu"
rm -f "$data/applications/tilo-menu.desktop" "$HOME/.local/bin/tilo-menu"
echo 'Tilo Menu Preview removed.'
