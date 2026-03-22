# Day 02 — Chess Game (Player vs 2000+ ELO Bot)

This day builds a full chess game in pygame and connects a real engine (Stockfish) for a strong 2000+ ELO AI opponent. It includes a full main menu, settings screen, legal move validation, highlights, move history, clocks, and export tools.

## Features
- Full legal move rules (check, checkmate, stalemate, castling, en passant, promotion).
- Player vs AI using Stockfish with strength limited to 2000+ ELO.
- Fallback AI bot (minimax) if `stockfish.exe` is missing or unavailable.
- Main menu + settings scene (player color, time control, AI mode).
- Event-driven SFX: move, capture, castling, check, and end (checkmate/stalemate/time over).
- Click-to-move UI with legal-move highlights and move list.
- Move undo, board flip, and quick save to PGN/FEN.
- Simple time control (per-side clock).
- Piece textures loaded from web-downloaded PNG files in `assets/textures`.

## Setup
1. `cd Day-02_Chess-Game`
2. Install dependencies:
   `pip install -r requirements.txt`
3. Install Stockfish automatically:
   `python setup_stockfish.py`
4. Run:
   `python chess_game.py`

If you do not install Stockfish, the game still runs with fallback AI (weaker).

## Controls
- Click a piece, then click a destination to move.
- `U` = undo last full move (player + bot).
- `F` = flip board.
- `R` = reset game.
- `P` = save PGN.
- `N` = save FEN.
- `Esc` = quit.
- In `Settings`, you can toggle `Sound` and tune `Sound Volume`.

## Notes
- Engine path is read from `stockfish.exe` in the same folder. If you want a custom path, edit `ENGINE_PATH` in `chess_game.py`.
- This project uses `python-chess` for rules and Stockfish for the AI.
- If Stockfish is not found, the game still works using the built-in fallback AI.
