"""Day 1 Snake Game - polished pygame edition with menu and language support."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import pygame

CELL_SIZE = 24
GRID_W = 30
GRID_H = 20
HUD_H = 84
W = GRID_W * CELL_SIZE
H = GRID_H * CELL_SIZE + HUD_H
PROFILE_PATH = Path(__file__).with_name("profile.json")
FEATURES_REPORT_PATH = Path(__file__).with_name("features_report.json")
SFX_DIR = Path(__file__).with_name("assets").joinpath("sfx")
LEADERBOARD_MAX = 10

STATE_MENU = "menu"
STATE_MODE = "mode"
STATE_SETTINGS = "settings"
STATE_PLAY = "play"
STATE_PAUSE = "pause"
STATE_OVER = "over"
STATE_STATS = "stats"
STATE_FEATURES = "features"

LANG_EN = "en"
LANG_VI = "vi"

DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

FPS_MENU = 60
DEFAULT_SPEED = 11

THEMES = {
    "default": {
        "bg": (19, 21, 28),
        "panel": (30, 34, 43),
        "grid": (44, 50, 64),
        "text": (235, 238, 248),
        "muted": (156, 164, 189),
        "accent": (112, 174, 255),
        "snake": (88, 224, 130),
        "head": (154, 255, 190),
        "food": (255, 104, 112),
        "special": (95, 199, 255),
        "danger": (255, 109, 109),
        "ok": (119, 231, 159),
        "gold": (249, 206, 98),
    },
    "sunset": {
        "bg": (35, 20, 22),
        "panel": (60, 36, 38),
        "grid": (86, 52, 54),
        "text": (250, 236, 220),
        "muted": (217, 182, 167),
        "accent": (255, 157, 102),
        "snake": (255, 192, 113),
        "head": (255, 225, 160),
        "food": (255, 103, 103),
        "special": (126, 213, 255),
        "danger": (255, 115, 115),
        "ok": (142, 235, 165),
        "gold": (255, 213, 122),
    },
}

MODE_RULES = {
    "classic": {"wrap": False, "obstacles": False, "timer": 0, "portals": False},
    "zen": {"wrap": True, "obstacles": False, "timer": 0, "portals": False},
    "walls": {"wrap": False, "obstacles": True, "timer": 0, "portals": False},
    "timed": {"wrap": False, "obstacles": False, "timer": 90, "portals": False},
    "portal": {"wrap": False, "obstacles": False, "timer": 0, "portals": True},
}

TR = {
    "en": {
        "title": "SNAKE GAME",
        "subtitle": "Day 1 - Main Menu Edition",
        "menu_start": "Start",
        "menu_mode": "Mode",
        "menu_settings": "Settings",
        "menu_stats": "Statistics",
        "menu_features": "Features",
        "menu_exit": "Exit",
        "mode_title": "Select Mode",
        "mode_hint": "Enter select | Esc back",
        "settings_title": "Settings",
        "settings_lang": "Language",
        "settings_theme": "Theme",
        "settings_speed": "Base speed",
        "settings_grid": "Show grid",
        "settings_sound": "Sound",
        "settings_volume": "Volume",
        "settings_back": "Back",
        "stats_title": "Statistics",
        "stats_best": "Best score: {v}",
        "stats_games": "Total games: {v}",
        "stats_food": "Total food: {v}",
        "stats_time": "Total time: {v}s",
        "stats_streak": "Best streak: {v}",
        "stats_features": "Features done: {v}",
        "stats_back": "Esc to return",
        "features_title": "Feature Tracker",
        "features_hint": "Up/Down select | Left/Right page | Enter cycle status | E export | Esc back",
        "features_page": "Page {page}/{total}",
        "status_ready": "ready",
        "status_in_progress": "in_progress",
        "status_done": "done",
        "hud_mode": "Mode: {mode}",
        "hud_score": "Score: {score}  Best: {best}  Level: {level}",
        "hud_timer": "Time: {t}s",
        "pause": "Paused",
        "pause_hint": "P/Esc continue | R restart | M menu",
        "over": "Game Over",
        "over_score": "Score: {s}",
        "over_hint": "R restart | M menu",
        "on": "On",
        "off": "Off",
    },
    "vi": {
        "title": "SNAKE GAME",
        "subtitle": "Day 1 - Co Main Menu",
        "menu_start": "Bat dau",
        "menu_mode": "Che do",
        "menu_settings": "Cai dat",
        "menu_stats": "Thong ke",
        "menu_features": "Tinh nang",
        "menu_exit": "Thoat",
        "mode_title": "Chon che do",
        "mode_hint": "Enter chon | Esc quay lai",
        "settings_title": "Cai dat",
        "settings_lang": "Ngon ngu",
        "settings_theme": "Giao dien",
        "settings_speed": "Toc do goc",
        "settings_grid": "Hien luoi",
        "settings_sound": "Am thanh",
        "settings_volume": "Am luong",
        "settings_back": "Quay lai",
        "stats_title": "Thong ke",
        "stats_best": "Diem cao nhat: {v}",
        "stats_games": "Tong tran: {v}",
        "stats_food": "Tong moi an: {v}",
        "stats_time": "Tong thoi gian: {v}s",
        "stats_streak": "Chuoi tot nhat: {v}",
        "stats_features": "So tinh nang da xong: {v}",
        "stats_back": "Nhan Esc de quay lai",
        "features_title": "Theo doi tinh nang",
        "features_hint": "Len/Xuong chon | Trai/Phai trang | Enter doi status | E export | Esc quay lai",
        "features_page": "Trang {page}/{total}",
        "status_ready": "san sang",
        "status_in_progress": "dang lam",
        "status_done": "hoan tat",
        "hud_mode": "Che do: {mode}",
        "hud_score": "Diem: {score}  Cao nhat: {best}  Cap: {level}",
        "hud_timer": "Thoi gian: {t}s",
        "pause": "Tam dung",
        "pause_hint": "P/Esc tiep tuc | R choi lai | M menu",
        "over": "Thua roi",
        "over_score": "Diem: {s}",
        "over_hint": "R choi lai | M menu",
        "on": "Bat",
        "off": "Tat",
    },
}


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class SnakeApp:
    def __init__(self) -> None:
        pygame.init()
        self.audio_ready = False
        try:
            pygame.mixer.init()
            self.audio_ready = True
        except Exception:
            self.audio_ready = False
        pygame.display.set_caption("Day-01 Snake Game")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("consolas", 36, bold=True)
        self.font_menu = pygame.font.SysFont("consolas", 25, bold=True)
        self.font_body = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 15)

        self.profile = self.load_profile()
        self.lang = self.profile.get("language", LANG_VI)
        self.state = STATE_MENU
        self.running = True
        self.menu_idx = 0
        self.mode_idx = 0
        self.settings_idx = 0
        self.feature_idx = 0
        self.feature_page_size = 12
        self.menu_items = ["menu_start", "menu_mode", "menu_settings", "menu_stats", "menu_features", "menu_exit"]
        self.mode_items = list(MODE_RULES.keys())
        self.settings_items = [
            "settings_lang",
            "settings_theme",
            "settings_speed",
            "settings_grid",
            "settings_sound",
            "settings_volume",
            "settings_back",
        ]

        self.snake: list[Point] = []
        self.dir = DIR_RIGHT
        self.pending_dir = DIR_RIGHT
        self.food = Point(4, 4)
        self.special_food: Point | None = None
        self.special_until = 0.0
        self.obstacles: set[Point] = set()
        self.portals: tuple[Point, Point] | None = None
        self.score = 0
        self.level = 1
        self.last_tick = time.time()
        self.session_start = time.time()
        self.time_left = 0.0
        self.move_interval = 1.0 / max(6, int(self.profile.get("speed", DEFAULT_SPEED)))
        self.best_in_run = 0

        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.load_sounds()
        self.reset_round()

    def load_sounds(self) -> None:
        if not self.audio_ready:
            return
        sound_files = {
            "eat": SFX_DIR / "food.wav",
            "special": SFX_DIR / "food.wav",
            "game_over": SFX_DIR / "death.wav",
        }
        for key, path in sound_files.items():
            try:
                if path.exists():
                    snd = pygame.mixer.Sound(str(path))
                    snd.set_volume(float(self.profile.get("volume", 70)) / 100.0)
                    self.sounds[key] = snd
            except Exception:
                continue

    def play_sound(self, name: str) -> None:
        if not self.profile.get("sound", True):
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.set_volume(float(self.profile.get("volume", 70)) / 100.0)
                snd.play()
            except Exception:
                pass

    def theme(self) -> dict:
        return THEMES.get(self.profile.get("theme", "default"), THEMES["default"])

    def tr(self, key: str, **kwargs) -> str:
        return TR[self.lang].get(key, key).format(**kwargs)

    def load_profile(self) -> dict:
        if PROFILE_PATH.exists():
            try:
                return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "language": LANG_VI,
            "theme": "default",
            "speed": DEFAULT_SPEED,
            "grid": True,
            "sound": True,
            "volume": 70,
            "mode": "classic",
            "best_score": 0,
            "total_games": 0,
            "total_food": 0,
            "total_time": 0,
            "best_streak": 0,
            "leaderboard": [],
            "feature_statuses": {},
        }

    def save_profile(self) -> None:
        PROFILE_PATH.write_text(json.dumps(self.profile, indent=2), encoding="utf-8")

    def reset_round(self) -> None:
        cx, cy = GRID_W // 2, GRID_H // 2
        self.snake = [Point(cx, cy), Point(cx - 1, cy), Point(cx - 2, cy)]
        self.dir = DIR_RIGHT
        self.pending_dir = DIR_RIGHT
        self.score = 0
        self.level = 1
        self.best_in_run = 0
        self.session_start = time.time()
        self.last_tick = time.time()
        self.food = self.find_free_cell()
        self.special_food = None
        self.special_until = 0.0
        self.obstacles = set()
        self.portals = None

        mode = self.profile.get("mode", "classic")
        rules = MODE_RULES[mode]
        self.time_left = float(rules["timer"])
        self.move_interval = 1.0 / max(6, int(self.profile.get("speed", DEFAULT_SPEED)))
        if rules["obstacles"]:
            for _ in range(14):
                self.obstacles.add(self.find_free_cell())
        if rules["portals"]:
            a = self.find_free_cell()
            b = self.find_free_cell(excluded={a})
            self.portals = (a, b)

    def find_free_cell(self, excluded: set[Point] | None = None) -> Point:
        excluded = excluded or set()
        used = set(self.snake) | self.obstacles | excluded
        used.add(self.food)
        if self.special_food:
            used.add(self.special_food)
        while True:
            p = Point(random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
            if p not in used:
                return p

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            fps = FPS_MENU if self.state != STATE_PLAY else 60
            self.clock.tick(fps)
        pygame.quit()

    def handle_events(self) -> None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
                return
            if e.type != pygame.KEYDOWN:
                continue
            if self.state == STATE_MENU:
                self.handle_menu_input(e.key)
            elif self.state == STATE_MODE:
                self.handle_mode_input(e.key)
            elif self.state == STATE_SETTINGS:
                self.handle_settings_input(e.key)
            elif self.state == STATE_PLAY:
                self.handle_play_input(e.key)
            elif self.state == STATE_PAUSE:
                self.handle_pause_input(e.key)
            elif self.state == STATE_OVER:
                self.handle_over_input(e.key)
            elif self.state == STATE_STATS:
                if e.key in (pygame.K_ESCAPE, pygame.K_m):
                    self.state = STATE_MENU
            elif self.state == STATE_FEATURES:
                self.handle_features_input(e.key)

    def handle_menu_input(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.menu_idx = (self.menu_idx - 1) % len(self.menu_items)
            self.play_sound("menu")
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
            self.play_sound("menu")
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            item = self.menu_items[self.menu_idx]
            self.play_sound("menu")
            if item == "menu_start":
                self.reset_round()
                self.state = STATE_PLAY
            elif item == "menu_mode":
                self.state = STATE_MODE
            elif item == "menu_settings":
                self.state = STATE_SETTINGS
            elif item == "menu_stats":
                self.state = STATE_STATS
            elif item == "menu_features":
                self.state = STATE_FEATURES
            elif item == "menu_exit":
                self.running = False
        elif key == pygame.K_ESCAPE:
            self.running = False

    def handle_mode_input(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.mode_idx = (self.mode_idx - 1) % len(self.mode_items)
            self.play_sound("menu")
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.mode_idx = (self.mode_idx + 1) % len(self.mode_items)
            self.play_sound("menu")
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self.profile["mode"] = self.mode_items[self.mode_idx]
            self.save_profile()
            self.play_sound("menu")
            self.state = STATE_MENU
        elif key == pygame.K_ESCAPE:
            self.state = STATE_MENU

    def handle_settings_input(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.settings_idx = (self.settings_idx - 1) % len(self.settings_items)
            self.play_sound("menu")
            return
        if key in (pygame.K_DOWN, pygame.K_s):
            self.settings_idx = (self.settings_idx + 1) % len(self.settings_items)
            self.play_sound("menu")
            return
        field = self.settings_items[self.settings_idx]
        if field == "settings_back" and key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.state = STATE_MENU
            return
        if field == "settings_lang" and key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
            self.lang = LANG_EN if self.lang == LANG_VI else LANG_VI
            self.profile["language"] = self.lang
            self.save_profile()
        elif field == "settings_theme" and key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
            names = list(THEMES.keys())
            cur = self.profile.get("theme", "default")
            idx = names.index(cur) if cur in names else 0
            self.profile["theme"] = names[(idx + 1) % len(names)]
            self.save_profile()
        elif field == "settings_speed" and key in (pygame.K_LEFT, pygame.K_RIGHT):
            delta = -1 if key == pygame.K_LEFT else 1
            self.profile["speed"] = max(6, min(24, int(self.profile.get("speed", DEFAULT_SPEED)) + delta))
            self.save_profile()
        elif field == "settings_grid" and key in (pygame.K_RETURN, pygame.K_SPACE):
            self.profile["grid"] = not bool(self.profile.get("grid", True))
            self.save_profile()
        elif field == "settings_sound" and key in (pygame.K_RETURN, pygame.K_SPACE):
            self.profile["sound"] = not bool(self.profile.get("sound", True))
            self.save_profile()
        elif field == "settings_volume" and key in (pygame.K_LEFT, pygame.K_RIGHT):
            delta = -5 if key == pygame.K_LEFT else 5
            self.profile["volume"] = max(0, min(100, int(self.profile.get("volume", 70)) + delta))
            self.save_profile()
        elif key == pygame.K_ESCAPE:
            self.state = STATE_MENU

    def handle_play_input(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.set_direction(DIR_UP)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.set_direction(DIR_DOWN)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.set_direction(DIR_LEFT)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.set_direction(DIR_RIGHT)
        elif key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = STATE_PAUSE

    def handle_pause_input(self, key: int) -> None:
        if key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = STATE_PLAY
        elif key == pygame.K_r:
            self.reset_round()
            self.state = STATE_PLAY
        elif key == pygame.K_m:
            self.state = STATE_MENU

    def handle_over_input(self, key: int) -> None:
        if key == pygame.K_r:
            self.reset_round()
            self.state = STATE_PLAY
        elif key in (pygame.K_m, pygame.K_ESCAPE):
            self.state = STATE_MENU

    def total_feature_pages(self) -> int:
        return max(1, (len(FEATURE_CATALOG) + self.feature_page_size - 1) // self.feature_page_size)

    def selected_feature_abs_index(self) -> int:
        return self.feature_idx

    def feature_status(self, feature_id: int, default_status: str) -> str:
        statuses = self.profile.setdefault("feature_statuses", {})
        return statuses.get(str(feature_id), default_status)

    def set_feature_status(self, feature_id: int, status: str) -> None:
        statuses = self.profile.setdefault("feature_statuses", {})
        statuses[str(feature_id)] = status
        self.save_profile()

    def cycle_feature_status(self, feature_id: int, default_status: str) -> None:
        order = ["ready", "in_progress", "done"]
        cur = self.feature_status(feature_id, default_status)
        idx = order.index(cur) if cur in order else 0
        self.set_feature_status(feature_id, order[(idx + 1) % len(order)])

    def export_features_report(self) -> None:
        exported = []
        done = 0
        for feature in FEATURE_CATALOG:
            status = self.feature_status(feature["id"], feature.get("status", "ready"))
            if status == "done":
                done += 1
            exported.append(
                {
                    "id": feature["id"],
                    "name": feature["name"],
                    "description": feature["description"],
                    "status": status,
                }
            )
        payload = {
            "generated_at": int(time.time()),
            "language": self.lang,
            "summary": {
                "total": len(FEATURE_CATALOG),
                "done": done,
                "in_progress": sum(1 for x in exported if x["status"] == "in_progress"),
                "ready": sum(1 for x in exported if x["status"] == "ready"),
            },
            "features": exported,
        }
        FEATURES_REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def handle_features_input(self, key: int) -> None:
        if key in (pygame.K_ESCAPE, pygame.K_m):
            self.state = STATE_MENU
            return
        if key in (pygame.K_UP, pygame.K_w):
            self.feature_idx = (self.feature_idx - 1) % len(FEATURE_CATALOG)
            self.play_sound("menu")
            return
        if key in (pygame.K_DOWN, pygame.K_s):
            self.feature_idx = (self.feature_idx + 1) % len(FEATURE_CATALOG)
            self.play_sound("menu")
            return
        if key in (pygame.K_LEFT, pygame.K_a):
            page = self.feature_idx // self.feature_page_size
            page = (page - 1) % self.total_feature_pages()
            self.feature_idx = page * self.feature_page_size
            self.feature_idx = min(self.feature_idx, len(FEATURE_CATALOG) - 1)
            return
        if key in (pygame.K_RIGHT, pygame.K_d):
            page = self.feature_idx // self.feature_page_size
            page = (page + 1) % self.total_feature_pages()
            self.feature_idx = page * self.feature_page_size
            self.feature_idx = min(self.feature_idx, len(FEATURE_CATALOG) - 1)
            return
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            feature = FEATURE_CATALOG[self.selected_feature_abs_index()]
            self.cycle_feature_status(feature["id"], feature.get("status", "ready"))
            self.play_sound("menu")
            return
        if key == pygame.K_e:
            self.export_features_report()

    def set_direction(self, d: tuple[int, int]) -> None:
        if self.dir[0] + d[0] == 0 and self.dir[1] + d[1] == 0:
            return
        self.pending_dir = d

    def update(self) -> None:
        if self.state != STATE_PLAY:
            return
        now = time.time()
        mode = self.profile.get("mode", "classic")
        rules = MODE_RULES[mode]
        if rules["timer"] > 0:
            self.time_left -= now - self.last_tick
            if self.time_left <= 0:
                self.finish_game()
                return
        if now - self.last_tick < self.move_interval:
            return
        self.last_tick = now
        self.dir = self.pending_dir
        head = self.snake[0]
        nxt = Point(head.x + self.dir[0], head.y + self.dir[1])
        if rules["wrap"]:
            nxt = Point(nxt.x % GRID_W, nxt.y % GRID_H)
        if not rules["wrap"] and (nxt.x < 0 or nxt.x >= GRID_W or nxt.y < 0 or nxt.y >= GRID_H):
            self.finish_game()
            return
        if nxt in self.snake or nxt in self.obstacles:
            self.finish_game()
            return
        if self.portals and nxt in self.portals:
            a, b = self.portals
            nxt = b if nxt == a else a
        self.snake.insert(0, nxt)

        ate = False
        if nxt == self.food:
            self.score += 1
            self.profile["total_food"] = int(self.profile.get("total_food", 0)) + 1
            self.food = self.find_free_cell()
            ate = True
            self.play_sound("eat")
            if self.score % 4 == 0 and self.special_food is None:
                self.special_food = self.find_free_cell()
                self.special_until = now + 6.0
        if self.special_food and nxt == self.special_food:
            self.score += 3
            self.special_food = None
            ate = True
            self.play_sound("special")
        if self.special_food and now > self.special_until:
            self.special_food = None
        if not ate:
            self.snake.pop()

        self.level = 1 + self.score // 6
        base = max(6, int(self.profile.get("speed", DEFAULT_SPEED)))
        self.move_interval = max(0.055, (1.0 / base) * (0.987 ** self.level))
        self.best_in_run = max(self.best_in_run, self.score)
        self.profile["best_score"] = max(int(self.profile.get("best_score", 0)), self.score)

    def finish_game(self) -> None:
        self.state = STATE_OVER
        self.play_sound("game_over")
        duration = int(time.time() - self.session_start)
        self.profile["total_games"] = int(self.profile.get("total_games", 0)) + 1
        self.profile["total_time"] = int(self.profile.get("total_time", 0)) + duration
        self.profile["best_streak"] = max(int(self.profile.get("best_streak", 0)), self.best_in_run)
        row = {"score": self.score, "mode": self.profile.get("mode", "classic"), "time": duration}
        board = list(self.profile.get("leaderboard", []))
        board.append(row)
        board = sorted(board, key=lambda x: int(x.get("score", 0)), reverse=True)[:LEADERBOARD_MAX]
        self.profile["leaderboard"] = board
        self.save_profile()

    def draw(self) -> None:
        th = self.theme()
        self.screen.fill(th["bg"])
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_MODE:
            self.draw_mode()
        elif self.state == STATE_SETTINGS:
            self.draw_settings()
        elif self.state == STATE_STATS:
            self.draw_stats()
        elif self.state == STATE_FEATURES:
            self.draw_features()
        else:
            self.draw_game()
            if self.state == STATE_PAUSE:
                self.draw_overlay(self.tr("pause"), self.tr("pause_hint"))
            elif self.state == STATE_OVER:
                self.draw_overlay(self.tr("over"), f"{self.tr('over_score', s=self.score)} | {self.tr('over_hint')}")
        pygame.display.flip()

    def draw_text(self, text: str, x: int, y: int, *, font=None, color=None, center=False) -> None:
        font = font or self.font_body
        color = color or self.theme()["text"]
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)

    def draw_menu(self) -> None:
        th = self.theme()
        self.draw_text(self.tr("title"), W // 2, 90, font=self.font_title, color=th["accent"], center=True)
        self.draw_text(self.tr("subtitle"), W // 2, 128, color=th["muted"], center=True)
        for i, item in enumerate(self.menu_items):
            sel = i == self.menu_idx
            prefix = "> " if sel else "  "
            color = th["gold"] if sel else th["text"]
            self.draw_text(prefix + self.tr(item), W // 2, 200 + i * 42, font=self.font_menu, color=color, center=True)
        self.draw_text(self.tr("hud_mode", mode=self.profile.get("mode", "classic")), 18, H - 28, font=self.font_small)
        self.draw_text(f"Lang: {self.lang.upper()}", W - 125, H - 28, font=self.font_small)

    def draw_mode(self) -> None:
        th = self.theme()
        self.draw_text(self.tr("mode_title"), W // 2, 80, font=self.font_title, color=th["accent"], center=True)
        cur = self.profile.get("mode", "classic")
        for i, mode in enumerate(self.mode_items):
            sel = i == self.mode_idx
            mark = "*" if mode == cur else " "
            color = th["gold"] if sel else th["text"]
            self.draw_text(f"{'>' if sel else ' '} [{mark}] {mode}", 180, 180 + i * 50, font=self.font_menu, color=color)
        self.draw_text(self.tr("mode_hint"), W // 2, H - 32, font=self.font_small, color=th["muted"], center=True)

    def setting_value(self, key: str) -> str:
        if key == "settings_lang":
            return self.lang.upper()
        if key == "settings_theme":
            return self.profile.get("theme", "default")
        if key == "settings_speed":
            return str(self.profile.get("speed", DEFAULT_SPEED))
        if key == "settings_grid":
            return self.tr("on") if self.profile.get("grid", True) else self.tr("off")
        if key == "settings_sound":
            return self.tr("on") if self.profile.get("sound", True) else self.tr("off")
        if key == "settings_volume":
            return f"{self.profile.get('volume', 70)}%"
        return ""

    def draw_settings(self) -> None:
        th = self.theme()
        self.draw_text(self.tr("settings_title"), W // 2, 74, font=self.font_title, color=th["accent"], center=True)
        for i, key in enumerate(self.settings_items):
            sel = i == self.settings_idx
            color = th["gold"] if sel else th["text"]
            line = f"{'>' if sel else ' '} {self.tr(key):<20} {self.setting_value(key)}"
            self.draw_text(line, 150, 170 + i * 46, font=self.font_menu, color=color)

    def draw_stats(self) -> None:
        th = self.theme()
        p = self.profile
        self.draw_text(self.tr("stats_title"), W // 2, 72, font=self.font_title, color=th["accent"], center=True)
        lines = [
            self.tr("stats_best", v=p.get("best_score", 0)),
            self.tr("stats_games", v=p.get("total_games", 0)),
            self.tr("stats_food", v=p.get("total_food", 0)),
            self.tr("stats_time", v=p.get("total_time", 0)),
            self.tr("stats_streak", v=p.get("best_streak", 0)),
            self.tr("stats_features", v=sum(1 for f in FEATURE_CATALOG if self.feature_status(f["id"], f.get("status", "ready")) == "done")),
        ]
        for i, line in enumerate(lines):
            self.draw_text(line, 150, 150 + i * 36)
        self.draw_text("Top 10", 150, 350, font=self.font_menu, color=th["gold"])
        for i, row in enumerate(p.get("leaderboard", [])):
            txt = f"{i+1:02d}. {row.get('score', 0):>3}  mode={row.get('mode', 'classic')}  t={row.get('time', 0)}s"
            self.draw_text(txt, 150, 384 + i * 24, font=self.font_small)
        self.draw_text(self.tr("stats_back"), W // 2, H - 30, font=self.font_small, color=th["muted"], center=True)

    def draw_features(self) -> None:
        th = self.theme()
        self.draw_text(self.tr("features_title"), W // 2, 62, font=self.font_title, color=th["accent"], center=True)

        total_pages = self.total_feature_pages()
        page = self.feature_idx // self.feature_page_size
        self.draw_text(self.tr("features_page", page=page + 1, total=total_pages), W // 2, 96, font=self.font_small, color=th["muted"], center=True)

        start = page * self.feature_page_size
        end = min(start + self.feature_page_size, len(FEATURE_CATALOG))
        y = 130
        for i in range(start, end):
            feature = FEATURE_CATALOG[i]
            selected = i == self.feature_idx
            status = self.feature_status(feature["id"], feature.get("status", "ready"))
            color = th["gold"] if selected else th["text"]
            if status == "done":
                status_color = th["ok"]
            elif status == "in_progress":
                status_color = th["accent"]
            else:
                status_color = th["muted"]
            prefix = ">" if selected else " "
            line = f"{prefix} #{feature['id']:03d} {feature['name']}"
            self.draw_text(line, 40, y, font=self.font_body, color=color)
            self.draw_text(self.tr(f"status_{status}"), 360, y, font=self.font_small, color=status_color)
            self.draw_text(feature["description"], 450, y, font=self.font_small, color=th["muted"])
            y += 48

        self.draw_text(self.tr("features_hint"), W // 2, H - 26, font=self.font_small, color=th["muted"], center=True)

    def draw_game(self) -> None:
        th = self.theme()
        pygame.draw.rect(self.screen, th["panel"], pygame.Rect(0, 0, W, HUD_H))
        self.draw_text(self.tr("hud_score", score=self.score, best=self.profile.get("best_score", 0), level=self.level), 14, 12)
        self.draw_text(self.tr("hud_mode", mode=self.profile.get("mode", "classic")), 14, 42)
        if MODE_RULES[self.profile.get("mode", "classic")]["timer"] > 0:
            self.draw_text(self.tr("hud_timer", t=max(0, int(self.time_left))), 520, 12)

        if self.profile.get("grid", True):
            for y in range(GRID_H):
                for x in range(GRID_W):
                    pygame.draw.rect(
                        self.screen,
                        th["grid"],
                        pygame.Rect(x * CELL_SIZE, HUD_H + y * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                        1,
                    )
        for b in self.obstacles:
            pygame.draw.rect(
                self.screen,
                th["danger"],
                pygame.Rect(b.x * CELL_SIZE + 2, HUD_H + b.y * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4),
                border_radius=5,
            )
        if self.portals:
            self.draw_portal(self.portals[0], th["accent"])
            self.draw_portal(self.portals[1], th["gold"])

        self.draw_food(self.food, th["food"])
        if self.special_food:
            self.draw_food(self.special_food, th["special"])

        for i, p in enumerate(self.snake):
            c = th["head"] if i == 0 else th["snake"]
            inset = 3 if i == 0 else 4
            pygame.draw.rect(
                self.screen,
                c,
                pygame.Rect(p.x * CELL_SIZE + inset, HUD_H + p.y * CELL_SIZE + inset, CELL_SIZE - inset * 2, CELL_SIZE - inset * 2),
                border_radius=6,
            )

    def draw_food(self, p: Point, color: tuple[int, int, int]) -> None:
        cx = p.x * CELL_SIZE + CELL_SIZE // 2
        cy = HUD_H + p.y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, color, (cx, cy), CELL_SIZE // 2 - 3)

    def draw_portal(self, p: Point, color: tuple[int, int, int]) -> None:
        cx = p.x * CELL_SIZE + CELL_SIZE // 2
        cy = HUD_H + p.y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, color, (cx, cy), CELL_SIZE // 2 - 2, 3)
        pygame.draw.circle(self.screen, color, (cx, cy), CELL_SIZE // 2 - 8, 2)

    def draw_overlay(self, title: str, sub: str) -> None:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        self.draw_text(title, W // 2, H // 2 - 26, font=self.font_title, color=self.theme()["gold"], center=True)
        self.draw_text(sub, W // 2, H // 2 + 18, center=True)

def main() -> None:
    SnakeApp().run()


if __name__ == "__main__":
    main()

