# Kapture

Modern screenshot and screen recording tool for Kali Linux (X11 / XFCE).

![Kapture Icon](assets/kapture.png)

## Installation

### Automatic Installation (Recommended)

Kapture includes an automated installer that checks your system, downloads and installs all system and Python requirements, sets up the command-line shortcut, and adds the desktop launcher to your application menu:

```bash
chmod +x install.sh
./install.sh
```

Or via Makefile:

```bash
make install
```

### Manual Installation

If you prefer to install dependencies manually:

1. **System dependencies** (Kali / Debian / Ubuntu):
   ```bash
   sudo apt update
   sudo apt install -y ffmpeg xclip xdotool pulseaudio-utils libnotify-bin xdg-utils python3-pyqt6 python3-pil
   ```

2. **Python dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or install Kapture as a package
   pip install -e .
   ```

## Running Kapture

```bash
./run            # show popup
./run --hidden   # tray only
make self-test   # verify system environment
make test        # run unit tests
```

When started with `./run`, Kapture will automatically check if Python requirements (`PyQt6`, `Pillow`) are present and download them if needed.

## CLI Usage

```bash
kapture shot full|region|window
kapture record full|region|window
kapture stop|pause|resume|status
kapture settings
```

## Default Hotkeys

- `Super+Print` - full screenshot
- `Ctrl+Alt+S` - region screenshot
- `Ctrl+Alt+W` - window screenshot
- `Ctrl+Alt+R` - toggle recording

Hotkeys are registered in-app and never modify your desktop environment settings. If a key is already grabbed, Kapture disables it and notifies you.

## Notes

- **Output Location**: Screenshots and recorded videos are saved directly to your home directory (`~/` / `/home/<user>`).
- True per-window capture uses ffmpeg `window_id`; works even when the window is covered.
- Full-screen and region recordings hide or place the HUD outside the captured area.
- Pause/resume splits the recording into segments and concatenates them at stop.
- Runtime session cache and logs are kept in `state/`.