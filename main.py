import math
import random
import sys
from dataclasses import dataclass

import pygame


WIDTH = 900
HEIGHT = 600
FPS = 60
DOT_COUNT = 140
PLAYER_SPEED = 2.6
AI_SPEED = 2.2
PULSE_COOLDOWN = 1.4
PULSE_RADIUS = 60
PULSE_POWER = 1.1
MATCH_TIME = 120

BACKGROUND = (18, 18, 28)
NEUTRAL = (170, 170, 190)
PLAYER_COLOR = (72, 186, 255)
AI_COLOR = (255, 96, 114)
TEXT_COLOR = (232, 232, 240)


@dataclass
class Dot:
    x: float
    y: float
    vx: float
    vy: float
    owner: str

    def color(self):
        if self.owner == "player":
            return PLAYER_COLOR
        if self.owner == "ai":
            return AI_COLOR
        return NEUTRAL

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 10 or self.x > WIDTH - 10:
            self.vx *= -1
        if self.y < 10 or self.y > HEIGHT - 10:
            self.vy *= -1
        self.x = max(10, min(WIDTH - 10, self.x))
        self.y = max(10, min(HEIGHT - 10, self.y))


@dataclass
class Agent:
    x: float
    y: float
    color: tuple[int, int, int]
    speed: float
    cooldown: float = 0

    def can_pulse(self):
        return self.cooldown <= 0

    def tick(self, dt: float):
        self.cooldown = max(0, self.cooldown - dt)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("War of Dots Lite")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.big_font = pygame.font.SysFont("consolas", 40)
        self.player = Agent(120, HEIGHT / 2, PLAYER_COLOR, PLAYER_SPEED)
        self.ai = Agent(WIDTH - 120, HEIGHT / 2, AI_COLOR, AI_SPEED)
        self.dots = self.spawn_dots()
        self.time_left = MATCH_TIME
        self.winner = None

    def spawn_dots(self):
        dots = []
        for _ in range(DOT_COUNT):
            x = random.uniform(60, WIDTH - 60)
            y = random.uniform(60, HEIGHT - 60)
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.5, 1.4)
            dots.append(
                Dot(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    owner="neutral",
                )
            )
        return dots

    def handle_player_input(self, dt: float):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.player.speed
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.player.speed
        self.player.x = max(20, min(WIDTH - 20, self.player.x + dx))
        self.player.y = max(20, min(HEIGHT - 20, self.player.y + dy))
        if keys[pygame.K_SPACE] and self.player.can_pulse():
            self.emit_pulse(self.player)
            self.player.cooldown = PULSE_COOLDOWN

    def ai_logic(self, dt: float):
        target = random.choice(self.dots)
        if target:
            angle = math.atan2(target.y - self.ai.y, target.x - self.ai.x)
            self.ai.x += math.cos(angle) * self.ai.speed
            self.ai.y += math.sin(angle) * self.ai.speed
            self.ai.x = max(20, min(WIDTH - 20, self.ai.x))
            self.ai.y = max(20, min(HEIGHT - 20, self.ai.y))
        if self.ai.can_pulse() and random.random() < 0.02:
            self.emit_pulse(self.ai)
            self.ai.cooldown = PULSE_COOLDOWN

    def emit_pulse(self, agent: Agent):
        for dot in self.dots:
            dx = dot.x - agent.x
            dy = dot.y - agent.y
            distance = math.hypot(dx, dy)
            if distance <= PULSE_RADIUS:
                influence = (PULSE_RADIUS - distance) / PULSE_RADIUS
                push = influence * PULSE_POWER
                if distance > 0:
                    dot.vx += (dx / distance) * push
                    dot.vy += (dy / distance) * push
                dot.owner = "player" if agent is self.player else "ai"

    def update(self, dt: float):
        if self.winner:
            return
        self.time_left = max(0, self.time_left - dt)
        if self.time_left == 0:
            self.winner = self.resolve_winner()
            return
        self.handle_player_input(dt)
        self.ai_logic(dt)
        for dot in self.dots:
            dot.update()
            self.check_capture(dot)
        self.player.tick(dt)
        self.ai.tick(dt)
        if self.count_owner("player") >= int(DOT_COUNT * 0.7):
            self.winner = "Você venceu!"
        if self.count_owner("ai") >= int(DOT_COUNT * 0.7):
            self.winner = "A I venceu!"

    def resolve_winner(self):
        player_count = self.count_owner("player")
        ai_count = self.count_owner("ai")
        if player_count > ai_count:
            return "Tempo! Você venceu!"
        if ai_count > player_count:
            return "Tempo! A I venceu!"
        return "Empate!"

    def count_owner(self, owner):
        return sum(1 for dot in self.dots if dot.owner == owner)

    def check_capture(self, dot: Dot):
        for agent, owner in ((self.player, "player"), (self.ai, "ai")):
            distance = math.hypot(dot.x - agent.x, dot.y - agent.y)
            if distance < 24:
                dot.owner = owner

    def draw_ui(self):
        player_count = self.count_owner("player")
        ai_count = self.count_owner("ai")
        neutral_count = DOT_COUNT - player_count - ai_count
        ui_text = f"Você: {player_count}  IA: {ai_count}  Neutros: {neutral_count}"
        time_text = f"Tempo: {int(self.time_left)}s"
        text_surface = self.font.render(ui_text, True, TEXT_COLOR)
        time_surface = self.font.render(time_text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (20, 16))
        self.screen.blit(time_surface, (WIDTH - time_surface.get_width() - 20, 16))
        if not self.player.can_pulse():
            cooldown_text = f"Pulso: {self.player.cooldown:.1f}s"
            cooldown_surface = self.font.render(cooldown_text, True, TEXT_COLOR)
            self.screen.blit(cooldown_surface, (20, HEIGHT - 34))

    def draw_agents(self):
        pygame.draw.circle(self.screen, self.player.color, (int(self.player.x), int(self.player.y)), 12)
        pygame.draw.circle(self.screen, self.ai.color, (int(self.ai.x), int(self.ai.y)), 12)
        pygame.draw.circle(
            self.screen,
            self.player.color,
            (int(self.player.x), int(self.player.y)),
            PULSE_RADIUS,
            1,
        )

    def draw_dots(self):
        for dot in self.dots:
            pygame.draw.circle(self.screen, dot.color(), (int(dot.x), int(dot.y)), 5)

    def draw_winner(self):
        if not self.winner:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 12, 18, 210))
        self.screen.blit(overlay, (0, 0))
        text_surface = self.big_font.render(self.winner, True, TEXT_COLOR)
        restart_surface = self.font.render("Pressione R para reiniciar", True, TEXT_COLOR)
        self.screen.blit(
            text_surface,
            (WIDTH / 2 - text_surface.get_width() / 2, HEIGHT / 2 - 40),
        )
        self.screen.blit(
            restart_surface,
            (WIDTH / 2 - restart_surface.get_width() / 2, HEIGHT / 2 + 20),
        )

    def reset(self):
        self.player.x, self.player.y = 120, HEIGHT / 2
        self.ai.x, self.ai.y = WIDTH - 120, HEIGHT / 2
        self.dots = self.spawn_dots()
        self.time_left = MATCH_TIME
        self.winner = None
        self.player.cooldown = 0
        self.ai.cooldown = 0

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    if self.winner:
                        self.reset()
            self.update(dt)
            self.screen.fill(BACKGROUND)
            self.draw_dots()
            self.draw_agents()
            self.draw_ui()
            self.draw_winner()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
