#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=================================================="
echo "          Installing Kapture Requirements         "
echo "=================================================="

# Detect sudo/root
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        echo "[!] Warning: sudo not found. If package installation fails, please run as root."
    fi
fi

# 1. Install System Dependencies via Package Manager
echo "[*] Step 1/3: Checking and installing system packages..."

if command -v apt-get >/dev/null 2>&1; then
    echo "[*] Detected Debian/Ubuntu/Kali Linux (apt)..."
    $SUDO apt-get update -y || true
    $SUDO apt-get install -y \
        ffmpeg \
        xclip \
        xdotool \
        pulseaudio-utils \
        libnotify-bin \
        xdg-utils \
        libx11-6 \
        libx11-dev \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-pyqt6 \
        python3-pil || echo "[!] Some system packages could not be installed via apt. Continuing..."
elif command -v pacman >/dev/null 2>&1; then
    echo "[*] Detected Arch Linux (pacman)..."
    $SUDO pacman -S --needed --noconfirm \
        ffmpeg \
        xclip \
        xdotool \
        libpulse \
        libnotify \
        xdg-utils \
        libx11 \
        python \
        python-pip \
        python-pyqt6 \
        python-pillow || echo "[!] Some system packages could not be installed via pacman. Continuing..."
elif command -v dnf >/dev/null 2>&1; then
    echo "[*] Detected Fedora/RHEL (dnf)..."
    $SUDO dnf install -y \
        ffmpeg \
        xclip \
        xdotool \
        pulseaudio-utils \
        libnotify \
        xdg-utils \
        libX11 \
        python3 \
        python3-pip \
        python3-pyqt6 \
        python3-pillow || echo "[!] Some system packages could not be installed via dnf. Continuing..."
else
    echo "[!] Unknown package manager. Please ensure ffmpeg, xclip, xdotool, pactl, and PyQt6 are installed."
fi

# 2. Install Python Dependencies
echo "[*] Step 2/3: Verifying and installing Python dependencies..."
python3 -m pip install -r requirements.txt 2>/dev/null || \
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null || \
echo "[*] Python packages already satisfied."

# Install package in editable/local mode
python3 -m pip install -e . --no-deps 2>/dev/null || \
python3 -m pip install -e . --no-deps --break-system-packages 2>/dev/null || true

# 3. Setup CLI command & Desktop Shortcut
echo "[*] Step 3/3: Setting up desktop shortcut and command-line tool..."
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$DIR/run" "$BIN_DIR/kapture"

# Install icon
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$ICON_DIR"
if [ -f "$DIR/assets/kapture.png" ]; then
    cp "$DIR/assets/kapture.png" "$ICON_DIR/kapture.png"
fi

# Install desktop entry
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"
if [ -f "$DIR/kapture.desktop" ]; then
    sed -e "s|Exec=kapture|Exec=$BIN_DIR/kapture|" \
        -e "s|Icon=kapture|Icon=$ICON_DIR/kapture.png|" \
        "$DIR/kapture.desktop" > "$APPS_DIR/kapture.desktop"
    chmod +x "$APPS_DIR/kapture.desktop"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

# Check PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    if [ -f "$HOME/.bashrc" ] && ! grep -q 'PATH.*\.local/bin' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
fi

echo ""
echo "=================================================="
echo "          Kapture Installed Successfully!         "
echo "=================================================="
echo "You can now run Kapture using any of the following:"
echo "  - Terminal:  kapture  (or ./run)"
echo "  - Menu:      Search for 'Kapture' in your application launcher"
echo "  - Self-test: make self-test"
echo "=================================================="
