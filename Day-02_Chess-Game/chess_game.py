"""Day 02 Chess Game - pygame + Stockfish (Player vs 2000+ ELO)."""

from __future__ import annotations

import datetime
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import chess
import chess.engine
import chess.pgn
import pygame

# -----------------------------
# Configuration
# -----------------------------
ENGINE_PATH = Path(__file__).with_name("stockfish.exe")
SFX_DIR = Path(__file__).with_name("assets").joinpath("sfx")
ENGINE_ELO = 3000
ENGINE_TIME = 0.6

SCREEN_W = 1100
SCREEN_H = 720
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
PANEL_X = BOARD_SIZE + 20
PANEL_W = SCREEN_W - PANEL_X - 20

FPS = 1000
SCENE_MENU = "menu"
SCENE_GAME = "game"
SCENE_SETTINGS = "settings"

WHITE = (245, 240, 230)
BLACK = (70, 70, 70)
HIGHLIGHT = (120, 180, 255)
SELECTED = (255, 220, 120)
TEXT = (230, 230, 230)
TEXT_MUTED = (175, 175, 175)
PANEL_BG = (20, 24, 30)
BG = (15, 18, 22)
BOARD_LIGHT = (238, 234, 225)
BOARD_DARK = (102, 109, 126)
LAST_MOVE = (255, 226, 135)
COORD_TEXT = (78, 82, 92)

FONT_MAIN = "consolas"


PIECE_GLYPH = {
    chess.PAWN: ("P", "p", "♙", "♟"),
    chess.KNIGHT: ("N", "n", "♘", "♞"),
    chess.BISHOP: ("B", "b", "♗", "♝"),
    chess.ROOK: ("R", "r", "♖", "♜"),
    chess.QUEEN: ("Q", "q", "♕", "♛"),
    chess.KING: ("K", "k", "♔", "♚"),
}

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


@dataclass
class Clock:
    white_seconds: float
    black_seconds: float
    running: bool = True
    last_tick: float = time.time()

    def update(self, turn_white: bool) -> None:
        if not self.running:
            return
        now = time.time()
        delta = now - self.last_tick
        self.last_tick = now
        if turn_white:
            self.white_seconds = max(0, self.white_seconds - delta)
        else:
            self.black_seconds = max(0, self.black_seconds - delta)

    def reset(self, seconds: float) -> None:
        self.white_seconds = seconds
        self.black_seconds = seconds
        self.last_tick = time.time()
        self.running = True

    def format_time(self, seconds: float) -> str:
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"


@dataclass
class MoveRecord:
    san: str
    uci: str
    fen: str
    timestamp: str


class MoveHistory:
    def __init__(self) -> None:
        self.moves: list[MoveRecord] = []

    def add(self, board: chess.Board, move: chess.Move) -> None:
        san = board.san(move)
        uci = move.uci()
        fen = board.fen()
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.moves.append(MoveRecord(san, uci, fen, timestamp))

    def pop_last(self) -> Optional[MoveRecord]:
        if not self.moves:
            return None
        return self.moves.pop()

    def to_pgn(self, board: chess.Board) -> str:
        game = chess.pgn.Game()
        node = game
        temp_board = chess.Board()
        for rec in self.moves:
            move = chess.Move.from_uci(rec.uci)
            node = node.add_variation(move)
            temp_board.push(move)
        game.headers["Date"] = datetime.date.today().isoformat()
        game.headers["White"] = "Player"
        game.headers["Black"] = f"Stockfish {ENGINE_ELO}"
        return str(game)


class EngineManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.available = False

    def start(self) -> None:
        if not self.path.exists():
            self.available = False
            return
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(str(self.path))
            self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": ENGINE_ELO})
            self.available = True
        except Exception:
            self.available = False
            self.engine = None

    def stop(self) -> None:
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
        self.engine = None
        self.available = False

    def get_move(self, board: chess.Board, think_time: float) -> Optional[chess.Move]:
        if not self.engine:
            return None
        try:
            result = self.engine.play(board, chess.engine.Limit(time=think_time))
            return result.move
        except Exception:
            return None


class FallbackBot:
    """Small minimax fallback bot used when Stockfish is missing."""

    def __init__(self, depth: int = 2) -> None:
        self.depth = depth

    def choose_move(self, board: chess.Board) -> Optional[chess.Move]:
        legal = list(board.legal_moves)
        if not legal:
            return None
        best_score = -10_000_000
        best_moves: list[chess.Move] = []
        alpha = -10_000_000
        beta = 10_000_000
        for move in legal:
            board.push(move)
            score = -self._search(board, self.depth - 1, -beta, -alpha)
            board.pop()
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
            alpha = max(alpha, score)
        return random.choice(best_moves) if best_moves else legal[0]

    def _search(self, board: chess.Board, depth: int, alpha: int, beta: int) -> int:
        if depth <= 0 or board.is_game_over():
            return self._evaluate(board)
        best = -10_000_000
        for move in board.legal_moves:
            board.push(move)
            score = -self._search(board, depth - 1, -beta, -alpha)
            board.pop()
            if score > best:
                best = score
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best

    def _evaluate(self, board: chess.Board) -> int:
        if board.is_checkmate():
            return -1_000_000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        score = 0
        for piece_type, value in PIECE_VALUES.items():
            score += value * len(board.pieces(piece_type, board.turn))
            score -= value * len(board.pieces(piece_type, not board.turn))
        mobility = len(list(board.legal_moves))
        score += mobility * 2
        if board.is_check():
            score += 35
        return score


class TextureManager:
    """Loads piece PNG textures from the web-downloaded local assets folder."""

    def __init__(self, square_size: int) -> None:
        self.square_size = square_size
        self.texture_dir = Path(__file__).with_name("assets").joinpath("textures")
        self.cache: dict[tuple[int, bool], pygame.Surface] = {}
        self._load()

    def _load(self) -> None:
        mapping = {
            (chess.PAWN, chess.WHITE): "w_pawn.png",
            (chess.KNIGHT, chess.WHITE): "w_knight.png",
            (chess.BISHOP, chess.WHITE): "w_bishop.png",
            (chess.ROOK, chess.WHITE): "w_rook.png",
            (chess.QUEEN, chess.WHITE): "w_queen.png",
            (chess.KING, chess.WHITE): "w_king.png",
            (chess.PAWN, chess.BLACK): "b_pawn.png",
            (chess.KNIGHT, chess.BLACK): "b_knight.png",
            (chess.BISHOP, chess.BLACK): "b_bishop.png",
            (chess.ROOK, chess.BLACK): "b_rook.png",
            (chess.QUEEN, chess.BLACK): "b_queen.png",
            (chess.KING, chess.BLACK): "b_king.png",
        }
        for key, filename in mapping.items():
            path = self.texture_dir.joinpath(filename)
            if not path.exists():
                continue
            try:
                image = pygame.image.load(str(path)).convert_alpha()
                scaled = pygame.transform.smoothscale(
                    image, (self.square_size - 10, self.square_size - 10)
                )
                self.cache[key] = scaled
            except Exception:
                continue

    def get(self, piece: chess.Piece) -> Optional[pygame.Surface]:
        return self.cache.get((piece.piece_type, piece.color))


class SoundManager:
    """Event-based chess sound playback with graceful fallback when files are missing."""

    def __init__(self) -> None:
        self.available = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init()
            self.available = True
        except Exception:
            self.available = False
            return
        self._load_defaults()

    def _load_defaults(self) -> None:
        mapping = {
            "move": SFX_DIR / "move.ogg",
            "capture": SFX_DIR / "capture.ogg",
            "castle": SFX_DIR / "castle.ogg",
            "check": SFX_DIR / "check.ogg",
            "end": SFX_DIR / "end.ogg",
        }
        for key, path in mapping.items():
            if not path.exists():
                continue
            try:
                self.sounds[key] = pygame.mixer.Sound(str(path))
            except Exception:
                continue

    def play(self, key: str, volume: float = 0.7) -> None:
        if not self.available:
            return
        snd = self.sounds.get(key)
        if not snd:
            return
        try:
            snd.set_volume(max(0.0, min(1.0, volume)))
            snd.play()
        except Exception:
            pass


class ChessUI:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Day 02 - Chess Game")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont(FONT_MAIN, 32, bold=True)
        self.font_h2 = pygame.font.SysFont(FONT_MAIN, 24, bold=True)
        self.font_body = pygame.font.SysFont(FONT_MAIN, 20)
        self.font_small = pygame.font.SysFont(FONT_MAIN, 16)
        self.font_piece = pygame.font.SysFont("segoeuisymbol", 48)
        self.textures = TextureManager(SQUARE_SIZE)
        self.sound = SoundManager()

        self.board = chess.Board()
        self.history = MoveHistory()
        self.engine = EngineManager(ENGINE_PATH)
        self.engine.start()
        self.fallback_bot = FallbackBot(depth=2)

        self.flip = False
        self.selected: Optional[int] = None
        self.legal_moves: list[chess.Move] = []
        self.pending_promotion: Optional[chess.Move] = None
        self.last_move: Optional[chess.Move] = None

        self.human_color = chess.WHITE
        self.bot_color = chess.BLACK
        self.bot_thinking = False
        self.bot_move: Optional[chess.Move] = None
        self.last_bot_request = 0.0

        self.clock_state = Clock(600, 600)
        self.message = ""
        self.status_message = ""
        self.scene = SCENE_MENU
        self.time_controls = [300, 600, 900, 1800]
        self.time_index = 1
        self.ai_mode = "auto"
        self.menu_items = ["Start Match", "Settings", "Quit"]
        self.menu_index = 0
        self.settings_items = ["Player Color", "Time Control", "AI Mode", "Sound", "Sound Volume", "Back"]
        self.settings_index = 0
        self.sound_enabled = True
        self.sound_volume = 0.75
        self.game_end_sound_played = False
        self.time_over = False
        self.result_modal_text = ""
        self.running = True

    # -----------------------------
    # Helpers
    # -----------------------------
    def to_screen_square(self, square: int) -> tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        if self.flip:
            file = 7 - file
            rank = 7 - rank
        x = file * SQUARE_SIZE
        y = (7 - rank) * SQUARE_SIZE
        return x, y

    def screen_to_square(self, pos: tuple[int, int]) -> Optional[int]:
        x, y = pos
        if x >= BOARD_SIZE or y >= BOARD_SIZE:
            return None
        file = x // SQUARE_SIZE
        rank = 7 - (y // SQUARE_SIZE)
        if self.flip:
            file = 7 - file
            rank = 7 - rank
        return chess.square(file, rank)

    def piece_glyph(self, piece: chess.Piece) -> str:
        glyphs = PIECE_GLYPH[piece.piece_type]
        return glyphs[2] if piece.color == chess.WHITE else glyphs[3]

    def is_human_turn(self) -> bool:
        return self.board.turn == self.human_color

    def active_ai_mode(self) -> str:
        if self.ai_mode == "stockfish":
            return "stockfish"
        if self.ai_mode == "fallback":
            return "fallback"
        return "stockfish" if self.engine.available else "fallback"

    def apply_time_control(self) -> None:
        base = float(self.time_controls[self.time_index])
        self.clock_state.reset(base)

    def start_match(self) -> None:
        self.reset()
        self.scene = SCENE_GAME
        if self.board.turn == self.bot_color:
            self.request_bot_move()

    def reset(self) -> None:
        self.board.reset()
        self.history = MoveHistory()
        self.selected = None
        self.legal_moves = []
        self.pending_promotion = None
        self.last_move = None
        self.bot_thinking = False
        self.bot_move = None
        self.apply_time_control()
        self.message = ""
        self.status_message = ""
        self.game_end_sound_played = False
        self.time_over = False
        self.result_modal_text = ""

    def update_message(self) -> None:
        if self.board.is_checkmate():
            self.message = "Checkmate"
            self.result_modal_text = "You lose" if self.board.turn == self.human_color else "You won"
        elif self.board.is_stalemate():
            self.message = "Stalemate"
            self.result_modal_text = "Stalemate"
        elif self.board.is_check():
            self.message = "Check"
            self.result_modal_text = ""
        elif self.board.is_insufficient_material():
            self.message = "Draw (insufficient material)"
            self.result_modal_text = "Stalemate"
        else:
            self.message = ""
            self.result_modal_text = ""

    # -----------------------------
    # Input
    # -----------------------------
    def handle_menu_click(self, pos: tuple[int, int]) -> None:
        start_y = 260
        for idx, item in enumerate(self.menu_items):
            rect = pygame.Rect(SCREEN_W // 2 - 150, start_y + idx * 72, 300, 56)
            if not rect.collidepoint(pos):
                continue
            if item == "Start Match":
                self.start_match()
            elif item == "Settings":
                self.scene = SCENE_SETTINGS
            elif item == "Quit":
                self.running = False
            return

    def handle_settings_click(self, pos: tuple[int, int]) -> None:
        start_y = 220
        for idx, item in enumerate(self.settings_items):
            rect = pygame.Rect(SCREEN_W // 2 - 220, start_y + idx * 70, 440, 54)
            if not rect.collidepoint(pos):
                continue
            if item == "Player Color":
                self.human_color = chess.BLACK if self.human_color == chess.WHITE else chess.WHITE
                self.bot_color = not self.human_color
            elif item == "Time Control":
                self.time_index = (self.time_index + 1) % len(self.time_controls)
            elif item == "AI Mode":
                order = ["auto", "stockfish", "fallback"]
                self.ai_mode = order[(order.index(self.ai_mode) + 1) % len(order)]
            elif item == "Sound":
                self.sound_enabled = not self.sound_enabled
            elif item == "Sound Volume":
                self.sound_volume += 0.1
                if self.sound_volume > 1.0:
                    self.sound_volume = 0.2
            elif item == "Back":
                self.scene = SCENE_MENU
            return

    def handle_click(self, pos: tuple[int, int]) -> None:
        if self.scene == SCENE_MENU:
            self.handle_menu_click(pos)
            return
        if self.scene == SCENE_SETTINGS:
            self.handle_settings_click(pos)
            return
        if not self.is_human_turn() or self.board.is_game_over() or self.time_over:
            return
        square = self.screen_to_square(pos)
        if square is None:
            return
        if self.pending_promotion:
            self.handle_promotion_click(pos)
            return
        piece = self.board.piece_at(square)
        if self.selected is None:
            if piece and piece.color == self.human_color:
                self.selected = square
                self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
        else:
            move = self.find_move(self.selected, square)
            if move:
                if move.promotion:
                    self.pending_promotion = move
                else:
                    self.push_move(move)
                self.selected = None
                self.legal_moves = []
            else:
                if piece and piece.color == self.human_color:
                    self.selected = square
                    self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
                else:
                    self.selected = None
                    self.legal_moves = []

    def handle_promotion_click(self, pos: tuple[int, int]) -> None:
        if not self.pending_promotion:
            return
        options = self.promotion_options()
        for label, rect, piece_type in options:
            if rect.collidepoint(pos):
                move = chess.Move(
                    self.pending_promotion.from_square,
                    self.pending_promotion.to_square,
                    promotion=piece_type,
                )
                self.push_move(move)
                self.pending_promotion = None
                return

    def find_move(self, from_sq: int, to_sq: int) -> Optional[chess.Move]:
        for move in self.legal_moves:
            if move.to_square == to_sq:
                return move
        return None

    def _play_event_sound(self, board_before: chess.Board, move: chess.Move) -> None:
        if not self.sound_enabled:
            return
        is_capture = board_before.is_capture(move)
        is_castle = board_before.is_castling(move)
        board_after = board_before.copy(stack=False)
        board_after.push(move)

        if board_after.is_checkmate() or board_after.is_stalemate():
            self.sound.play("end", self.sound_volume)
            return
        if board_after.is_check():
            self.sound.play("check", self.sound_volume)
            return
        if is_castle:
            self.sound.play("castle", self.sound_volume)
            return
        if is_capture:
            self.sound.play("capture", self.sound_volume)
            return
        self.sound.play("move", self.sound_volume)

    def push_move(self, move: chess.Move) -> None:
        board_before = self.board.copy(stack=False)
        self.last_move = move
        self.history.add(self.board, move)
        self.board.push(move)
        self._play_event_sound(board_before, move)
        self.update_message()
        if self.board.turn == self.bot_color and not self.board.is_game_over():
            self.request_bot_move()

    # -----------------------------
    # Bot
    # -----------------------------
    def request_bot_move(self) -> None:
        if self.bot_thinking:
            return
        if self.board.turn != self.bot_color or self.board.is_game_over():
            return
        self.bot_thinking = True
        self.last_bot_request = time.time()

    def update_bot(self) -> None:
        if not self.bot_thinking:
            return

        mode = self.active_ai_mode()
        move = None
        if mode == "stockfish":
            if time.time() - self.last_bot_request < ENGINE_TIME:
                return
            move = self.engine.get_move(self.board, ENGINE_TIME)
            if move is None:
                self.status_message = "Stockfish not ready, switched to fallback bot."
                self.ai_mode = "fallback"
                mode = "fallback"
        if mode == "fallback":
            move = self.fallback_bot.choose_move(self.board)
        if move is None:
            self.bot_thinking = False
            return
        board_before = self.board.copy(stack=False)
        self.last_move = move
        self.history.add(self.board, move)
        self.board.push(move)
        self._play_event_sound(board_before, move)
        self.update_message()
        self.bot_thinking = False

    # -----------------------------
    # Save/Load
    # -----------------------------
    def save_pgn(self) -> None:
        pgn_text = self.history.to_pgn(self.board)
        out = Path(__file__).with_name("game.pgn")
        out.write_text(pgn_text, encoding="utf-8")

    def save_fen(self) -> None:
        out = Path(__file__).with_name("position.fen")
        out.write_text(self.board.fen(), encoding="utf-8")

    # -----------------------------
    # Draw
    # -----------------------------
    def draw_board(self) -> None:
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, rank)
                x, y = self.to_screen_square(square)
                color = BOARD_LIGHT if (file + rank) % 2 == 0 else BOARD_DARK
                pygame.draw.rect(self.screen, color, pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))

        if self.last_move is not None:
            for sq in (self.last_move.from_square, self.last_move.to_square):
                x, y = self.to_screen_square(sq)
                overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                overlay.fill((LAST_MOVE[0], LAST_MOVE[1], LAST_MOVE[2], 90))
                self.screen.blit(overlay, (x, y))

        for move in self.legal_moves:
            x, y = self.to_screen_square(move.to_square)
            pygame.draw.rect(self.screen, HIGHLIGHT, pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE), 3)

        if self.selected is not None:
            x, y = self.to_screen_square(self.selected)
            pygame.draw.rect(self.screen, SELECTED, pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE), 3)

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue
            x, y = self.to_screen_square(square)
            texture = self.textures.get(piece)
            if texture is not None:
                rect = texture.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                self.screen.blit(texture, rect)
            else:
                glyph = self.piece_glyph(piece)
                surf = self.font_piece.render(glyph, True, (10, 10, 10) if piece.color else (255, 255, 255))
                rect = surf.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2 + 2))
                self.screen.blit(surf, rect)

        for f in range(8):
            square = chess.square(f, 0)
            x, y = self.to_screen_square(square)
            label = chr(ord("a") + f if not self.flip else ord("h") - f)
            self.screen.blit(self.font_small.render(label, True, COORD_TEXT), (x + 4, BOARD_SIZE - 20))
        for r in range(8):
            square = chess.square(0, r)
            x, y = self.to_screen_square(square)
            label = str(r + 1 if self.flip else 8 - r)
            self.screen.blit(self.font_small.render(label, True, COORD_TEXT), (4, y + 4))

    def draw_panel(self) -> None:
        pygame.draw.rect(self.screen, PANEL_BG, pygame.Rect(BOARD_SIZE, 0, SCREEN_W - BOARD_SIZE, SCREEN_H))
        title = self.font_title.render("Chess Game - Day 02", True, TEXT)
        self.screen.blit(title, (PANEL_X, 20))

        mode = self.active_ai_mode()
        engine_status = "AI: Stockfish" if mode == "stockfish" else "AI: Fallback"
        engine_color = (120, 220, 140) if mode == "stockfish" else (255, 170, 110)
        status = self.font_body.render(engine_status, True, engine_color)
        self.screen.blit(status, (PANEL_X, 60))

        info = self.font_small.render(
            f"ELO target: {ENGINE_ELO}  Think: {ENGINE_TIME:.2f}s  Mode={self.ai_mode}",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(info, (PANEL_X, 86))

        clock_w = self.clock_state.format_time(self.clock_state.white_seconds)
        clock_b = self.clock_state.format_time(self.clock_state.black_seconds)
        self.screen.blit(self.font_body.render(f"White: {clock_w}", True, TEXT), (PANEL_X, 120))
        self.screen.blit(self.font_body.render(f"Black: {clock_b}", True, TEXT), (PANEL_X, 150))

        if self.message:
            self.screen.blit(self.font_body.render(self.message, True, (255, 200, 120)), (PANEL_X, 190))
        if self.status_message:
            self.screen.blit(self.font_small.render(self.status_message, True, (130, 180, 255)), (PANEL_X, 218))

        self.draw_history()
        self.draw_controls()
        if self.pending_promotion:
            self.draw_promotion_overlay()

    def draw_history(self) -> None:
        header = self.font_body.render("Moves", True, TEXT)
        self.screen.blit(header, (PANEL_X, 240))
        y = 270
        for i, rec in enumerate(self.history.moves[-20:], start=max(1, len(self.history.moves) - 19)):
            text = f"{i:02d}. {rec.san}"
            surf = self.font_small.render(text, True, TEXT_MUTED)
            self.screen.blit(surf, (PANEL_X, y))
            y += 18

    def draw_controls(self) -> None:
        lines = [
            "Controls:",
            "Click to move",
            "U = Undo",
            "F = Flip board",
            "R = Reset",
            "P = Save PGN",
            "N = Save FEN",
            "Esc = Quit",
        ]
        y = 640
        for line in lines:
            surf = self.font_small.render(line, True, TEXT_MUTED)
            self.screen.blit(surf, (PANEL_X, y))
            y += 18

    def draw_vertical_gradient(self, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
        for y in range(SCREEN_H):
            t = y / max(1, SCREEN_H - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

    def draw_menu(self) -> None:
        self.draw_vertical_gradient((10, 16, 28), (20, 32, 54))
        title = self.font_title.render("Chess Game Business Edition", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 100)))
        subtitle = self.font_body.render("Main Menu", True, TEXT_MUTED)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 140)))

        start_y = 260
        for idx, item in enumerate(self.menu_items):
            rect = pygame.Rect(SCREEN_W // 2 - 150, start_y + idx * 72, 300, 56)
            shadow = rect.move(0, 4)
            pygame.draw.rect(self.screen, (15, 24, 40), shadow, border_radius=12)
            color = (68, 104, 156) if idx == self.menu_index else (36, 46, 64)
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            pygame.draw.rect(self.screen, (120, 136, 165), rect, 2, border_radius=12)
            text = self.font_body.render(item, True, TEXT)
            self.screen.blit(text, text.get_rect(center=rect.center))

        engine_text = "Stockfish detected" if self.engine.available else "Stockfish missing: fallback bot active"
        engine_color = (120, 220, 140) if self.engine.available else (255, 170, 110)
        self.screen.blit(self.font_small.render(engine_text, True, engine_color), (SCREEN_W // 2 - 155, 520))
        self.screen.blit(self.font_small.render("Enter = select, Esc = quit", True, TEXT_MUTED), (SCREEN_W // 2 - 100, 548))

    def draw_settings(self) -> None:
        self.draw_vertical_gradient((12, 22, 38), (16, 30, 50))
        title = self.font_h2.render("Settings", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 120)))

        values = {
            "Player Color": "White" if self.human_color == chess.WHITE else "Black",
            "Time Control": f"{self.time_controls[self.time_index] // 60} min",
            "AI Mode": self.ai_mode.upper(),
            "Sound": "ON" if self.sound_enabled else "OFF",
            "Sound Volume": f"{int(self.sound_volume * 100)}%",
            "Back": "",
        }

        start_y = 220
        for idx, item in enumerate(self.settings_items):
            rect = pygame.Rect(SCREEN_W // 2 - 220, start_y + idx * 70, 440, 54)
            shadow = rect.move(0, 4)
            pygame.draw.rect(self.screen, (16, 25, 43), shadow, border_radius=10)
            color = (62, 92, 140) if idx == self.settings_index else (35, 45, 62)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (120, 140, 170), rect, 2, border_radius=10)
            text = f"{item}: {values[item]}" if values[item] else item
            self.screen.blit(self.font_body.render(text, True, TEXT), (rect.x + 16, rect.y + 15))

        self.screen.blit(self.font_small.render("Enter to change, Esc to menu", True, TEXT_MUTED), (SCREEN_W // 2 - 110, 560))

    def promotion_options(self) -> list[tuple[str, pygame.Rect, int]]:
        base_x = BOARD_SIZE // 2 - 2 * SQUARE_SIZE
        base_y = BOARD_SIZE // 2 - SQUARE_SIZE // 2
        options = [
            ("Q", pygame.Rect(base_x, base_y, SQUARE_SIZE, SQUARE_SIZE), chess.QUEEN),
            ("R", pygame.Rect(base_x + SQUARE_SIZE, base_y, SQUARE_SIZE, SQUARE_SIZE), chess.ROOK),
            ("B", pygame.Rect(base_x + 2 * SQUARE_SIZE, base_y, SQUARE_SIZE, SQUARE_SIZE), chess.BISHOP),
            ("N", pygame.Rect(base_x + 3 * SQUARE_SIZE, base_y, SQUARE_SIZE, SQUARE_SIZE), chess.KNIGHT),
        ]
        return options

    def draw_promotion_overlay(self) -> None:
        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        for label, rect, piece_type in self.promotion_options():
            pygame.draw.rect(self.screen, (240, 240, 240), rect)
            pygame.draw.rect(self.screen, (20, 20, 20), rect, 2)
            piece = chess.Piece(piece_type, self.human_color)
            texture = self.textures.get(piece)
            if texture is not None:
                self.screen.blit(texture, texture.get_rect(center=rect.center))
            else:
                glyph = self.piece_glyph(piece)
                surf = self.font_piece.render(glyph, True, (20, 20, 20))
                self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_result_modal(self) -> None:
        if not self.result_modal_text:
            return
        if not (self.board.is_game_over() or self.time_over):
            return
        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(BOARD_SIZE // 2 - 130, BOARD_SIZE // 2 - 90, 260, 180)
        pygame.draw.rect(self.screen, (247, 247, 247), box, border_radius=12)
        pygame.draw.rect(self.screen, (35, 45, 62), box, 3, border_radius=12)

        title = self.font_h2.render(self.result_modal_text, True, (30, 35, 45))
        self.screen.blit(title, title.get_rect(center=(box.centerx, box.y + 62)))
        hint = self.font_small.render("Press R to rematch or Esc for menu", True, (76, 84, 96))
        self.screen.blit(hint, hint.get_rect(center=(box.centerx, box.y + 120)))

    # -----------------------------
    # Main loop
    # -----------------------------
    def handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.scene == SCENE_GAME or self.scene == SCENE_SETTINGS:
                self.scene = SCENE_MENU
            else:
                self.running = False
            return

        if self.scene == SCENE_MENU:
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                item = self.menu_items[self.menu_index]
                if item == "Start Match":
                    self.start_match()
                elif item == "Settings":
                    self.scene = SCENE_SETTINGS
                elif item == "Quit":
                    self.running = False
            return

        if self.scene == SCENE_SETTINGS:
            if key in (pygame.K_UP, pygame.K_w):
                self.settings_index = (self.settings_index - 1) % len(self.settings_items)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.settings_index = (self.settings_index + 1) % len(self.settings_items)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                item = self.settings_items[self.settings_index]
                if item == "Player Color":
                    self.human_color = chess.BLACK if self.human_color == chess.WHITE else chess.WHITE
                    self.bot_color = not self.human_color
                elif item == "Time Control":
                    self.time_index = (self.time_index + 1) % len(self.time_controls)
                elif item == "AI Mode":
                    order = ["auto", "stockfish", "fallback"]
                    self.ai_mode = order[(order.index(self.ai_mode) + 1) % len(order)]
                elif item == "Sound":
                    self.sound_enabled = not self.sound_enabled
                elif item == "Sound Volume":
                    self.sound_volume += 0.1
                    if self.sound_volume > 1.0:
                        self.sound_volume = 0.2
                elif item == "Back":
                    self.scene = SCENE_MENU
            return

        if key == pygame.K_f:
            self.flip = not self.flip
        elif key == pygame.K_r:
            self.start_match()
        elif key == pygame.K_u:
            self.undo_last_full_move()
        elif key == pygame.K_p:
            self.save_pgn()
        elif key == pygame.K_n:
            self.save_fen()

    def undo_last_full_move(self) -> None:
        if len(self.history.moves) < 1:
            return
        if self.board.move_stack:
            self.board.pop()
            self.history.pop_last()
        if self.board.move_stack:
            self.board.pop()
            self.history.pop_last()
        self.last_move = self.board.move_stack[-1] if self.board.move_stack else None
        self.update_message()

    def tick(self) -> None:
        if self.scene != SCENE_GAME:
            return
        if self.time_over:
            return
        self.clock_state.update(self.board.turn == chess.WHITE)
        if self.clock_state.white_seconds <= 0 or self.clock_state.black_seconds <= 0:
            self.message = "Time over"
            self.time_over = True
            human_seconds = self.clock_state.white_seconds if self.human_color == chess.WHITE else self.clock_state.black_seconds
            self.result_modal_text = "You lose" if human_seconds <= 0 else "You won"
            if not self.game_end_sound_played and self.sound_enabled:
                self.sound.play("end", self.sound_volume)
                self.game_end_sound_played = True
            return
        if not self.is_human_turn():
            self.update_bot()

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            if self.scene == SCENE_GAME and not self.board.is_game_over():
                self.tick()

            if self.scene == SCENE_MENU:
                self.draw_menu()
            elif self.scene == SCENE_SETTINGS:
                self.draw_settings()
            else:
                self.screen.fill(BG)
                self.draw_board()
                self.draw_panel()
                self.draw_result_modal()
            pygame.display.flip()
            self.clock.tick(FPS)

        self.engine.stop()
        pygame.quit()


# -----------------------------
# Piece-square tables
# These are not used by Stockfish, but kept for future evaluation overlays.
# -----------------------------
PIECE_SQUARE_TABLES = {
    "pawn_mid": [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        50,
        50,
        50,
        50,
        50,
        50,
        50,
        50,
        10,
        10,
        20,
        30,
        30,
        20,
        10,
        10,
        5,
        5,
        10,
        25,
        25,
        10,
        5,
        5,
        0,
        0,
        0,
        20,
        20,
        0,
        0,
        0,
        5,
        -5,
        -10,
        0,
        0,
        -10,
        -5,
        5,
        5,
        10,
        10,
        -20,
        -20,
        10,
        10,
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    "pawn_end": [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        80,
        80,
        80,
        80,
        80,
        80,
        80,
        80,
        40,
        40,
        40,
        40,
        40,
        40,
        40,
        40,
        20,
        20,
        20,
        20,
        20,
        20,
        20,
        20,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    "knight_mid": [
        -50,
        -40,
        -30,
        -30,
        -30,
        -30,
        -40,
        -50,
        -40,
        -20,
        0,
        0,
        0,
        0,
        -20,
        -40,
        -30,
        0,
        10,
        15,
        15,
        10,
        0,
        -30,
        -30,
        5,
        15,
        20,
        20,
        15,
        5,
        -30,
        -30,
        0,
        15,
        20,
        20,
        15,
        0,
        -30,
        -30,
        5,
        10,
        15,
        15,
        10,
        5,
        -30,
        -40,
        -20,
        0,
        5,
        5,
        0,
        -20,
        -40,
        -50,
        -40,
        -30,
        -30,
        -30,
        -30,
        -40,
        -50,
    ],
    "knight_end": [
        -40,
        -30,
        -20,
        -20,
        -20,
        -20,
        -30,
        -40,
        -30,
        -10,
        0,
        0,
        0,
        0,
        -10,
        -30,
        -20,
        0,
        10,
        10,
        10,
        10,
        0,
        -20,
        -20,
        5,
        15,
        20,
        20,
        15,
        5,
        -20,
        -20,
        0,
        15,
        20,
        20,
        15,
        0,
        -20,
        -20,
        5,
        10,
        15,
        15,
        10,
        5,
        -20,
        -30,
        -10,
        0,
        5,
        5,
        0,
        -10,
        -30,
        -40,
        -30,
        -20,
        -20,
        -20,
        -20,
        -30,
        -40,
    ],
    "bishop_mid": [
        -20,
        -10,
        -10,
        -10,
        -10,
        -10,
        -10,
        -20,
        -10,
        5,
        0,
        0,
        0,
        0,
        5,
        -10,
        -10,
        10,
        10,
        10,
        10,
        10,
        10,
        -10,
        -10,
        0,
        10,
        10,
        10,
        10,
        0,
        -10,
        -10,
        5,
        5,
        10,
        10,
        5,
        5,
        -10,
        -10,
        0,
        5,
        10,
        10,
        5,
        0,
        -10,
        -10,
        0,
        0,
        0,
        0,
        0,
        0,
        -10,
        -20,
        -10,
        -10,
        -10,
        -10,
        -10,
        -10,
        -20,
    ],
    "bishop_end": [
        -10,
        -5,
        -5,
        -5,
        -5,
        -5,
        -5,
        -10,
        -5,
        5,
        0,
        0,
        0,
        0,
        5,
        -5,
        -5,
        10,
        10,
        10,
        10,
        10,
        10,
        -5,
        -5,
        0,
        10,
        10,
        10,
        10,
        0,
        -5,
        -5,
        5,
        5,
        10,
        10,
        5,
        5,
        -5,
        -5,
        0,
        5,
        10,
        10,
        5,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -10,
        -5,
        -5,
        -5,
        -5,
        -5,
        -5,
        -10,
    ],
    "rook_mid": [
        0,
        0,
        5,
        10,
        10,
        5,
        0,
        0,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        5,
        10,
        10,
        10,
        10,
        10,
        10,
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    "rook_end": [
        5,
        10,
        10,
        10,
        10,
        10,
        10,
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        0,
        0,
        5,
        10,
        10,
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    "queen_mid": [
        -20,
        -10,
        -10,
        -5,
        -5,
        -10,
        -10,
        -20,
        -10,
        0,
        0,
        0,
        0,
        0,
        0,
        -10,
        -10,
        0,
        5,
        5,
        5,
        5,
        0,
        -10,
        -5,
        0,
        5,
        5,
        5,
        5,
        0,
        -5,
        0,
        0,
        5,
        5,
        5,
        5,
        0,
        -5,
        -10,
        5,
        5,
        5,
        5,
        5,
        0,
        -10,
        -10,
        0,
        5,
        0,
        0,
        0,
        0,
        -10,
        -20,
        -10,
        -10,
        -5,
        -5,
        -10,
        -10,
        -20,
    ],
    "queen_end": [
        -10,
        -5,
        -5,
        0,
        0,
        -5,
        -5,
        -10,
        -5,
        0,
        0,
        0,
        0,
        0,
        0,
        -5,
        -5,
        0,
        5,
        5,
        5,
        5,
        0,
        -5,
        0,
        0,
        5,
        5,
        5,
        5,
        0,
        0,
        0,
        0,
        5,
        5,
        5,
        5,
        0,
        0,
        -5,
        5,
        5,
        5,
        5,
        5,
        0,
        -5,
        -5,
        0,
        5,
        0,
        0,
        0,
        0,
        -5,
        -10,
        -5,
        -5,
        0,
        0,
        -5,
        -5,
        -10,
    ],
    "king_mid": [
        -30,
        -40,
        -40,
        -50,
        -50,
        -40,
        -40,
        -30,
        -30,
        -40,
        -40,
        -50,
        -50,
        -40,
        -40,
        -30,
        -30,
        -40,
        -40,
        -50,
        -50,
        -40,
        -40,
        -30,
        -30,
        -40,
        -40,
        -50,
        -50,
        -40,
        -40,
        -30,
        -20,
        -30,
        -30,
        -40,
        -40,
        -30,
        -30,
        -20,
        -10,
        -20,
        -20,
        -20,
        -20,
        -20,
        -20,
        -10,
        20,
        20,
        0,
        0,
        0,
        0,
        20,
        20,
        20,
        30,
        10,
        0,
        0,
        10,
        30,
        20,
    ],
    "king_end": [
        -50,
        -40,
        -30,
        -20,
        -20,
        -30,
        -40,
        -50,
        -30,
        -20,
        -10,
        0,
        0,
        -10,
        -20,
        -30,
        -30,
        -10,
        20,
        30,
        30,
        20,
        -10,
        -30,
        -30,
        -10,
        30,
        40,
        40,
        30,
        -10,
        -30,
        -30,
        -10,
        30,
        40,
        40,
        30,
        -10,
        -30,
        -30,
        -10,
        20,
        30,
        30,
        20,
        -10,
        -30,
        -30,
        -30,
        0,
        0,
        0,
        0,
        -30,
        -30,
        -50,
        -30,
        -30,
        -30,
        -30,
        -30,
        -30,
        -50,
    ],
}


def main() -> None:
    game = ChessUI()
    game.run()


if __name__ == "__main__":
    main()
