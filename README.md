# Snake Game with Hand Gesture Control

A Snake game with hand gesture control using computer vision. Features multiple game modes, leaderboard system, and power-ups.

## Features

### Game Modes
- **Classic**: Traditional snake with wrapping borders
- **Arcade**: Obstacles that increase with difficulty
- **Zen**: No death, infinite gameplay

### Controls
- **Hand Gestures**: Move your hand up/down/left/right to control snake
- **Keyboard**: Arrow keys or WASD
- Press **H** for help, **L** for leaderboard, **R** to restart, **M** for main menu, **Q** to quit

### Gameplay
- Power-ups: Speed Boost, Score Multiplier (2x), Shield
- Progressive difficulty increases every 200 points
- Combo system tracks consecutive food eaten
- Particle effects for visual feedback
- Top 10 leaderboard with player names

## Installation

Requires Python 3.8+ and a webcam (optional for hand tracking).

```bash
git clone https://github.com/mizhab-as/snake_game.git
cd snake_game
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## How to Play

1. Start the game with `python src/main.py`
2. Select mode with UP/DOWN arrows, press ENTER
3. Control snake with hand gestures or keyboard
4. Collect food and power-ups, avoid obstacles
5. Try to beat the high score

## Project Structure

```
snake_game/
├── src/
│   ├── main.py           # Game loop and UI
│   ├── snake.py          # Game logic
│   └── hand_tracking.py  # Hand gesture detection
├── requirements.txt
└── README.md
```

## Tech Stack

- pygame (game engine)
- OpenCV (video capture)
- MediaPipe (hand tracking)
- NumPy (math)

## Scoring

- Food: 10 points × difficulty × multiplier
- Power-up: 50 points
- Combo system for consecutive food

## Contributing

Feel free to report bugs, suggest features, or submit pull requests.

## License

MIT License

## Author

Mizhab A S
