# 🐍 Snake Game with Hand Gesture Control

A modern Snake game implementation with **hand gesture control** using computer vision, featuring multiple game modes, leaderboard system, and power-ups.

## ✨ Features

### Game Modes
- **Classic Mode**: Traditional snake gameplay with wrapping borders
- **Arcade Mode**: Obstacles that increase with difficulty level
- **Zen Mode**: Infinite gameplay with no death

### Hand Gesture Controls
- Control the snake by moving your hand in front of the camera
- Real-time hand tracking using MediaPipe
- Automatic fallback to keyboard controls if no camera detected

### Gameplay Features
- **Power-ups System**:
  - Speed Boost (yellow) - Temporary speed increase
  - Score Multiplier (orange) - 2x points
  - Shield (blue) - Protects from one obstacle collision
- **Progressive Difficulty**: Game difficulty increases every 200 points
- **Combo System**: Track consecutive food eaten
- **Particle Effects**: Visual feedback for actions
- **Leaderboard**: Top 10 high scores with player names

### Controls
- **Hand Gestures**: Move your hand up/down/left/right
- **Keyboard**: Arrow keys or WASD
- **H**: Toggle help menu
- **L**: View leaderboard
- **R**: Restart game
- **M**: Return to main menu (after game over)
- **Q**: Quit game

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Webcam (optional, for hand gesture control)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/snake_game.git
cd snake_game
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎮 How to Play

1. Start the game:
```bash
python src/main.py
```

2. Select your game mode using **UP/DOWN** arrow keys and press **ENTER**

3. Control the snake:
   - Move your hand in front of the camera, OR
   - Use arrow keys/WASD

4. Collect red food to grow and score points

5. Grab power-ups for special abilities

6. Avoid hitting yourself (or obstacles in Arcade mode)

## 📦 Project Structure

```
snake_game/
├── src/
│   ├── main.py           # Main game loop and UI
│   ├── snake.py          # Game logic and mechanics
│   └── hand_tracking.py  # Hand gesture detection
├── assets/               # (Reserved for future assets)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🛠️ Technical Details

### Technologies Used
- **pygame**: Game rendering and UI
- **OpenCV**: Video capture and image processing
- **MediaPipe**: Hand tracking and gesture detection
- **NumPy**: Numerical computations

### Game Mechanics
- Grid-based movement (20x20 pixel blocks)
- Toroidal world (wrap-around borders)
- Real-time collision detection
- Dynamic obstacle generation (Arcade mode)
- Persistent leaderboard storage

## 🎯 Scoring System

- Food: 10 points × difficulty level × active multiplier
- Power-up: 50 points
- Combo multiplier increases with consecutive food collection

## 📝 Future Enhancements

- [ ] Sound effects and background music
- [ ] Additional power-up types
- [ ] Customizable themes
- [ ] Multiplayer mode
- [ ] More game modes
- [ ] Achievement system

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Created with ❤️ by [Your Name]

## 🙏 Acknowledgments

- MediaPipe for hand tracking technology
- pygame community for excellent documentation
- OpenCV for computer vision tools

---

**Enjoy playing!** 🎮✨
