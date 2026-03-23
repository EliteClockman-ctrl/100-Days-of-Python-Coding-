# Day 04 - Ping Pong Game

A polished Pong-style arcade game built with `pygame` for Day 4.

## Features
- Main Menu: `Start Vs AI`, `Start 2 Players`, `Settings`, `Quit`
- Settings: target score, AI speed, master volume
- Smooth gameplay at high FPS with paddle spin/reflection
- Particle impact effects and score flash effect
- Pause system (`Esc`) and quick restart (`R`)
- Winner result card with rematch options
- Persistent profile (`profile.json`) for settings

## Web Resources Used
- Sound FX: OpenGameArt `Pong_sfx.zip` (Pop.ogg, Score.ogg)
- Pixel font: Google Fonts `PressStart2P-Regular.ttf`
- Background image: Picsum Photos random image endpoint

## Setup
1. `cd Day-04_Ping-Pong-Game`
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Run:
   `python game.py`

## Controls
- `W/S`: Left paddle
- `UP/DOWN`: Right paddle in PvP mode
- `ESC`: Pause/Resume during match
- `R`: Restart match
- `Space`: Play again on result screen

## Notes
- If assets fail to load, the game still runs with safe fallback colors/fonts.
- For best experience, use fullscreen desktop resolution close to `1280x720`.