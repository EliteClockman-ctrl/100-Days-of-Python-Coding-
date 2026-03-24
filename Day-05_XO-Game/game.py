"""Day 05 XO Game (Tic-Tac-Toe) built with pygame.

Features:
- Main menu with PvP and PvAI mode
- AI difficulties: Easy and Hard (minimax)
- Scoreboard, winner highlight line, and round reset
- In-game navigation: Main Menu, New Round, Reset Scores
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "profile.json"

SCREEN_W = 1000
SCREEN_H = 680
FPS = 120

SCENE_MENU = "menu"
SCENE_PLAY = "play"

BG_TOP = (24, 30, 48)
BG_BOTTOM = (13, 16, 28)
PANEL = (20, 25, 38)
PANEL_BORDER = (74, 100, 152)
TEXT = (239, 244, 255)
TEXT_MUTED = (175, 186, 210)
ACCENT = (96, 178, 255)
WIN = (255, 196, 102)
X_COLOR = (255, 142, 124)
O_COLOR = (125, 224, 203)
GRID = (98, 118, 170)

BOARD_SIZE = 540
CELL = BOARD_SIZE // 3
BOARD_X = 60
BOARD_Y = 70

DEFAULTS = {
    "difficulty": "Hard",
    "scores": {"X": 0, "O": 0, "Draw": 0},
    "last_mode": "ai",
}


@dataclass
class Button:
    text: str
    rect: pygame.Rect

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, active: bool) -> None:
        bg = (45, 64, 100) if not active else (67, 98, 152)
        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, PANEL_BORDER, self.rect, 2, border_radius=12)
        label = font.render(self.text, True, TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def hit(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class XOGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Day 05 - XO Game")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True

        self.title_font = pygame.font.SysFont("consolas", 54, bold=True)
        self.head_font = pygame.font.SysFont("consolas", 30, bold=True)
        self.text_font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 18)

        profile = self.load_profile()
        self.difficulty = profile["difficulty"]
        self.scores = profile["scores"]
        self.mode = profile["last_mode"]

        self.scene = SCENE_MENU
        self.board = ["" for _ in range(9)]
        self.turn = "X"
        self.winner = ""
        self.win_line: tuple[int, int, int] | None = None
        self.game_over = False
        self.ai_next_tick = 0

        self.menu_buttons = [
            Button("Start Player vs AI", pygame.Rect(650, 220, 290, 56)),
            Button("Start 2 Players", pygame.Rect(650, 294, 290, 56)),
            Button("Difficulty: Hard", pygame.Rect(650, 368, 290, 56)),
            Button("Quit", pygame.Rect(650, 442, 290, 56)),
        ]

        self.play_buttons = [
            Button("New Round", pygame.Rect(650, 340, 290, 54)),
            Button("Reset Scores", pygame.Rect(650, 408, 290, 54)),
            Button("Main Menu", pygame.Rect(650, 476, 290, 54)),
            Button("Difficulty: Hard", pygame.Rect(650, 544, 290, 54)),
        ]
        self.sync_difficulty_labels()

    def load_profile(self) -> dict:
        if not PROFILE_PATH.exists():
            return dict(DEFAULTS)
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return dict(DEFAULTS)

        merged = dict(DEFAULTS)
        merged.update(data)

        diff = str(merged.get("difficulty", "Hard"))
        if diff not in ("Easy", "Hard"):
            diff = "Hard"

        scores = merged.get("scores", {})
        clean_scores = {
            "X": int(scores.get("X", 0)),
            "O": int(scores.get("O", 0)),
            "Draw": int(scores.get("Draw", 0)),
        }

        mode = str(merged.get("last_mode", "ai"))
        if mode not in ("ai", "pvp"):
            mode = "ai"

        return {"difficulty": diff, "scores": clean_scores, "last_mode": mode}

    def save_profile(self) -> None:
        payload = {
            "difficulty": self.difficulty,
            "scores": self.scores,
            "last_mode": self.mode,
        }
        PROFILE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def sync_difficulty_labels(self) -> None:
        self.menu_buttons[2].text = f"Difficulty: {self.difficulty}"
        self.play_buttons[3].text = f"Difficulty: {self.difficulty}"

    def toggle_difficulty(self) -> None:
        self.difficulty = "Easy" if self.difficulty == "Hard" else "Hard"
        self.sync_difficulty_labels()

    def reset_round(self, start_turn: str = "X") -> None:
        self.board = ["" for _ in range(9)]
        self.turn = start_turn
        self.winner = ""
        self.win_line = None
        self.game_over = False
        self.ai_next_tick = pygame.time.get_ticks() + 350

    def reset_scores(self) -> None:
        self.scores = {"X": 0, "O": 0, "Draw": 0}

    def board_index_from_mouse(self, pos: tuple[int, int]) -> int | None:
        px, py = pos
        if not (BOARD_X <= px < BOARD_X + BOARD_SIZE and BOARD_Y <= py < BOARD_Y + BOARD_SIZE):
            return None
        col = (px - BOARD_X) // CELL
        row = (py - BOARD_Y) // CELL
        return int(row * 3 + col)

    def check_winner(self, board: list[str]) -> tuple[str, tuple[int, int, int] | None]:
        lines = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]
        for a, b, c in lines:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a], (a, b, c)
        if "" not in board:
            return "Draw", None
        return "", None

    def place_move(self, index: int) -> bool:
        if index < 0 or index >= 9:
            return False
        if self.board[index] != "" or self.game_over:
            return False

        self.board[index] = self.turn
        result, line = self.check_winner(self.board)
        if result:
            self.game_over = True
            self.winner = result
            self.win_line = line
            if result in self.scores:
                self.scores[result] += 1
            return True

        self.turn = "O" if self.turn == "X" else "X"
        if self.mode == "ai" and self.turn == "O":
            self.ai_next_tick = pygame.time.get_ticks() + 340
        return True

    def available_moves(self, board: list[str]) -> list[int]:
        return [i for i, cell in enumerate(board) if cell == ""]

    def minimax(self, board: list[str], current: str) -> int:
        result, _ = self.check_winner(board)
        if result == "O":
            return 10
        if result == "X":
            return -10
        if result == "Draw":
            return 0

        if current == "O":
            best = -1000
            for move in self.available_moves(board):
                board[move] = "O"
                best = max(best, self.minimax(board, "X"))
                board[move] = ""
            return best

        best = 1000
        for move in self.available_moves(board):
            board[move] = "X"
            best = min(best, self.minimax(board, "O"))
            board[move] = ""
        return best

    def ai_choose_move(self) -> int | None:
        moves = self.available_moves(self.board)
        if not moves:
            return None

        if self.difficulty == "Easy":
            # Easy bot: mostly random with a small chance to play smart.
            if random.random() < 0.78:
                return random.choice(moves)

        best_score = -1000
        best_moves: list[int] = []
        for move in moves:
            self.board[move] = "O"
            score = self.minimax(self.board, "X")
            self.board[move] = ""
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return random.choice(best_moves) if best_moves else random.choice(moves)

    def handle_click_menu(self, pos: tuple[int, int]) -> None:
        if self.menu_buttons[0].hit(pos):
            self.mode = "ai"
            self.scene = SCENE_PLAY
            self.reset_round("X")
        elif self.menu_buttons[1].hit(pos):
            self.mode = "pvp"
            self.scene = SCENE_PLAY
            self.reset_round("X")
        elif self.menu_buttons[2].hit(pos):
            self.toggle_difficulty()
        elif self.menu_buttons[3].hit(pos):
            self.running = False

    def handle_click_play(self, pos: tuple[int, int]) -> None:
        if self.play_buttons[0].hit(pos):
            self.reset_round("X")
            return
        if self.play_buttons[1].hit(pos):
            self.reset_scores()
            return
        if self.play_buttons[2].hit(pos):
            self.scene = SCENE_MENU
            return
        if self.play_buttons[3].hit(pos):
            self.toggle_difficulty()
            return

        if self.game_over:
            return

        if self.mode == "ai" and self.turn == "O":
            return

        idx = self.board_index_from_mouse(pos)
        if idx is not None:
            self.place_move(idx)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.scene == SCENE_PLAY:
                        self.scene = SCENE_MENU
                    else:
                        self.running = False
                elif event.key == pygame.K_r and self.scene == SCENE_PLAY:
                    self.reset_round("X")
                elif event.key == pygame.K_m and self.scene == SCENE_PLAY:
                    self.scene = SCENE_MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scene == SCENE_MENU:
                    self.handle_click_menu(event.pos)
                else:
                    self.handle_click_play(event.pos)

    def update(self) -> None:
        if self.scene != SCENE_PLAY or self.mode != "ai":
            return
        if self.game_over or self.turn != "O":
            return

        now = pygame.time.get_ticks()
        if now < self.ai_next_tick:
            return

        move = self.ai_choose_move()
        if move is not None:
            self.place_move(move)

    def draw_gradient_bg(self) -> None:
        for y in range(SCREEN_H):
            t = y / max(1, SCREEN_H - 1)
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

    def draw_board(self) -> None:
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.screen, PANEL, board_rect, border_radius=12)
        pygame.draw.rect(self.screen, PANEL_BORDER, board_rect, 3, border_radius=12)

        for i in range(1, 3):
            x = BOARD_X + i * CELL
            y = BOARD_Y + i * CELL
            pygame.draw.line(self.screen, GRID, (x, BOARD_Y + 12), (x, BOARD_Y + BOARD_SIZE - 12), 4)
            pygame.draw.line(self.screen, GRID, (BOARD_X + 12, y), (BOARD_X + BOARD_SIZE - 12, y), 4)

        for idx, value in enumerate(self.board):
            if not value:
                continue
            row = idx // 3
            col = idx % 3
            cx = BOARD_X + col * CELL + CELL // 2
            cy = BOARD_Y + row * CELL + CELL // 2
            pad = 42
            if value == "X":
                x1, y1 = cx - CELL // 2 + pad, cy - CELL // 2 + pad
                x2, y2 = cx + CELL // 2 - pad, cy + CELL // 2 - pad
                pygame.draw.line(self.screen, X_COLOR, (x1, y1), (x2, y2), 12)
                pygame.draw.line(self.screen, X_COLOR, (x2, y1), (x1, y2), 12)
            else:
                radius = CELL // 2 - pad
                pygame.draw.circle(self.screen, O_COLOR, (cx, cy), radius, 12)

        if self.win_line:
            self.draw_win_line(self.win_line)

    def draw_win_line(self, line: tuple[int, int, int]) -> None:
        start_idx = line[0]
        end_idx = line[2]
        srow, scol = divmod(start_idx, 3)
        erow, ecol = divmod(end_idx, 3)
        sx = BOARD_X + scol * CELL + CELL // 2
        sy = BOARD_Y + srow * CELL + CELL // 2
        ex = BOARD_X + ecol * CELL + CELL // 2
        ey = BOARD_Y + erow * CELL + CELL // 2
        pygame.draw.line(self.screen, WIN, (sx, sy), (ex, ey), 10)

    def draw_right_panel(self) -> None:
        panel = pygame.Rect(620, 70, 340, 540)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=14)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=14)

        title = self.head_font.render("XO Control", True, TEXT)
        self.screen.blit(title, (650, 100))

        mode_label = "Player vs AI" if self.mode == "ai" else "2 Players"
        mode_text = self.text_font.render(f"Mode: {mode_label}", True, ACCENT)
        diff_text = self.text_font.render(f"Bot: {self.difficulty}", True, ACCENT)
        self.screen.blit(mode_text, (650, 144))
        self.screen.blit(diff_text, (650, 172))

        score_title = self.text_font.render("Scoreboard", True, TEXT)
        self.screen.blit(score_title, (650, 220))

        score_x = self.text_font.render(f"X: {self.scores['X']}", True, X_COLOR)
        score_o = self.text_font.render(f"O: {self.scores['O']}", True, O_COLOR)
        score_d = self.text_font.render(f"Draw: {self.scores['Draw']}", True, TEXT_MUTED)
        self.screen.blit(score_x, (650, 252))
        self.screen.blit(score_o, (760, 252))
        self.screen.blit(score_d, (870, 252))

        mouse = pygame.mouse.get_pos()
        for button in self.play_buttons:
            button.draw(self.screen, self.small_font, button.hit(mouse))

        if self.game_over:
            if self.winner == "Draw":
                msg = "Round Result: Draw"
                col = TEXT
            else:
                msg = f"Round Winner: {self.winner}"
                col = X_COLOR if self.winner == "X" else O_COLOR
        else:
            msg = f"Current Turn: {self.turn}"
            col = X_COLOR if self.turn == "X" else O_COLOR

        status = self.text_font.render(msg, True, col)
        self.screen.blit(status, (650, 304))

        hint = self.small_font.render("R: New Round | M: Main Menu | ESC: Back", True, TEXT_MUTED)
        self.screen.blit(hint, (650, 622))

    def draw_menu(self) -> None:
        self.draw_gradient_bg()

        title = self.title_font.render("XO GAME", True, TEXT)
        subtitle = self.text_font.render("Day 05 - 100 Days of Python Coding", True, ACCENT)
        desc = self.small_font.render("Play smart, beat the bot, and stack your score.", True, TEXT_MUTED)
        self.screen.blit(title, (640, 100))
        self.screen.blit(subtitle, (642, 164))
        self.screen.blit(desc, (642, 194))

        # Decorative board preview on the left side.
        preview = pygame.Rect(92, 120, 470, 470)
        pygame.draw.rect(self.screen, PANEL, preview, border_radius=14)
        pygame.draw.rect(self.screen, PANEL_BORDER, preview, 2, border_radius=14)
        for i in range(1, 3):
            pygame.draw.line(self.screen, GRID, (92 + i * 156, 138), (92 + i * 156, 572), 4)
            pygame.draw.line(self.screen, GRID, (110, 120 + i * 156), (544, 120 + i * 156), 4)

        pygame.draw.line(self.screen, X_COLOR, (160, 190), (248, 278), 12)
        pygame.draw.line(self.screen, X_COLOR, (248, 190), (160, 278), 12)
        pygame.draw.circle(self.screen, O_COLOR, (402, 350), 54, 12)

        mouse = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            button.draw(self.screen, self.small_font, button.hit(mouse))

    def draw_play(self) -> None:
        self.draw_gradient_bg()
        self.draw_board()
        self.draw_right_panel()

    def draw(self) -> None:
        if self.scene == SCENE_MENU:
            self.draw_menu()
        else:
            self.draw_play()
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        self.save_profile()
        pygame.quit()


if __name__ == "__main__":
    XOGame().run()