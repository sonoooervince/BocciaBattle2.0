from __future__ import annotations

import math
import random
from typing import Any

import pygame

from game.boccia import Boccia
from game.boccia_profiles import (
    BOCCIA_PROFILES,
    cycle_boccia_profile,
    get_boccia_profile,
)
from game.brands import get_brand
from game.field import Field
from game.jack import Jack
from game.physics import PhysicsEngine


class TrainingScreen:
    """Allenamento libero con la stessa fisica della partita."""

    READY = "ready"
    ROLLING = "rolling"

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.window = settings["window"]
        self.gameplay = settings["gameplay"]
        self.physics_settings = settings["physics"]
        self.colors = settings["colors"]

        field_cfg = settings["field"]
        self.field = Field(
            pygame.Rect(
                field_cfg["x"],
                field_cfg["y"],
                field_cfg["width"],
                field_cfg["height"],
            )
        )
        self.physics = PhysicsEngine(
            friction_deceleration=self.physics_settings["friction_deceleration"],
            border_restitution=self.physics_settings["border_restitution"],
            border_tangent_damping=self.physics_settings["border_tangent_damping"],
            collision_restitution=self.physics_settings["collision_restitution"],
            stop_speed=self.physics_settings["stop_speed"],
            max_substeps=self.physics_settings["max_substeps"],
        )

        self.font_title = pygame.font.SysFont("arial", 34, bold=True)
        self.font_big = pygame.font.SysFont("arial", 23, bold=True)
        self.font = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)

        self.random = random.Random()
        self.selected_boccia_type = self.gameplay.get(
            "selected_boccia_type",
            "medie",
        )
        self.selected_brand = self.gameplay.get(
            "selected_brand",
            "handi_life_sport",
        )
        self.ball_limit = int(self.gameplay.get("training_ball_limit", 12))

        self.angle = 0.0
        self.power = 55.0
        self.state = self.READY
        self.balls: list[Boccia] = []
        self.active_ball: Boccia | None = None
        self.last_thrown_ball: Boccia | None = None
        self.throws = 0
        self.last_distance_m: float | None = None
        self.best_distance_m: float | None = None
        self.jack = self._new_jack()
        self._prepare_ball()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._launch()
            elif event.key == pygame.K_r:
                self._reset_training()
            elif event.key == pygame.K_x and self.state == self.READY:
                self._clear_balls()
            elif event.key == pygame.K_j and self.state == self.READY:
                self._randomize_jack()
            elif event.key == pygame.K_c:
                self.angle = 0.0
            elif event.key in (
                pygame.K_1,
                pygame.K_2,
                pygame.K_3,
                pygame.K_4,
                pygame.K_5,
            ):
                self._select_boccia_type(event.key - pygame.K_1)
            elif event.key == pygame.K_q:
                self._cycle_boccia_type(-1)
            elif event.key == pygame.K_e:
                self._cycle_boccia_type(1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._change_angle(-self.gameplay["angle_step"])
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._change_angle(self.gameplay["angle_step"])
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._change_power(self.gameplay["power_step"])
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._change_power(-self.gameplay["power_step"])

        elif event.type == pygame.MOUSEMOTION and self.state == self.READY:
            self._aim_at_mouse(event.pos)

        elif event.type == pygame.MOUSEWHEEL and self.state == self.READY:
            self._change_power(event.y * self.gameplay["power_step"])

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1
                and self.state == self.READY
                and self.field.rect.collidepoint(event.pos)
            ):
                self._aim_at_mouse(event.pos)
                self._launch()
            elif event.button == 3 and self.state == self.READY:
                self.angle = 0.0

    def update(self, dt: float) -> None:
        if self.state == self.READY:
            self._continuous_keyboard_input(dt)
            return

        report = self.physics.step(
            self.balls,
            self.jack,
            dt,
            self.field.playable_bounds,
        )
        del report

        if not self.physics.is_settled(self.balls, self.jack):
            return

        if self.last_thrown_ball is not None:
            self.last_distance_m = self._pixels_to_meters(
                self.last_thrown_ball.position.distance_to(
                    self.jack.position
                )
            )
            if (
                self.best_distance_m is None
                or self.last_distance_m < self.best_distance_m
            ):
                self.best_distance_m = self.last_distance_m

        self.state = self.READY
        self._prepare_ball()

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        self.field.draw(self.screen)
        self._draw_training_rings()

        for ball in self.balls:
            ball.draw(self.screen)

        self.jack.draw(self.screen)

        if self.state == self.READY and self.active_ball is not None:
            self._draw_aim_indicator()
            self.active_ball.draw(self.screen, selected=True)

        self._draw_hud()

    def _new_jack(self) -> Jack:
        return Jack(
            self.field.jack_default_position,
            radius=self.gameplay["jack_radius"],
            mass=self.gameplay["jack_mass"],
        )

    def _prepare_ball(self) -> None:
        self.active_ball = Boccia(
            self.field.launch_point,
            radius=self.gameplay["boccia_radius"],
            color=tuple(self.colors["red_ball"]),
            owner_key="red",
            mass=self.gameplay["boccia_mass"],
            boccia_type=self.selected_boccia_type,
        )

    def _launch(self) -> None:
        if self.state != self.READY or self.active_ball is None:
            return

        self.active_ball.launch(
            angle_degrees=self.angle,
            power_percent=self.power,
            min_speed=self.gameplay["min_launch_speed"],
            max_speed=self.gameplay["max_launch_speed"],
        )
        self.balls.append(self.active_ball)
        if len(self.balls) > self.ball_limit:
            self.balls.pop(0)

        self.last_thrown_ball = self.active_ball
        self.active_ball = None
        self.throws += 1
        self.state = self.ROLLING

    def _reset_training(self) -> None:
        self.balls.clear()
        self.jack = self._new_jack()
        self.throws = 0
        self.last_distance_m = None
        self.best_distance_m = None
        self.angle = 0.0
        self.power = 55.0
        self.state = self.READY
        self._prepare_ball()

    def _clear_balls(self) -> None:
        self.balls.clear()
        self.last_thrown_ball = None
        self.last_distance_m = None
        self._prepare_ball()

    def _randomize_jack(self) -> None:
        margin_x = 70
        x = self.random.uniform(
            self.field.rect.left + margin_x,
            self.field.rect.right - margin_x,
        )
        y = self.random.uniform(
            self.field.rect.top + 80,
            self.field.launch_line_y - 120,
        )
        self.jack.position.update(x, y)
        self.jack.velocity.update(0, 0)
        self.last_distance_m = None
        self._prepare_ball()

    def _select_boccia_type(self, index: int) -> None:
        if self.state != self.READY or not (0 <= index < len(BOCCIA_PROFILES)):
            return
        self.selected_boccia_type = BOCCIA_PROFILES[index].key
        self._prepare_ball()

    def _cycle_boccia_type(self, direction: int) -> None:
        if self.state != self.READY:
            return
        self.selected_boccia_type = cycle_boccia_profile(
            self.selected_boccia_type,
            direction,
        ).key
        self._prepare_ball()

    def _continuous_keyboard_input(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._change_angle(
                -self.gameplay["angle_keyboard_speed"] * dt
            )
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._change_angle(
                self.gameplay["angle_keyboard_speed"] * dt
            )
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._change_power(
                self.gameplay["power_keyboard_speed"] * dt
            )
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._change_power(
                -self.gameplay["power_keyboard_speed"] * dt
            )

    def _aim_at_mouse(self, mouse_pos: tuple[int, int]) -> None:
        vector = pygame.Vector2(mouse_pos) - self.field.launch_point
        if vector.length_squared() < 4:
            return
        angle = math.degrees(math.atan2(vector.x, -vector.y))
        limit = self.gameplay["max_aim_angle"]
        self.angle = max(-limit, min(limit, angle))

    def _change_angle(self, amount: float) -> None:
        if self.state != self.READY:
            return
        limit = self.gameplay["max_aim_angle"]
        self.angle = max(-limit, min(limit, self.angle + amount))

    def _change_power(self, amount: float) -> None:
        if self.state != self.READY:
            return
        self.power = max(
            self.gameplay["min_power"],
            min(self.gameplay["max_power"], self.power + amount),
        )

    def _pixels_to_meters(self, pixels: float) -> float:
        scale = (
            self.field.rect.height
            / self.gameplay["virtual_field_length_m"]
        )
        return pixels / scale

    def _draw_training_rings(self) -> None:
        center = (
            round(self.jack.position.x),
            round(self.jack.position.y),
        )
        for radius in (35, 70, 105):
            pygame.draw.circle(
                self.screen,
                (220, 230, 225),
                center,
                radius,
                1,
            )

    def _draw_aim_indicator(self) -> None:
        angle_radians = math.radians(self.angle)
        direction = pygame.Vector2(
            math.sin(angle_radians),
            -math.cos(angle_radians),
        )
        start = self.field.launch_point
        end = start + direction * (
            95 + (self.power / 100.0) * 155
        )
        pygame.draw.line(
            self.screen,
            tuple(self.colors["aim"]),
            start,
            end,
            4,
        )
        side = pygame.Vector2(-direction.y, direction.x)
        pygame.draw.polygon(
            self.screen,
            tuple(self.colors["aim"]),
            [
                end,
                end - direction * 18 + side * 10,
                end - direction * 18 - side * 10,
            ],
        )

    def _draw_hud(self) -> None:
        x = self.field.rect.right + 42
        y = 38
        width = self.window["width"] - x - 38

        title = self.font_title.render(
            "ALLENAMENTO",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (x, y))
        y += 52

        brand = get_brand(self.selected_brand)
        profile = get_boccia_profile(self.selected_boccia_type)

        self._panel(x, y, width, 110)
        self._row(x + 18, y + 14, "Marca", brand.display_name)
        self._row(x + 18, y + 46, "Boccia", profile.label)
        self._row(
            x + 18,
            y + 78,
            "Stato",
            "PRONTO" if self.state == self.READY else "IN MOVIMENTO",
        )
        y += 126

        self._panel(x, y, width, 142)
        self._row(x + 18, y + 12, "Direzione", f"{self.angle:+.1f}°")
        self._row(x + 18, y + 44, "Potenza", f"{self.power:.0f}%")
        self._row(x + 18, y + 76, "Tiri", str(self.throws))
        self._row(
            x + 18,
            y + 108,
            "Bocce in campo",
            f"{len(self.balls)} / {self.ball_limit}",
        )
        y += 158

        self._panel(x, y, width, 108)
        self._row(
            x + 18,
            y + 16,
            "Ultimo tiro",
            self._distance_text(self.last_distance_m),
        )
        self._row(
            x + 18,
            y + 52,
            "Miglior tiro",
            self._distance_text(self.best_distance_m),
        )
        y += 126

        heading = self.font_big.render(
            "CONTROLLI",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(heading, (x, y))
        y += 38

        controls = (
            "1–5 / Q-E  cambia tipo di boccia",
            "Mouse / ←→  mira",
            "Rotella / ↑↓  potenza",
            "Click / SPAZIO  lancia",
            "J  sposta il jack",
            "X  pulisci le bocce",
            "R  azzera allenamento",
            "ESC  torna al menu",
        )
        for line in controls:
            surface = self.font_small.render(
                line,
                True,
                tuple(self.colors["text_secondary"]),
            )
            self.screen.blit(surface, (x, y))
            y += 25

    def _panel(self, x: int, y: int, width: int, height: int) -> None:
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["panel"]),
            rect,
            border_radius=12,
        )
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["panel_border"]),
            rect,
            1,
            border_radius=12,
        )

    def _row(self, x: int, y: int, label: str, value: str) -> None:
        left = self.font.render(
            label,
            True,
            tuple(self.colors["text_secondary"]),
        )
        right = self.font.render(
            value,
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(left, (x, y))
        self.screen.blit(right, (x + 190, y))

    @staticmethod
    def _distance_text(value: float | None) -> str:
        return "—" if value is None else f"{value:.2f} m"
