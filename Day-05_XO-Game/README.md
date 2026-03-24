# Day 05 - XO Game (Tic-Tac-Toe)

A polished XO game built with `pygame`.

## Features
- Main menu with `Player vs AI` and `2 Players`
- AI difficulty toggle: `Easy` and `Hard`
- Smart `Hard` AI using minimax
- Scoreboard for `X`, `O`, and `Draw`
- Winner highlight line and round status panel
- In-game controls: `New Round`, `Reset Scores`, `Main Menu`

## Setup
1. `cd Day-05_XO-Game`
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Run:
   `python game.py`

## Controls
- Mouse click to place `X` or `O`
- `R` to start a new round
- `M` to return to main menu
- `ESC` to go back/quit

## Notes
- Player symbol is `X`; AI symbol is `O` in AI mode.
- Settings and scoreboard are stored in `profile.json`.