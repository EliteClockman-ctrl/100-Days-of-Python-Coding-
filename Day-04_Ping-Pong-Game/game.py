"""Day 04 Ping Pong Game using pygame.

Features:
- Main menu with PvP, Vs AI, Settings, Quit
- Settings for volume, target score, AI speed
- Modern board rendering with background image from web resource
- Sound effects from web resource pack
- Pause, restart, and winner overlay
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
AUDIO_DIR = ASSETS / "audio"
FONT_PATH = ASSETS / "fonts" / "PressStart2P-Regular.ttf"
BG_PATH = ASSETS / "images" / "background.jpg"
PROFILE_PATH = ROOT / "profile.json"

SCREEN_W = 1280
SCREEN_H = 720
FPS = 120

SCENE_MENU = "menu"
SCENE_SETTINGS = "settings"
SCENE_PLAYING = "playing"
SCENE_RESULT = "result"

WHITE = (242, 246, 252)
MUTED = (175, 190, 210)
DARK = (10, 16, 28)
NAVY = (18, 32, 56)
CYAN = (58, 188, 255)
CYAN_SOFT = (90, 214, 255)
ORANGE = (255, 170, 80)
RED = (248, 92, 92)

DEFAULTS = {
    "master_volume": 0.65,
    "target_score": 7,
    "ai_speed": 0.66,
    "ball_speed": 420,
    "mode": "ai",
}


@dataclass
class GameConfig:
    master_volume: float = DEFAULTS["master_volume"]
    target_score: int = DEFAULTS["target_score"]
    ai_speed: float = DEFAULTS["ai_speed"]
    ball_speed: float = DEFAULTS["ball_speed"]
    mode: str = DEFAULTS["mode"]


class SoundManager:
    def __init__(self) -> None:
        self.available = False
        self.hit: pygame.mixer.Sound | None = None
        self.score: pygame.mixer.Sound | None = None

    def load(self) -> None:
        try:
            pygame.mixer.init()
            self.hit = pygame.mixer.Sound(str(AUDIO_DIR / "Pop.ogg"))
            self.score = pygame.mixer.Sound(str(AUDIO_DIR / "Score.ogg"))
            self.available = True
        except Exception:
            self.available = False
            self.hit = None
            self.score = None

    def set_volume(self, value: float) -> None:
        if not self.available:
            return
        for snd in (self.hit, self.score):
            if snd:
                snd.set_volume(max(0.0, min(1.0, value)))

    def play_hit(self) -> None:
        if self.hit:
            self.hit.play()

    def play_score(self) -> None:
        if self.score:
            self.score.play()


@dataclass
class Paddle:
    x: float
    y: float
    w: int = 20
    h: int = 130
    speed: float = 560

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def move(self, dy: float) -> None:
        self.y += dy
        self.y = max(20, min(SCREEN_H - 20 - self.h, self.y))


@dataclass
class Ball:
    x: float
    y: float
    radius: int = 14
    vx: float = 0.0
    vy: float = 0.0

    def reset(self, base_speed: float, serve_right: bool) -> None:
        self.x = SCREEN_W * 0.5
        self.y = SCREEN_H * 0.5
        angle = random.uniform(-0.5, 0.5)
        direction = 1 if serve_right else -1
        self.vx = math.cos(angle) * base_speed * direction
        self.vy = math.sin(angle) * base_speed

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]


class Button:
    def __init__(self, text: str, x: int, y: int, w: int, h: int) -> None:
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, active: bool = False) -> None:
        bg = (40, 60, 95) if not active else (62, 102, 162)
        pygame.draw.rect(surf, bg, self.rect, border_radius=10)
        pygame.draw.rect(surf, (138, 171, 220), self.rect, 2, border_radius=10)
        label = font.render(self.text, True, WHITE)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def hit_test(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class PingPongGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Day 04 - Ping Pong Game")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True

        self.config = self.load_profile()

        self.title_font = self.load_font(44)
        self.head_font = self.load_font(24)
        self.text_font = self.load_font(16)
        self.small_font = self.load_font(12)

        self.bg = self.load_background()
        self.sounds = SoundManager()
        self.sounds.load()
        self.sounds.set_volume(self.config.master_volume)

        self.scene = SCENE_MENU
        self.mode = self.config.mode
        self.paused = False
        self.winner = ""
        self.flash_timer = 0.0

        self.left_score = 0
        self.right_score = 0

        self.left_paddle = Paddle(50, SCREEN_H * 0.5 - 65)
        self.right_paddle = Paddle(SCREEN_W - 70, SCREEN_H * 0.5 - 65)
        self.ball = Ball(SCREEN_W * 0.5, SCREEN_H * 0.5)
        self.ball.reset(self.config.ball_speed, serve_right=random.choice([True, False]))

        self.particles: list[Particle] = []

        self.menu_buttons = [
            Button("Start Vs AI", SCREEN_W // 2 - 170, 260, 340, 58),
            Button("Start 2 Players", SCREEN_W // 2 - 170, 330, 340, 58),
            Button("Settings", SCREEN_W // 2 - 170, 400, 340, 58),
            Button("Quit", SCREEN_W // 2 - 170, 470, 340, 58),
        ]

        self.settings_buttons = [
            Button("Target Score -", 250, 200, 260, 54),
            Button("Target Score +", 530, 200, 260, 54),
            Button("AI Speed -", 250, 285, 260, 54),
            Button("AI Speed +", 530, 285, 260, 54),
            Button("Volume -", 250, 370, 260, 54),
            Button("Volume +", 530, 370, 260, 54),
            Button("Back", 430, 470, 220, 58),
        ]

        self.result_buttons = [
            Button("Play Again", SCREEN_W // 2 - 170, 410, 340, 58),
            Button("Main Menu", SCREEN_W // 2 - 170, 480, 340, 58),
        ]

    def load_font(self, size: int) -> pygame.font.Font:
        if FONT_PATH.exists():
            return pygame.font.Font(str(FONT_PATH), size)
        return pygame.font.SysFont("consolas", size)

    def load_background(self) -> pygame.Surface:
        if BG_PATH.exists():
            try:
                img = pygame.image.load(str(BG_PATH)).convert()
                return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
            except Exception:
                pass
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        bg.fill((12, 18, 30))
        return bg

    def load_profile(self) -> GameConfig:
        if not PROFILE_PATH.exists():
            return GameConfig()
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return GameConfig()
        merged = dict(DEFAULTS)
        merged.update(data)
        return GameConfig(
            master_volume=float(merged["master_volume"]),
            target_score=int(merged["target_score"]),
            ai_speed=float(merged["ai_speed"]),
            ball_speed=float(merged["ball_speed"]),
            mode=str(merged["mode"]),
        )

    def save_profile(self) -> None:
        payload = {
            "master_volume": self.config.master_volume,
            "target_score": self.config.target_score,
            "ai_speed": self.config.ai_speed,
            "ball_speed": self.config.ball_speed,
            "mode": self.mode,
        }
        PROFILE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def reset_match(self) -> None:
        self.left_score = 0
        self.right_score = 0
        self.left_paddle.y = SCREEN_H * 0.5 - self.left_paddle.h * 0.5
        self.right_paddle.y = SCREEN_H * 0.5 - self.right_paddle.h * 0.5
        self.ball.reset(self.config.ball_speed, serve_right=random.choice([True, False]))
        self.particles.clear()
        self.paused = False
        self.winner = ""
        self.flash_timer = 0.0

    def spawn_hit_particles(self) -> None:
        for _ in range(10):
            speed = random.uniform(80, 260)
            angle = random.uniform(0, math.tau)
            self.particles.append(
                Particle(
                    x=self.ball.x,
                    y=self.ball.y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(0.15, 0.45),
                    color=random.choice([CYAN, CYAN_SOFT, ORANGE, WHITE]),
                )
            )

    def update_particles(self, dt: float) -> None:
        alive: list[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.96
            p.vy *= 0.96
            alive.append(p)
        self.particles = alive

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.scene == SCENE_PLAYING:
                        self.paused = not self.paused
                    elif self.scene == SCENE_SETTINGS:
                        self.scene = SCENE_MENU
                    else:
                        self.running = False
                if self.scene == SCENE_PLAYING and event.key == pygame.K_r:
                    self.reset_match()
                if self.scene == SCENE_RESULT and event.key == pygame.K_SPACE:
                    self.start_game(self.mode)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)

    def handle_click(self, pos: tuple[int, int]) -> None:
        if self.scene == SCENE_MENU:
            if self.menu_buttons[0].hit_test(pos):
                self.start_game("ai")
            elif self.menu_buttons[1].hit_test(pos):
                self.start_game("pvp")
            elif self.menu_buttons[2].hit_test(pos):
                self.scene = SCENE_SETTINGS
            elif self.menu_buttons[3].hit_test(pos):
                self.running = False
            self.sounds.play_hit()
            return

        if self.scene == SCENE_SETTINGS:
            if self.settings_buttons[0].hit_test(pos):
                self.config.target_score = max(3, self.config.target_score - 1)
            elif self.settings_buttons[1].hit_test(pos):
                self.config.target_score = min(25, self.config.target_score + 1)
            elif self.settings_buttons[2].hit_test(pos):
                self.config.ai_speed = max(0.25, self.config.ai_speed - 0.05)
            elif self.settings_buttons[3].hit_test(pos):
                self.config.ai_speed = min(1.2, self.config.ai_speed + 0.05)
            elif self.settings_buttons[4].hit_test(pos):
                self.config.master_volume = max(0.0, self.config.master_volume - 0.05)
                self.sounds.set_volume(self.config.master_volume)
            elif self.settings_buttons[5].hit_test(pos):
                self.config.master_volume = min(1.0, self.config.master_volume + 0.05)
                self.sounds.set_volume(self.config.master_volume)
            elif self.settings_buttons[6].hit_test(pos):
                self.save_profile()
                self.scene = SCENE_MENU
            self.sounds.play_hit()
            return

        if self.scene == SCENE_RESULT:
            if self.result_buttons[0].hit_test(pos):
                self.start_game(self.mode)
            elif self.result_buttons[1].hit_test(pos):
                self.scene = SCENE_MENU
            self.sounds.play_hit()

    def start_game(self, mode: str) -> None:
        self.mode = mode
        self.scene = SCENE_PLAYING
        self.reset_match()

    def update_play(self, dt: float) -> None:
        if self.paused:
            return

        keys = pygame.key.get_pressed()

        left_move = 0.0
        if keys[pygame.K_w]:
            left_move -= self.left_paddle.speed * dt
        if keys[pygame.K_s]:
            left_move += self.left_paddle.speed * dt
        self.left_paddle.move(left_move)

        if self.mode == "pvp":
            right_move = 0.0
            if keys[pygame.K_UP]:
                right_move -= self.right_paddle.speed * dt
            if keys[pygame.K_DOWN]:
                right_move += self.right_paddle.speed * dt
            self.right_paddle.move(right_move)
        else:
            ai_center = self.right_paddle.y + self.right_paddle.h * 0.5
            target = self.ball.y + self.ball.vy * 0.08
            if ai_center < target - 8:
                self.right_paddle.move(self.right_paddle.speed * self.config.ai_speed * dt)
            elif ai_center > target + 8:
                self.right_paddle.move(-self.right_paddle.speed * self.config.ai_speed * dt)

        self.ball.update(dt)

        if self.ball.y - self.ball.radius <= 14:
            self.ball.y = 14 + self.ball.radius
            self.ball.vy *= -1
            self.sounds.play_hit()
            self.spawn_hit_particles()
        elif self.ball.y + self.ball.radius >= SCREEN_H - 14:
            self.ball.y = SCREEN_H - 14 - self.ball.radius
            self.ball.vy *= -1
            self.sounds.play_hit()
            self.spawn_hit_particles()

        left_rect = self.left_paddle.rect()
        right_rect = self.right_paddle.rect()
        ball_rect = pygame.Rect(
            int(self.ball.x - self.ball.radius), int(self.ball.y - self.ball.radius), self.ball.radius * 2, self.ball.radius * 2
        )

        if ball_rect.colliderect(left_rect) and self.ball.vx < 0:
            self.ball.x = left_rect.right + self.ball.radius
            self.reflect_from_paddle(self.left_paddle, is_left=True)

        if ball_rect.colliderect(right_rect) and self.ball.vx > 0:
            self.ball.x = right_rect.left - self.ball.radius
            self.reflect_from_paddle(self.right_paddle, is_left=False)

        if self.ball.x < -30:
            self.right_score += 1
            self.point_scored(serve_right=False)
        elif self.ball.x > SCREEN_W + 30:
            self.left_score += 1
            self.point_scored(serve_right=True)

        if self.left_score >= self.config.target_score:
            self.winner = "Left Player"
            self.scene = SCENE_RESULT
            self.sounds.play_score()
        elif self.right_score >= self.config.target_score:
            self.winner = "Right Player" if self.mode == "pvp" else "AI Bot"
            self.scene = SCENE_RESULT
            self.sounds.play_score()

    def reflect_from_paddle(self, paddle: Paddle, is_left: bool) -> None:
        offset = (self.ball.y - (paddle.y + paddle.h * 0.5)) / (paddle.h * 0.5)
        offset = max(-1.0, min(1.0, offset))
        speed = min(980, math.hypot(self.ball.vx, self.ball.vy) * 1.04)
        angle = offset * 0.95
        direction = 1 if is_left else -1
        self.ball.vx = direction * math.cos(angle) * speed
        self.ball.vy = math.sin(angle) * speed
        self.sounds.play_hit()
        self.spawn_hit_particles()

    def point_scored(self, serve_right: bool) -> None:
        self.ball.reset(self.config.ball_speed, serve_right=serve_right)
        self.flash_timer = 0.28
        self.sounds.play_score()

    def update(self, dt: float) -> None:
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.update_particles(dt)
        if self.scene == SCENE_PLAYING:
            self.update_play(dt)

    def draw_background(self) -> None:
        self.screen.blit(self.bg, (0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((8, 14, 22, 150))
        self.screen.blit(overlay, (0, 0))

    def draw_center_line(self) -> None:
        for y in range(30, SCREEN_H - 30, 30):
            pygame.draw.rect(self.screen, (220, 230, 250, 80), (SCREEN_W // 2 - 4, y, 8, 16), border_radius=3)

    def draw_score(self) -> None:
        left = self.title_font.render(str(self.left_score), True, WHITE)
        right = self.title_font.render(str(self.right_score), True, WHITE)
        self.screen.blit(left, left.get_rect(center=(SCREEN_W * 0.25, 52)))
        self.screen.blit(right, right.get_rect(center=(SCREEN_W * 0.75, 52)))

        mode_text = "Mode: VS AI" if self.mode == "ai" else "Mode: 2 Players"
        mode_surf = self.text_font.render(mode_text, True, CYAN_SOFT)
        self.screen.blit(mode_surf, (SCREEN_W // 2 - mode_surf.get_width() // 2, 20))

        target = self.text_font.render(f"Target: {self.config.target_score}", True, MUTED)
        self.screen.blit(target, (22, 20))

    def draw_play_scene(self) -> None:
        self.draw_background()
        self.draw_center_line()
        self.draw_score()

        pygame.draw.rect(self.screen, WHITE, self.left_paddle.rect(), border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.right_paddle.rect(), border_radius=8)

        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 0.45))))
            col = (p.color[0], p.color[1], p.color[2], alpha)
            puff = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(puff, col, (3, 3), 3)
            self.screen.blit(puff, (p.x - 3, p.y - 3))

        pygame.draw.circle(self.screen, ORANGE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)
        pygame.draw.circle(self.screen, WHITE, (int(self.ball.x - 4), int(self.ball.y - 4)), self.ball.radius // 3)

        hint = self.small_font.render("W/S: Left  |  Up/Down: Right  |  ESC: Pause  |  R: Restart", True, MUTED)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 26))

        if self.flash_timer > 0:
            alpha = int(120 * (self.flash_timer / 0.28))
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            self.screen.blit(flash, (0, 0))

        if self.paused:
            self.draw_pause_overlay()

    def draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((2, 8, 18, 190))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(SCREEN_W // 2 - 280, SCREEN_H // 2 - 140, 560, 280)
        pygame.draw.rect(self.screen, NAVY, card, border_radius=14)
        pygame.draw.rect(self.screen, CYAN, card, 2, border_radius=14)

        title = self.head_font.render("Paused", True, WHITE)
        info = self.text_font.render("Press ESC to continue", True, MUTED)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 20)))
        self.screen.blit(info, info.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 26)))

    def draw_menu_scene(self) -> None:
        self.draw_background()

        title = self.title_font.render("PING PONG", True, WHITE)
        subtitle = self.text_font.render("Day 04 - 100 Days of Python Coding", True, CYAN_SOFT)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 140)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 182)))

        mouse = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            button.draw(self.screen, self.text_font, button.hit_test(mouse))

        footer = self.small_font.render("Resources from web: OpenGameArt SFX + Google Fonts", True, MUTED)
        self.screen.blit(footer, footer.get_rect(center=(SCREEN_W // 2, SCREEN_H - 34)))

    def draw_settings_scene(self) -> None:
        self.draw_background()
        title = self.title_font.render("SETTINGS", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 110)))

        info1 = self.text_font.render(f"Target Score: {self.config.target_score}", True, CYAN_SOFT)
        info2 = self.text_font.render(f"AI Speed: {self.config.ai_speed:.2f}", True, CYAN_SOFT)
        info3 = self.text_font.render(f"Volume: {self.config.master_volume:.2f}", True, CYAN_SOFT)
        self.screen.blit(info1, (830, 218))
        self.screen.blit(info2, (830, 303))
        self.screen.blit(info3, (830, 388))

        mouse = pygame.mouse.get_pos()
        for button in self.settings_buttons:
            button.draw(self.screen, self.text_font, button.hit_test(mouse))

    def draw_result_scene(self) -> None:
        self.draw_background()

        card = pygame.Rect(SCREEN_W // 2 - 320, 170, 640, 360)
        pygame.draw.rect(self.screen, (13, 26, 45), card, border_radius=16)
        pygame.draw.rect(self.screen, CYAN, card, 2, border_radius=16)

        title = self.title_font.render("MATCH FINISHED", True, WHITE)
        winner_text = self.head_font.render(f"Winner: {self.winner}", True, ORANGE)
        final_score = self.text_font.render(f"Score {self.left_score} : {self.right_score}", True, CYAN_SOFT)

        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 245)))
        self.screen.blit(winner_text, winner_text.get_rect(center=(SCREEN_W // 2, 302)))
        self.screen.blit(final_score, final_score.get_rect(center=(SCREEN_W // 2, 338)))

        mouse = pygame.mouse.get_pos()
        for button in self.result_buttons:
            button.draw(self.screen, self.text_font, button.hit_test(mouse))

        tip = self.small_font.render("Press SPACE to play again quickly", True, MUTED)
        self.screen.blit(tip, tip.get_rect(center=(SCREEN_W // 2, 555)))

    def draw(self) -> None:
        if self.scene == SCENE_MENU:
            self.draw_menu_scene()
        elif self.scene == SCENE_SETTINGS:
            self.draw_settings_scene()
        elif self.scene == SCENE_PLAYING:
            self.draw_play_scene()
        elif self.scene == SCENE_RESULT:
            self.draw_result_scene()

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        self.save_profile()
        pygame.quit()


if __name__ == "__main__":
    PingPongGame().run()