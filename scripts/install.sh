#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
target="$data/tilo-menu"
assets="$root/data/themes/Menu/Vista"
archive="${TILO_GNOMENU_ARCHIVE:-$HOME/Downloads/gnomenu-2.9.1.tar.gz}"

if [[ ! -f "$assets/themedata.xml" ]]; then
  mkdir -p "$assets"
  temp="$(mktemp -d)"
  trap 'rm -rf "$temp"' EXIT
  if [[ ! -f "$archive" ]]; then
    archive="$temp/gnomenu-2.9.1.tar.gz"
    echo 'Downloading original GnoMenu 2.9.1 Vista artwork from Launchpad...'
    curl --fail --location --retry 2 --output "$archive" 'https://launchpad.net/gnomenu/trunk/2.9.1/+download/gnomenu-2.9.1.tar.gz'
  fi
  tar -xzf "$archive" -C "$temp" --wildcards 'gnomenu/src/share/gnomenu/Themes/Menu/Vista/*'
  cp -a "$temp/gnomenu/src/share/gnomenu/Themes/Menu/Vista/." "$assets/"
fi

mkdir -p "$target" "$data/applications" "$HOME/.local/bin"
cp -a "$root/tilomenu" "$target/"
mkdir -p "$target/data/themes/Menu"
cp -a "$assets" "$target/data/themes/Menu/"
cat > "$HOME/.local/bin/tilo-menu" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$target\${PYTHONPATH:+:\$PYTHONPATH}"
exec /usr/bin/python3 -m tilomenu.menu "$target/data/themes/Menu/Vista" "\$@"
EOF
chmod +x "$HOME/.local/bin/tilo-menu"
cat > "$data/applications/tilo-menu.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Tilo Menu Preview
Comment=GnoMenu-style application menu for MATE
Exec=$HOME/.local/bin/tilo-menu
Icon=start-here
Terminal=false
Categories=Utility;
EOF
echo 'Installed Tilo Menu Preview. Run ~/.local/bin/tilo-menu or open it from the MATE applications menu.'
