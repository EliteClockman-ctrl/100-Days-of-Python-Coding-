# Day 06 - Co Ca Ngua Game (Ludo style)

Day 6 builds a full horse-race board game using `pygame` with AI players and rule-based movement.

## Gameplay Features
- 4 players (`Red`, `Green`, `Yellow`, `Blue`) with 4 horses each
- Dice-based movement on standard outer track + home lane
- Need `6` to bring a horse out from yard
- Capture opponent on non-safe path squares
- `6` or capture gives extra turn
- Exact roll is required to reach center
- First player to bring all 4 horses home wins

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