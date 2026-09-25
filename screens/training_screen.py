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
from game.training_drills import TRAINING_DRILLS, get_drill


class TrainingScreen:
    """Structured training using the same physics and official court."""

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
            solver_iterations=self.physics_settings.get(
                "solver_iterations",
                6,
            ),
            boundary_mode="open",
        )

        self.font_title = pygame.font.SysFont("arial", 34, bold=True)
        self.font_big = pygame.font.SysFont("arial", 21, bold=True)
        self.font = pygame.font.SysFont("arial", 17)
        self.font_small = pygame.font.SysFont("arial", 13)

        self.random = random.Random()
        self.selected_boccia_type = self.gameplay.get(
            "selected_boccia_type",
            "medie",
        )
        self.selected_brand = self.gameplay.get(
            "selected_brand",
            "handi_life_sport",
        )
        self.aim_mode = self.gameplay.get("aim_mode", "target")
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

        self.drill_index = 0
        self.drill_attempts = 0
        self.drill_successes = 0
        self.drill_message = "Seleziona un esercizio con TAB o F1–F7."
        self.shot_ball_collisions = 0
        self.shot_jack_hits = 0
        self.target_ball: Boccia | None = None
        self.target_ball_start: pygame.Vector2 | None = None
        self.corridor_rect: pygame.Rect | None = None

        self.jack = self._new_jack()
        self._setup_drill(reset_score=True)

    @property
    def drill(self):
        return get_drill(self.drill_index)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.state == self.READY:
                self._change_drill(1)
                return

            function_keys = (
                pygame.K_F1,
                pygame.K_F2,
                pygame.K_F3,
                pygame.K_F4,
                pygame.K_F5,
                pygame.K_F6,
                pygame.K_F7,
            )
            if event.key in function_keys and self.state == self.READY:
                self.drill_index = function_keys.index(event.key)
                self._setup_drill(reset_score=True)
                return

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._launch()
            elif event.key == pygame.K_r:
                self._setup_drill(reset_score=True)
            elif event.key == pygame.K_x and self.state == self.READY:
                self._setup_drill(reset_score=False)
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
        self.shot_ball_collisions += report.ball_collisions
        self.shot_jack_hits += report.jack_hits

        for ball in list(self.balls):
            if self.field.touches_exterior_boundary(ball):
                ball.velocity.update(0, 0)
                self.balls.remove(ball)

        if self.field.touches_exterior_boundary(self.jack):
            self.jack.position = self.field.cross_position.copy()
            self.jack.velocity.update(0, 0)

        if not self.physics.is_settled(self.balls, self.jack):
            return

        if (
            self.last_thrown_ball is not None
            and self.last_thrown_ball in self.balls
        ):
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
        else:
            self.last_distance_m = None

        self._evaluate_drill()
        self.state = self.READY
        self._prepare_ball()

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        self.field.draw(self.screen)
        self._draw_training_rings()
        self._draw_drill_guides()

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
            removable = [
                ball for ball in self.balls
                if ball is not self.target_ball
            ]
            if removable:
                self.balls.remove(removable[0])

        self.last_thrown_ball = self.active_ball
        self.active_ball = None
        self.throws += 1
        self.drill_attempts += 1
        self.shot_ball_collisions = 0
        self.shot_jack_hits = 0
        self.drill_message = "Tiro in corso…"
        self.state = self.ROLLING

    def _setup_drill(self, reset_score: bool) -> None:
        self.balls.clear()
        self.jack = self._new_jack()
        self.last_thrown_ball = None
        self.last_distance_m = None
        self.target_ball = None
        self.target_ball_start = None
        self.corridor_rect = None
        self.angle = 0.0
        self.power = 55.0
        self.state = self.READY

        if reset_score:
            self.drill_attempts = 0
            self.drill_successes = 0
            self.best_distance_m = None

        key = self.drill.key

        if key in {"approach25", "approach50"}:
            self._randomize_jack(prepare=False)

        elif key == "hit":
            self.jack.position = self.field.cross_position.copy()
            offset = self.field.px_per_meter_y * 0.55
            self.target_ball = self._static_ball(
                pygame.Vector2(
                    self.field.cross_position.x,
                    self.field.cross_position.y + offset,
                ),
                "blue",
            )
            self.target_ball_start = self.target_ball.position.copy()
            self.balls.append(self.target_ball)

        elif key == "cluster":
            self.jack.position = self.field.cross_position.copy()
            offsets = (
                (-8, 10, "blue"),
                (8, 10, "red"),
                (-7, -6, "red"),
                (7, -6, "blue"),
            )
            for dx, dy, owner in offsets:
                self.balls.append(
                    self._static_ball(
                        self.jack.position + pygame.Vector2(dx, dy),
                        owner,
                    )
                )

        elif key == "corridor":
            self._randomize_jack(prepare=False)
            corridor_width = self.field.px_per_meter_x * 0.85
            left = self.field.rect.centerx - corridor_width / 2.0
            top = self.field.rect.top + self.field.px_per_meter_y * 1.0
            bottom = self.field.throwing_line_y - self.field.px_per_meter_y * 0.25
            self.corridor_rect = pygame.Rect(
                round(left),
                round(top),
                round(corridor_width),
                round(bottom - top),
            )

        elif key == "penalty":
            self.jack.position = self.field.cross_position.copy()

        self.drill_message = self.drill.success_hint
        self._prepare_ball()

    def _static_ball(
        self,
        position: pygame.Vector2,
        owner: str,
    ) -> Boccia:
        color = (
            tuple(self.colors["red_ball"])
            if owner == "red"
            else tuple(self.colors["blue_ball"])
        )
        return Boccia(
            position,
            radius=self.gameplay["boccia_radius"],
            color=color,
            owner_key=owner,
            mass=self.gameplay["boccia_mass"],
            boccia_type="medie",
        )

    def _evaluate_drill(self) -> None:
        key = self.drill.key
        ball = self.last_thrown_ball
        success = False

        if key == "free":
            self.drill_message = "Tiro registrato. Prova una nuova soluzione."
            return

        if ball is None or ball not in self.balls:
            self.drill_message = "FUORI CAMPO • Riprova."
            return

        distance_cm = (
            ball.position.distance_to(self.jack.position)
            / self.field.rect.height
            * self.field.COURT_LENGTH_M
            * 100.0
        )

        if key == "approach25":
            success = distance_cm <= 25.0
        elif key == "approach50":
            success = distance_cm <= 50.0
        elif key == "hit":
            success = self.shot_ball_collisions > 0
        elif key == "cluster":
            success = (
                self.shot_ball_collisions > 0
                and distance_cm <= 50.0
            )
        elif key == "corridor":
            success = (
                self.corridor_rect is not None
                and self.corridor_rect.collidepoint(ball.position)
                and distance_cm <= 50.0
            )
        elif key == "penalty":
            success = self.field.ball_scores_penalty(ball)

        if success:
            self.drill_successes += 1
            self.drill_message = "SUCCESSO ✓"
        else:
            self.drill_message = "NON RIUSCITO • Riprova."

    def _change_drill(self, direction: int) -> None:
        self.drill_index = (
            self.drill_index + direction
        ) % len(TRAINING_DRILLS)
        self._setup_drill(reset_score=True)

    def _randomize_jack(self, prepare: bool = True) -> None:
        margin_x = self.field.px_per_meter_x * 0.7
        x = self.random.uniform(
            self.field.rect.left + margin_x,
            self.field.rect.right - margin_x,
        )

        min_y = self.field.rect.top + self.field.px_per_meter_y * 2.0
        max_y = self.field.v_line_y_at_x(x) - self.field.px_per_meter_y * 0.5
        y = self.random.uniform(min_y, max(min_y + 1, max_y))

        self.jack.position.update(x, y)
        self.jack.velocity.update(0, 0)
        self.last_distance_m = None
        if prepare:
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
        target = pygame.Vector2(mouse_pos)
        vector = target - self.field.launch_point
        if vector.length_squared() < 4:
            return

        angle = math.degrees(math.atan2(vector.x, -vector.y))
        limit = self.gameplay["max_aim_angle"]
        self.angle = max(-limit, min(limit, angle))

        if self.aim_mode == "target":
            profile = get_boccia_profile(self.selected_boccia_type)
            friction = (
                self.physics_settings["friction_deceleration"]
                * profile.friction_multiplier
            )
            required_speed = math.sqrt(
                max(0.0, 2.0 * friction * vector.length())
            )
            min_speed = self.gameplay["min_launch_speed"]
            max_speed = self.gameplay["max_launch_speed"]
            normalized = (
                (required_speed - min_speed)
                / max(1.0, max_speed - min_speed)
            )
            self.power = max(
                self.gameplay["min_power"],
                min(
                    self.gameplay["max_power"],
                    normalized * 100.0,
                ),
            )

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
        return (
            pixels
            / self.field.rect.height
            * self.field.COURT_LENGTH_M
        )

    def _draw_training_rings(self) -> None:
        center = (
            round(self.jack.position.x),
            round(self.jack.position.y),
        )
        for meters in (0.25, 0.50, 1.0):
            radius = round(self.field.px_per_meter_y * meters)
            pygame.draw.circle(
                self.screen,
                (220, 230, 225),
                center,
                radius,
                1,
            )

    def _draw_drill_guides(self) -> None:
        if self.corridor_rect is not None:
            pygame.draw.rect(
                self.screen,
                tuple(self.colors["aim_soft"]),
                self.corridor_rect,
                2,
            )

        if self.drill.key == "penalty":
            pygame.draw.rect(
                self.screen,
                tuple(self.colors["accent"]),
                self.field.target_box_rect,
                2,
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
        y = 28
        width = self.window["width"] - x - 38

        title = self.font_title.render(
            "ALLENAMENTO AVANZATO",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (x, y))
        y += 46

        self._panel(x, y, width, 112)
        self._row(x + 16, y + 10, "Esercizio", self.drill.name)
        description = self.font_small.render(
            self.drill.description[:54],
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(description, (x + 16, y + 42))
        message = self.font.render(
            self.drill_message[:42],
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(message, (x + 16, y + 72))
        y += 124

        attempts = max(1, self.drill_attempts)
        rate = (
            0.0
            if self.drill_attempts == 0
            else self.drill_successes / attempts * 100.0
        )
        self._panel(x, y, width, 105)
        self._row(x + 16, y + 10, "Tentativi", str(self.drill_attempts))
        self._row(x + 16, y + 40, "Successi", str(self.drill_successes))
        self._row(x + 16, y + 70, "Percentuale", f"{rate:.1f}%")
        y += 117

        brand = get_brand(self.selected_brand)
        profile = get_boccia_profile(self.selected_boccia_type)
        self._panel(x, y, width, 135)
        self._row(x + 16, y + 10, "Marca", brand.display_name)
        self._row(x + 16, y + 40, "Boccia", profile.label)
        self._row(x + 16, y + 70, "Potenza", f"{self.power:.0f}%")
        self._row(x + 16, y + 100, "Direzione", f"{self.angle:+.1f}°")
        y += 147

        self._panel(x, y, width, 105)
        self._row(
            x + 16,
            y + 10,
            "Ultimo",
            self._distance_text(self.last_distance_m),
        )
        self._row(
            x + 16,
            y + 40,
            "Migliore",
            self._distance_text(self.best_distance_m),
        )
        self._row(
            x + 16,
            y + 70,
            "Collisioni tiro",
            str(self.shot_ball_collisions),
        )
        y += 119

        controls = (
            "TAB / F1–F7  cambia esercizio",
            "Mouse / ←→  mira • rotella / ↑↓ potenza",
            "SPAZIO  lancia • 1–5 / Q-E durezza",
            "J jack casuale • X reset campo • R reset punteggio",
            "ESC torna al menu",
        )
        for line in controls:
            surface = self.font_small.render(
                line,
                True,
                tuple(self.colors["text_secondary"]),
            )
            self.screen.blit(surface, (x, y))
            y += 23

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
        self.screen.blit(right, (x + 170, y))

    @staticmethod
    def _distance_text(value: float | None) -> str:
        return "—" if value is None else f"{value:.2f} m"
