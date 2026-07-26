# Snake Game - Hand Gesture Control

[![Release](https://img.shields.io/github/v/release/mizhab-as/Snake-Game?style=flat-square&color=2bbc8a)](https://github.com/mizhab-as/Snake-Game/releases)
[![Build & Release](https://img.shields.io/github/actions/workflow/status/mizhab-as/Snake-Game/build.yml?style=flat-square&label=build)](https://github.com/mizhab-as/Snake-Game/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/github/license/mizhab-as/Snake-Game?style=flat-square)](LICENSE)

A modern desktop Snake game built with Python, Pygame-CE, OpenCV, and MediaPipe. Play using real-time hand swipe gestures captured by your webcam, or use traditional keyboard controls. Features multiple game modes, inter-dimensional warp portals, dynamic power-up drops, customizable themes, local leaderboards, and synthesized audio.

![Modern Arcade Mode Gameplay](assets/screenshots/2.png)

---

## Downloads

Get zero-dependency, pre-packaged binaries directly from **[GitHub Releases](https://github.com/mizhab-as/Snake-Game/releases)**:

| Platform | Download | Instructions |
|---|---|---|
| **macOS** | `SnakeGame_macOS.zip` | Extract zip and launch `SnakeGame.app` |
| **Windows** | `SnakeGame.exe` | Double-click to run (no install needed) |

---

## Gameplay & Features

### ✋ Real-Time Gesture Tracking
- Powered by **MediaPipe Hands** and **OpenCV** to track spatial hand movement.
- Uses Landmark 9 (Middle Finger MCP) as a stable palm anchor point to eliminate fingertip noise.
- Smooth swipe recognition (**UP**, **DOWN**, **LEFT**, **RIGHT**) with 10-frame movement averaging (`deque`).
- Live webcam Picture-in-Picture (PIP) feed with on-screen motion tracking overlay.

### 🎮 Game Modes
- **Classic**: Traditional Snake experience with wrapping borders and progressive speed scaling.
- **Arcade**: Dynamic game field featuring random obstacles, inter-dimensional warp portals (teleporting from Portal A to Portal B), and timed power-up spawns.
- **Zen**: relaxed, mortality-free mode for testing gestures or casual play without game-over states.

### ⚡ Power-Ups & Items
- 🛡️ **Shield**: Negates a single fatal crash into obstacles or snake body segments.
- ⚡ **Speed Boost**: Temporarily increases movement speed for fast traversal.
- ❄️ **Freeze**: Halves game tick rate for fine control in dense obstacle areas.
- ✖️ **2x Multiplier**: Doubles points earned for all food collected while active.
- 👻 **Ghost**: Allows passing through body segments unharmed.

### 🎨 Visual Themes & Customization
- **Modern**: Charcoal matte dark layout with radial glow accents, line grid, rounded UI elements, and particle bursts.
- **Retro**: Nostalgic 2-bit Game Boy green LCD aesthetic with dark pixel blocks.
- **Skins**: Switch between **Chameleon** (dynamic color shifting), **Neon Glow**, and **Rainbow**.

### 🎵 Native Audio Synthesis
- Custom-synthesized sound effects produced on-the-fly using NumPy audio buffers in Pygame-CE (no external audio files required).

---

<div align="center">

## Visual Showcase

<table>
  <tr>
    <th width="50%">Mode Selection</th>
    <th width="50%">Settings Menu</th>
  </tr>
  <tr>
    <td><img src="assets/screenshots/1.png" alt="Mode Select Screen"></td>
    <td><img src="assets/screenshots/5.png" alt="Settings Menu"></td>
  </tr>
  <tr>
    <th width="50%">Retro LCD Theme</th>
    <th width="50%">Leaderboard & Game Over</th>
  </tr>
  <tr>
    <td><img src="assets/screenshots/6.png" alt="Retro Theme"></td>
    <td><img src="assets/screenshots/4.png" alt="Leaderboard Screen"></td>
  </tr>
</table>

<p>
📹 <b>Video Demo</b>: A full gameplay video demonstration is included at <a href="assets/videos/11.mp4"><code>assets/videos/11.mp4</code></a>.
</p>

</div>

---

## Quick Controls

| Function | Hand Gesture | Keyboard Shortcut |
|---|---|---|
| **Directional Movement** | Swipe Up / Down / Left / Right | `↑` `↓` `←` `→` or `WASD` |
| **Menu Navigation** | — | `Up` / `Down` + `Enter` |
| **Settings Menu** | — | `H` |
| **Cycle Theme** | — | `C` |
| **Cycle Snake Skin** | — | `S` |
| **Toggle Mute / Audio** | — | `M` |
| **Toggle Camera Hardware** | — | `V` |
| **Cycle Camera Source** | — | `O` |
| **Toggle Motion Overlay** | — | `T` |
| **Toggle Camera PIP** | — | `B` |
| **Toggle Fullscreen** | — | `F` |
| **Cycle Resolution** | — | `P` |
| **Gesture Help Dialog** | — | `?` |
| **Pause / Main Menu / Quit** | — | `Esc` / `M` / `Q` |

---

## Run From Source

### Prerequisites
- Python 3.10 or 3.11
- A webcam (optional if playing with keyboard)

### Quick Start (Automated Scripts)

**macOS / Linux:**
```bash
git clone https://github.com/mizhab-as/Snake-Game.git
cd Snake-Game
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
git clone https://github.com/mizhab-as/Snake-Game.git
cd Snake-Game
run.bat
```

### Manual Installation
```bash
git clone https://github.com/mizhab-as/Snake-Game.git
cd Snake-Game

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch game
python src/main.py
```

---

## Technical Details & Hand Tracking Engine

### Architecture
```
Snake-Game/
├── src/
│   ├── main.py           # Main window creation, UI state machine, render loop, settings dialogs
│   ├── snake.py          # Game state engine, grid collision, power-up timers, portal logic
│   └── hand_tracking.py  # OpenCV camera capture, MediaPipe solution pipeline, swipe filter
├── assets/
│   ├── screenshots/      # High-resolution UI and gameplay screenshots
│   └── videos/           # Gameplay video demonstrations
├── SnakeGame.spec        # macOS PyInstaller build spec (includes MediaPipe graph/model packaging)
├── SnakeGame-Windows.spec# Windows PyInstaller build spec
├── requirements.txt      # Python package requirements
├── run.sh / run.bat      # Environment bootstrapping scripts
└── README.md
```

### Hand Gesture Processing Pipeline
1. **Frame Capture**: OpenCV fetches webcam frames (`CAP_AVFOUNDATION` backend on macOS).
2. **Inference Caching**: `_process_frame_cached()` stores MediaPipe outputs per frame ID, guaranteeing only 1 model pass per game frame update.
3. **Reference Landmark**: Uses Landmark 9 (Middle Finger MCP) for palm center tracking.
4. **Displacement Filtering**: Evaluates spatial movement across a 10-frame window. A swipe registers when axis movement exceeds `0.025` coordinate threshold.
5. **Buffer Reset**: Flushes movement history upon registering a swipe to prevent double-triggering.

---

## Building Executables

The PyInstaller spec files package all necessary MediaPipe resource models (`.tflite`, `.binarypb`) and label files (`handedness.txt`):

```bash
# macOS Build (.app)
pyinstaller -y SnakeGame.spec

# Windows Build (.exe)
pyinstaller -y SnakeGame-Windows.spec
```

The output bundle is generated inside `dist/`.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

Created by **[Mizhab A S](https://github.com/mizhab-as)**.
