# Day 06 - Horse Race Ludo (Business Edition)

Day 6 builds a professional horse-race board game using `pygame` with AI players, web textures, and an all-English UI.

## Gameplay Features
- 4 players (`Red`, `Green`, `Yellow`, `Blue`) with 4 horses each
- Dice-based movement on standard outer track + home lane
- Need `6` to bring a horse out from yard
- Capture opponent on non-safe path squares
- `6` or capture gives extra turn
- Exact roll is required to reach center
- First player to bring all 4 horses home wins
- Business-style dashboard with event feed and animated dice display
- Horse texture loaded from web source (Noto horse image)

## Controls
- `Space` or click `Roll Dice` to roll
- Click highlighted horse to move
- `End Turn` to skip when needed
- `New Game` to reset full board
- `Esc` to return menu

## Setup
1. `cd Day-06_Co-Ca-Ngua-Game`
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Run:
   `python game.py`

## Notes
- Human controls one color; other colors are AI.
- You can change human color and toggle sound in menu.
- Rules implemented follow common Ludo / Co Ca Ngua variant.
- If `horse_realistic.png` exists, the game uses it as primary horse texture.
