# 100 Days Of Python Coding

Series of daily Python projects designed to build up skills with consistent, manageable bite-sized challenges.

## Why this repo
- Each day lives in a dedicated folder (`Day-01_Snake-Game`, etc.) so you can track progress per task.
- Every folder follows the same structure: `README.md` explaining the sprint, `requirements.txt` for dependencies, and Python code that you can run directly.
- The root README keeps the series goals, workflow, and daily checklist so it is easy to onboard future collaborators or review the overall plan.

## How to use
1. Pick a day folder (start with `Day-01_Snake-Game` for the Snake prototype).
2. Read that folder's README for its specific goal and setup instructions.
3. Install dependencies with `pip install -r requirements.txt` inside the chosen folder.
4. Run the Python script described there (e.g., `python game.py`).
5. Commit whatever you change, push a new branch, and repeat the next day with a fresh folder.

## Current days
- Day 01: `Day-01_Snake-Game` (Snake Game with menu + sounds).
- Day 02: `Day-02_Chess-Game` (Chess Game with pygame, full rules, Stockfish/fallback AI, UI + sounds).
- Day 03: `Day-03_QR-Code-Generator` (Desktop QR generator with presets, styling, and export).

## Daily workflow
- Plan a feature or learning goal before coding.
- Keep the code clean and document important design or UX decisions in that day's README.
- If assets are needed (sounds, images), keep them inside that day's folder to avoid cluttering the top level.
- Export or log progress (e.g., `features_report.json`) so you can summarize each sprint.
