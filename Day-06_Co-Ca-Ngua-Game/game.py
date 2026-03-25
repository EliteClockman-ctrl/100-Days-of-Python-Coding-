"""Day 06 - Horse Race Ludo (business edition) with pygame.

Rules implemented (common variant):
- Roll a die and move one horse by dice value.
- Need a 6 to bring a horse out from yard.
- Landing on opponent (non-safe square) captures and sends it back to yard.
- Roll 6 grants an extra turn.
- Move into home lane after one full lap; exact roll required to reach center.
- First player to bring all 4 horses to center wins.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import pygame  # pyre-ignore[21]


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TEXTURES = ASSETS / "textures"
AUDIO = ASSETS / "audio"
PROFILE = ROOT / "profile.json"

SCREEN_W = 1280
SCREEN_H = 780
FPS = 120

SCENE_MENU = "menu"
SCENE_PLAY = "play"

GRID_SIZE = 15
CELL = 44
BOARD_X = 38
BOARD_Y = 58
BOARD_PX = GRID_SIZE * CELL

FINAL_STEP = 58
SAFE_INDICES: set[int] = {0, 8, 13, 21, 26, 34, 39, 47}

BG_TOP = (20, 26, 43)
BG_BOTTOM = (10, 14, 26)
PANEL = (20, 25, 38)
PANEL_BORDER = (78, 105, 160)
TEXT = (236, 243, 255)
MUTED = (170, 184, 212)
ACCENT = (102, 190, 255)
GOLD = (255, 204, 120)

COLOR_RGB = {
    "red": (234, 99, 99),
    "green": (109, 214, 126),
    "yellow": (255, 214, 108),
    "blue": (112, 161, 255),
}
COLOR_LABEL = {
    "red": "Red",
    "green": "Green",
    "yellow": "Yellow",
    "blue": "Blue",
}

PLAYERS: list[str] = ["red", "green", "yellow", "blue"]
START_INDEX: dict[str, int] = {"red": 0, "green": 13, "yellow": 26, "blue": 39}

OUTER_PATH = [
    (6, 1),
    (6, 2),
    (6, 3),
    (6, 4),
    (6, 5),
    (5, 6),
    (4, 6),
    (3, 6),
    (2, 6),
    (1, 6),
    (0, 6),
    (0, 7),
    (0, 8),
    (1, 8),
    (2, 8),
    (3, 8),
    (4, 8),
    (5, 8),
    (6, 9),
    (6, 10),
    (6, 11),
    (6, 12),
    (6, 13),
    (6, 14),
    (7, 14),
    (8, 14),
    (8, 13),
    (8, 12),
    (8, 11),
    (8, 10),
    (8, 9),
    (9, 8),
    (10, 8),
    (11, 8),
    (12, 8),
    (13, 8),
    (14, 8),
    (14, 7),
    (14, 6),
    (13, 6),
    (12, 6),
    (11, 6),
    (10, 6),
    (9, 6),
    (8, 5),
    (8, 4),
    (8, 3),
    (8, 2),
    (8, 1),
    (8, 0),
    (7, 0),
    (6, 0),
]

HOME_PATH = {
    "red": [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],
    "green": [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)],
    "yellow": [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)],
    "blue": [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)],
}

YARD_CELLS = {
    "red": [(1, 1), (3, 1), (1, 3), (3, 3)],
    "green": [(11, 1), (13, 1), (11, 3), (13, 3)],
    "yellow": [(11, 11), (13, 11), (11, 13), (13, 13)],
    "blue": [(1, 11), (3, 11), (1, 13), (3, 13)],
}

DEFAULTS = {
    "human_color": "red",
    "sound": True,
}


@dataclass
class Button:
    text: str
    rect: pygame.Rect

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, active: bool = False) -> None:
        bg = (46, 66, 103) if not active else (66, 98, 154)
        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, PANEL_BORDER, self.rect, 2, border_radius=12)
        label = font.render(self.text, True, TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def hit(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class SoundManager:
    def __init__(self) -> None:
        self.available = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}

    def load(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            self.available = False
            return

        files = {
            "click": AUDIO / "click.wav",
            "move": AUDIO / "move.wav",
            "capture": AUDIO / "capture.wav",
        }
        count: int = 0
        for key, path in files.items():
            if not path.exists():
                continue
            try:
                self.sounds[key] = pygame.mixer.Sound(str(path))
                count += 1
            except Exception:
                pass

        self.available = count > 0
        if self.available:
            self.sounds.get("click") and self.sounds["click"].set_volume(0.4)
            self.sounds.get("move") and self.sounds["move"].set_volume(0.55)
            self.sounds.get("capture") and self.sounds["capture"].set_volume(0.75)

    def play(self, name: str, enabled: bool = True) -> None:
        if not enabled or not self.available:
            return
        if name in self.sounds:
            self.sounds[name].play()


class CaNguaGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Day 06 - Horse Race Business Edition")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True

        self.title_font = pygame.font.SysFont("segoe ui", 50, bold=True)
        self.head_font = pygame.font.SysFont("segoe ui", 28, bold=True)
        self.text_font = pygame.font.SysFont("segoe ui", 22)
        self.small_font = pygame.font.SysFont("segoe ui", 18)

        profile = self.load_profile()
        self.human_color = profile["human_color"]
        self.sound_enabled = profile["sound"]

        self.sounds = SoundManager()
        self.sounds.load()

        self.bg_image = self.load_bg_image()
        self.horse_texture = self.load_horse_texture()
        self.dice_texture = self.load_dice_texture()

        self.scene = SCENE_MENU
        self.current_idx = 0
        self.dice_value: int | None = None
        self.display_dice_value: int | None = None
        self.roll_anim_end_ms = 0
        self.movable_tokens: list[int] = []
        self.message = ""
        self.winner_color = ""
        self.event_feed: list[str] = []

        self.tokens: dict[str, list[int]] = {color: [-1, -1, -1, -1] for color in PLAYERS}

        self.ai_action_time = 0

        self.menu_buttons = [
            Button("Start Match", pygame.Rect(830, 250, 360, 62)),
            Button("Human Color: Red", pygame.Rect(830, 330, 360, 62)),
            Button("Sound: On", pygame.Rect(830, 410, 360, 62)),
            Button("Quit", pygame.Rect(830, 490, 360, 62)),
        ]

        self.play_buttons = [
            Button("Roll Dice", pygame.Rect(830, 270, 360, 58)),
            Button("End Turn", pygame.Rect(830, 340, 360, 58)),
            Button("New Match", pygame.Rect(830, 410, 360, 58)),
            Button("Main Menu", pygame.Rect(830, 480, 360, 58)),
        ]
        self.sync_menu_labels()

    def load_profile(self) -> dict:
        if not PROFILE.exists():
            return dict(DEFAULTS)
        try:
            data = json.loads(PROFILE.read_text(encoding="utf-8"))
        except Exception:
            return dict(DEFAULTS)

        merged = dict(DEFAULTS)
        merged.update(data)

        if merged.get("human_color") not in PLAYERS:
            merged["human_color"] = "red"
        merged["sound"] = bool(merged.get("sound", True))
        return merged

    def save_profile(self) -> None:
        data = {
            "human_color": self.human_color,
            "sound": self.sound_enabled,
        }
        PROFILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_bg_image(self) -> pygame.Surface | None:
        path = TEXTURES / "bg.jpg"
        if not path.exists():
            return None
        try:
            img = pygame.image.load(str(path)).convert()
            return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
        except Exception:
            return None

    def load_horse_texture(self) -> pygame.Surface | None:
        for name in ["horse_realistic.png", "horse_base.png", "horse_knight_base.png"]:
            path = TEXTURES / name
            if not path.exists():
                continue
            try:
                img = pygame.image.load(str(path)).convert_alpha()
                return pygame.transform.smoothscale(img, (30, 30))
            except Exception:
                continue
        return None

    def load_dice_texture(self) -> pygame.Surface | None:
        for name in ["dice_realistic.png", "dice_icon.png"]:
            path = TEXTURES / name
            if not path.exists():
                continue
            try:
                img = pygame.image.load(str(path)).convert_alpha()
                return pygame.transform.smoothscale(img, (34, 34))
            except Exception:
                continue
        return None

    def sync_menu_labels(self) -> None:
        self.menu_buttons[1].text = f"Human Color: {COLOR_LABEL[self.human_color]}"
        self.menu_buttons[2].text = f"Sound: {'On' if self.sound_enabled else 'Off'}"

    def push_event(self, text: str) -> None:
        self.event_feed.insert(0, text)
        while len(self.event_feed) > 6:
            self.event_feed.pop()

    def truncate_text(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        out: list[str] = []
        for i, ch in enumerate(text):
            if i >= limit:
                break
            out.append(ch)
        return "".join(out)

    def reset_game(self) -> None:
        self.tokens = {color: [-1, -1, -1, -1] for color in PLAYERS}
        self.current_idx = 0
        self.dice_value = None
        self.display_dice_value = None
        self.roll_anim_end_ms = 0
        self.movable_tokens = []
        self.message = "New match started. Roll the dice to move."
        self.winner_color = ""
        self.event_feed = ["Match started"]
        self.ai_action_time = pygame.time.get_ticks() + 400

    def current_color(self) -> str:
        return PLAYERS[self.current_idx]

    def is_human_turn(self) -> bool:
        return self.current_color() == self.human_color

    def step_to_grid(self, color: str, token_idx: int) -> tuple[int, int]:
        step = self.tokens[color][token_idx]
        if step < 0:
            return YARD_CELLS[color][token_idx]
        if step <= 51:
            idx = (START_INDEX[color] + step) % 52
            return OUTER_PATH[idx]
        if step <= 57:
            return HOME_PATH[color][step - 52]
        return (7, 7)

    def grid_to_px(self, gx: int, gy: int) -> tuple[int, int]:
        return (BOARD_X + gx * CELL + CELL // 2, BOARD_Y + gy * CELL + CELL // 2)

    def can_move_token(self, color: str, token_idx: int, dice: int) -> bool:
        step = self.tokens[color][token_idx]
        if step == FINAL_STEP:
            return False
        if step == -1:
            return dice == 6
        return step + dice <= FINAL_STEP

    def compute_movable_tokens(self, color: str, dice: int) -> list[int]:
        return [i for i in range(4) if self.can_move_token(color, i, dice)]

    def path_index_of(self, color: str, token_idx: int) -> int | None:
        step = self.tokens[color][token_idx]
        if step < 0 or step > 51:
            return None
        return (START_INDEX[color] + step) % 52

    def will_capture(self, color: str, token_idx: int, dice: int) -> bool:
        step = self.tokens[color][token_idx]
        if step == -1:
            new_step = 0
        else:
            new_step = step + dice

        if new_step < 0 or new_step > 51:
            return False

        target_idx = (START_INDEX[color] + new_step) % 52
        if target_idx in SAFE_INDICES:
            return False

        for other in PLAYERS:
            if other == color:
                continue
            for j in range(4):
                other_idx = self.path_index_of(other, j)
                if other_idx is not None and other_idx == target_idx:
                    return True
        return False

    def move_token(self, color: str, token_idx: int, dice: int) -> bool:
        captured = False
        step = self.tokens[color][token_idx]
        if step == -1:
            self.tokens[color][token_idx] = 0
        else:
            self.tokens[color][token_idx] += dice

        new_step = self.tokens[color][token_idx]

        if 0 <= new_step <= 51:
            target_idx = (START_INDEX[color] + new_step) % 52
            if target_idx not in SAFE_INDICES:
                for other in PLAYERS:
                    if other == color:
                        continue
                    for j in range(4):
                        other_idx = self.path_index_of(other, j)
                        if other_idx is not None and other_idx == target_idx:
                            self.tokens[other][j] = -1
                            captured = True

        if all(step == FINAL_STEP for step in self.tokens[color]):
            self.winner_color = color
            self.message = f"{COLOR_LABEL[color]} wins the match!"
            self.push_event(self.message)

        return captured

    def end_turn(self, extra_turn: bool = False) -> None:
        if self.winner_color:
            self.dice_value = None
            self.movable_tokens = []
            return

        if extra_turn:
            self.dice_value = None
            self.display_dice_value = None
            self.movable_tokens = []
            self.message = f"{COLOR_LABEL[self.current_color()]} gets extra turn."
            self.push_event(self.message)
            return

        self.current_idx = (self.current_idx + 1) % len(PLAYERS)
        self.dice_value = None
        self.display_dice_value = None
        self.movable_tokens = []
        self.message = f"Turn: {COLOR_LABEL[self.current_color()]}"
        self.push_event(self.message)

        if not self.is_human_turn():
            self.ai_action_time = pygame.time.get_ticks() + 500

    def roll_dice(self) -> None:
        if self.dice_value is not None:
            return

        color = self.current_color()
        dice = random.randint(1, 6)
        self.dice_value = dice
        self.display_dice_value = dice
        self.roll_anim_end_ms = pygame.time.get_ticks() + 500
        self.movable_tokens = self.compute_movable_tokens(color, dice)
        self.message = f"{COLOR_LABEL[color]} rolled {dice}."
        self.push_event(self.message)

        if not self.movable_tokens:
            self.message += " No valid move."
            self.push_event(self.message)
            self.end_turn(False)

    def choose_ai_token(self) -> int | None:
        color = self.current_color()
        dice = self.dice_value
        if not self.movable_tokens or dice is None:
            return None

        scored: list[tuple[int, int]] = []
        for token_idx in self.movable_tokens:
            step = self.tokens[color][token_idx]
            new_step = 0 if step == -1 else step + dice
            score = new_step * 3

            if self.will_capture(color, token_idx, dice):
                score += 140
            if new_step == FINAL_STEP:
                score += 180
            if step == -1:
                score += 35
            if 0 <= new_step <= 51:
                board_idx = (START_INDEX[color] + new_step) % 52
                if board_idx in SAFE_INDICES:
                    score += 20

            score += random.randint(0, 6)
            scored.append((score, token_idx))

        scored.sort(reverse=True)
        return scored[0][1] if scored else None

    def handle_menu_click(self, pos: tuple[int, int]) -> None:
        if self.menu_buttons[0].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            self.scene = SCENE_PLAY
            self.reset_game()
        elif self.menu_buttons[1].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            idx = PLAYERS.index(self.human_color)
            self.human_color = PLAYERS[(idx + 1) % len(PLAYERS)]
            self.sync_menu_labels()
        elif self.menu_buttons[2].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            self.sound_enabled = not self.sound_enabled
            self.sync_menu_labels()
        elif self.menu_buttons[3].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            self.running = False

    def token_under_cursor(self, pos: tuple[int, int]) -> int | None:
        color = self.current_color()
        for token_idx in self.movable_tokens:
            gx, gy = self.step_to_grid(color, token_idx)
            cx, cy = self.grid_to_px(gx, gy)
            if (pos[0] - cx) ** 2 + (pos[1] - cy) ** 2 <= 22**2:
                return token_idx
        return None

    def handle_play_click(self, pos: tuple[int, int]) -> None:
        if self.play_buttons[0].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            if self.is_human_turn() and not self.winner_color:
                self.roll_dice()
            return
        if self.play_buttons[1].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            if self.is_human_turn() and self.dice_value is not None:
                self.end_turn(False)
            return
        if self.play_buttons[2].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            self.reset_game()
            return
        if self.play_buttons[3].hit(pos):
            self.sounds.play("click", self.sound_enabled)
            self.scene = SCENE_MENU
            return

        if self.winner_color:
            return
        if not self.is_human_turn():
            return
        if self.dice_value is None or not self.movable_tokens:
            return

        dice = self.dice_value
        if dice is None:
            return

        token_idx = self.token_under_cursor(pos)
        if token_idx is None:
            return

        captured = self.move_token(self.current_color(), token_idx, dice)
        self.sounds.play("move", self.sound_enabled)
        self.push_event(f"{COLOR_LABEL[self.current_color()]} moved horse #{token_idx + 1}.")
        if captured:
            self.sounds.play("capture", self.sound_enabled)
            self.push_event(f"{COLOR_LABEL[self.current_color()]} captured an opponent horse.")

        extra = dice == 6 or captured
        self.end_turn(extra)

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
                elif event.key == pygame.K_SPACE and self.scene == SCENE_PLAY and self.is_human_turn():
                    self.roll_dice()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scene == SCENE_MENU:
                    self.handle_menu_click(event.pos)
                else:
                    self.handle_play_click(event.pos)

    def update_ai(self) -> None:
        if self.scene != SCENE_PLAY:
            return
        if self.winner_color:
            return
        if self.is_human_turn():
            return

        now = pygame.time.get_ticks()
        if now < self.ai_action_time:
            return

        if self.dice_value is None:
            self.roll_dice()
            self.ai_action_time = now + 500
            return

        if not self.movable_tokens:
            self.end_turn(False)
            self.ai_action_time = now + 420
            return

        token_idx = self.choose_ai_token()
        if token_idx is None:
            self.end_turn(False)
            self.ai_action_time = now + 420
            return

        dice = self.dice_value
        if dice is None:
            self.end_turn(False)
            self.ai_action_time = now + 420
            return

        captured = self.move_token(self.current_color(), token_idx, dice)
        self.sounds.play("move", self.sound_enabled)
        self.push_event(f"{COLOR_LABEL[self.current_color()]} moved horse #{token_idx + 1}.")
        if captured:
            self.sounds.play("capture", self.sound_enabled)
            self.push_event(f"{COLOR_LABEL[self.current_color()]} captured an opponent horse.")

        extra = dice == 6 or captured
        self.end_turn(extra)
        self.ai_action_time = now + 560

    def draw_gradient(self) -> None:
        for y in range(SCREEN_H):
            t = y / max(1, SCREEN_H - 1)
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

    def draw_background(self) -> None:
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((8, 12, 20, 170))
            self.screen.blit(overlay, (0, 0))
        else:
            self.draw_gradient()

    def draw_board_base(self) -> None:
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_PX, BOARD_PX)
        pygame.draw.rect(self.screen, (245, 247, 251), board_rect, border_radius=16)
        pygame.draw.rect(self.screen, PANEL_BORDER, board_rect, 3, border_radius=16)

        # Draw corners / yards
        corner_cells = {
            "red": pygame.Rect(BOARD_X, BOARD_Y, CELL * 6, CELL * 6),
            "green": pygame.Rect(BOARD_X + CELL * 9, BOARD_Y, CELL * 6, CELL * 6),
            "yellow": pygame.Rect(BOARD_X + CELL * 9, BOARD_Y + CELL * 9, CELL * 6, CELL * 6),
            "blue": pygame.Rect(BOARD_X, BOARD_Y + CELL * 9, CELL * 6, CELL * 6),
        }
        for color, rect in corner_cells.items():
            fill = COLOR_RGB[color]
            shade = (min(255, fill[0] + 15), min(255, fill[1] + 15), min(255, fill[2] + 15))
            pygame.draw.rect(self.screen, shade, rect)

        # Draw home lanes
        for color in PLAYERS:
            c = COLOR_RGB[color]
            for gx, gy in HOME_PATH[color]:
                rect = pygame.Rect(BOARD_X + gx * CELL, BOARD_Y + gy * CELL, CELL, CELL)
                pygame.draw.rect(self.screen, c, rect)

        # Draw outer path
        for i, (gx, gy) in enumerate(OUTER_PATH):
            rect = pygame.Rect(BOARD_X + gx * CELL, BOARD_Y + gy * CELL, CELL, CELL)
            color = (245, 248, 253)
            if i in SAFE_INDICES:
                color = (218, 231, 255)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (182, 194, 218), rect, 1)

        # Center zone
        center_rect = pygame.Rect(BOARD_X + 6 * CELL, BOARD_Y + 6 * CELL, CELL * 3, CELL * 3)
        pygame.draw.rect(self.screen, (230, 236, 248), center_rect)
        pygame.draw.polygon(
            self.screen,
            COLOR_RGB["red"],
            [
                (center_rect.centerx, center_rect.top + 6),
                (center_rect.left + 6, center_rect.centery),
                (center_rect.centerx, center_rect.centery),
            ],
        )
        pygame.draw.polygon(
            self.screen,
            COLOR_RGB["green"],
            [
                (center_rect.left + 6, center_rect.centery),
                (center_rect.centerx, center_rect.bottom - 6),
                (center_rect.centerx, center_rect.centery),
            ],
        )
        pygame.draw.polygon(
            self.screen,
            COLOR_RGB["yellow"],
            [
                (center_rect.centerx, center_rect.bottom - 6),
                (center_rect.right - 6, center_rect.centery),
                (center_rect.centerx, center_rect.centery),
            ],
        )
        pygame.draw.polygon(
            self.screen,
            COLOR_RGB["blue"],
            [
                (center_rect.right - 6, center_rect.centery),
                (center_rect.centerx, center_rect.top + 6),
                (center_rect.centerx, center_rect.centery),
            ],
        )

        # Yard circles
        for color in PLAYERS:
            for gx, gy in YARD_CELLS[color]:
                cx, cy = self.grid_to_px(gx, gy)
                pygame.draw.circle(self.screen, (250, 252, 255), (cx, cy), 18)
                pygame.draw.circle(self.screen, COLOR_RGB[color], (cx, cy), 18, 3)

    def draw_piece(self, color: str, token_idx: int, highlighted: bool = False) -> None:
        gx, gy = self.step_to_grid(color, token_idx)
        cx, cy = self.grid_to_px(gx, gy)

        ring = 22 if highlighted else 19
        pygame.draw.circle(self.screen, (30, 36, 58), (cx, cy), ring)
        pygame.draw.circle(self.screen, COLOR_RGB[color], (cx, cy), ring, 4)

        if self.horse_texture:
            icon = self.horse_texture.copy()
            tint = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
            tint.fill((*COLOR_RGB[color], 90))
            icon.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.screen.blit(icon, icon.get_rect(center=(cx, cy)))
        else:
            label = self.small_font.render("H", True, TEXT)
            self.screen.blit(label, label.get_rect(center=(cx, cy)))

    def draw_all_pieces(self) -> None:
        highlights: set[int] = set()
        if self.scene == SCENE_PLAY and self.is_human_turn() and self.dice_value is not None:
            highlights = set(self.movable_tokens)

        for color in PLAYERS:
            for token_idx in range(4):
                self.draw_piece(color, token_idx, highlighted=(color == self.current_color() and token_idx in highlights))

    def draw_panel(self) -> None:
        panel = pygame.Rect(770, 58, 472, 660)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=16)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=16)

        title = self.head_font.render("Horse Race Dashboard", True, TEXT)
        self.screen.blit(title, (804, 94))

        turn = self.current_color()
        turn_text = self.text_font.render(f"Turn: {COLOR_LABEL[turn]}", True, COLOR_RGB[turn])
        self.screen.blit(turn_text, (804, 138))

        human_text = self.small_font.render(f"Human: {COLOR_LABEL[self.human_color]} | Space: Roll", True, MUTED)
        self.screen.blit(human_text, (804, 170))

        if self.display_dice_value is None:
            dice_text = self.text_font.render("Dice: -", True, ACCENT)
        else:
            dice_text = self.text_font.render(f"Dice: {self.display_dice_value}", True, GOLD)
        self.screen.blit(dice_text, (804, 212))

        if self.dice_texture:
            self.screen.blit(self.dice_texture, (950, 205))

        msg_text = self.truncate_text(self.message, 64)
        msg = self.small_font.render(msg_text, True, MUTED)
        self.screen.blit(msg, (804, 250))

        # Status per player
        y = 300
        for color in PLAYERS:
            finished = sum(1 for s in self.tokens[color] if s == FINAL_STEP)
            yard = sum(1 for s in self.tokens[color] if s < 0)
            txt = self.small_font.render(
                f"{COLOR_LABEL[color]}  finish:{finished}/4  yard:{yard}",
                True,
                COLOR_RGB[color],
            )
            self.screen.blit(txt, (804, y))
            y += 34

        mouse = pygame.mouse.get_pos()
        for button in self.play_buttons:
            active = button.hit(mouse)
            button.draw(self.screen, self.small_font, active)

        tips = [
            "Rules (common):",
            "- Roll 6 to bring horse out.",
            "- Capture opponent on non-safe path.",
            "- Roll 6 gives extra turn.",
            "- Exact roll needed to enter center.",
        ]
        yy = 582
        for line in tips:
            surf = self.small_font.render(line, True, MUTED)
            self.screen.blit(surf, (804, yy))
            yy += 24

        feed_box = pygame.Rect(790, 560, 432, 90)
        pygame.draw.rect(self.screen, (28, 36, 54), feed_box, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_BORDER, feed_box, 1, border_radius=10)
        feed_title = self.small_font.render("Event Feed", True, ACCENT)
        self.screen.blit(feed_title, (802, 566))
        fy = 590
        max_feed = 2 if len(self.event_feed) >= 2 else len(self.event_feed)
        for idx in range(max_feed):
            item = self.event_feed[idx]
            row = self.small_font.render(f"- {self.truncate_text(item, 52)}", True, MUTED)
            self.screen.blit(row, (802, fy))
            fy += 22

        if self.winner_color:
            overlay = pygame.Surface((BOARD_PX, BOARD_PX), pygame.SRCALPHA)
            overlay.fill((6, 12, 20, 180))
            self.screen.blit(overlay, (BOARD_X, BOARD_Y))
            winner = self.title_font.render(f"{COLOR_LABEL[self.winner_color]} Wins!", True, COLOR_RGB[self.winner_color])
            self.screen.blit(winner, winner.get_rect(center=(BOARD_X + BOARD_PX // 2, BOARD_Y + BOARD_PX // 2 - 10)))
            tip = self.small_font.render("Click New Match to play again", True, TEXT)
            self.screen.blit(tip, tip.get_rect(center=(BOARD_X + BOARD_PX // 2, BOARD_Y + BOARD_PX // 2 + 44)))

    def draw_menu(self) -> None:
        self.draw_background()

        title = self.title_font.render("HORSE RACE LUDO", True, TEXT)
        subtitle = self.text_font.render("Business Edition - Day 06", True, ACCENT)
        desc = self.small_font.render("Rule-based movement, capture, home lane, AI opponents", True, MUTED)
        self.screen.blit(title, (800, 130))
        self.screen.blit(subtitle, (804, 198))
        self.screen.blit(desc, (804, 232))

        # Board preview
        self.draw_board_base()
        self.draw_all_pieces()

        mouse = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            button.draw(self.screen, self.text_font, button.hit(mouse))

    def draw_play(self) -> None:
        self.draw_background()
        self.draw_board_base()
        self.draw_all_pieces()
        self.draw_panel()

    def draw(self) -> None:
        if self.scene == SCENE_MENU:
            self.draw_menu()
        else:
            self.draw_play()
        pygame.display.flip()

    def update_roll_animation(self) -> None:
        if self.roll_anim_end_ms <= 0:
            return
        now = pygame.time.get_ticks()
        if now < self.roll_anim_end_ms:
            self.display_dice_value = random.randint(1, 6)
        else:
            self.roll_anim_end_ms = 0
            self.display_dice_value = self.dice_value

    def update(self) -> None:
        self.update_roll_animation()
        self.update_ai()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        self.save_profile()
        pygame.quit()


if __name__ == "__main__":
    CaNguaGame().run()
