# Day 05 - XO Game (Tic-Tac-Toe)

A polished XO game built with `pygame`.

## Features
- Main menu with `Player vs AI` and `2 Players`
- AI difficulty toggle: `Easy`, `Medium`, and `Hard`
- Smart `Hard` AI using minimax
- Match mode: first to `5` points wins the full match
- Bigger XO play area for easier and clearer gameplay
- Web audio integrated for move, button click, draw, round win, and match win
- Scoreboard for `X`, `O`, and `Draw`
- Winner highlight line and round status panel
- In-game controls: `New Round`, `New Match`, `Main Menu`

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
- Use `New Match` when someone reaches `5` to start a fresh race.

## Web Audio Sources
- OpenGameArt Pong SFX: `Pop.ogg`, `Score.ogg`
- pygame GitHub example assets: `move.wav`, `draw.wav`, `match.wav`, `click.wav`
