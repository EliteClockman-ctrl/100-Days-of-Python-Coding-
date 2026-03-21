# Day 01 - Snake Game

Professional Snake game for the 100 Days of Python challenge, built with `pygame`.

## Features
- Main Menu with navigation (`Start`, `Mode`, `Settings`, `Stats`, `Exit`).
- Main Menu now includes `Features` tracker screen.
- Multi-language UI (`VI/EN`) switchable from settings.
- Multiple game modes: `classic`, `zen`, `walls`, `timed`, `portal`.
- Score + best score + leaderboard (top 10) persisted to local profile.
- Theme switching and gameplay tuning (`speed`, `grid`, `sound`, `volume`).
- Smooth snake movement, collisions, special food, pause/restart flow.
- Feature roadmap management: mark each feature as `ready/in_progress/done`.
- Export feature progress report to `features_report.json` directly in game.

## Project structure
```text
Day-01_Snake-Game/
|-- game.py
|-- requirements.txt
`-- README.md
```

## Setup
1. Open terminal in `Day-01_Snake-Game`.
2. Install dependency:
   `pip install -r requirements.txt`
3. Start game:
   `python game.py`

## Controls
- Move: `Arrow keys` or `WASD`
- Pause/Resume: `P` or `Esc`
- Restart after game over: `R`
- Back to menu: `M`
- Quit from menu: `Esc`
- In `Features` screen:
  - Navigate items: `Up/Down`
  - Change page: `Left/Right`
  - Change status: `Enter` or `Space`
  - Export report: `E`

## Day 01 learning goals
- Build a full game loop (`event -> update -> render`).
- Organize game logic using classes and small methods.
- Handle state transitions (`running`, `game over`, `restart`) cleanly.
