from __future__ import annotations

import math
from typing import Any

import pygame

from game.boccia import Boccia
from game.field import Field
from game.jack import Jack
from game.physics import PhysicsEngine


class GameScreen:
    READY = "ready"
    ROLLING = "rolling"
    STOPPED = "stopped"

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.window = settings["window"]
        self.gameplay = settings["gameplay"]
        self.physics_settings = settings["physics"]
        self.colors = settings["colors"]

        self.font_title = pygame.font.SysFont("arial", 34, bold=True)
        self.font_big = pygame.font.SysFont("arial", 26, bold=True)
        self.font = pygame.font.SysFont("arial", 20)
        self.font_small = pygame.font.SysFont("arial", 16)

        field_cfg = settings["field"]
        field_rect = pygame.Rect(
            field_cfg["x"],
            field_cfg["y"],
            field_cfg["width"],
            field_cfg["height"],
        )
        self.field = Field(field_rect)

        self.ball = Boccia(
            self.field.launch_point,
            radius=self.gameplay["boccia_radius"],
            color=tuple(self.colors["player_ball"]),
        )
        self.jack = Jack(
            self.field.jack_default_position,
            radius=self.gameplay["jack_radius"],
        )

        self.physics = PhysicsEngine(
            friction_deceleration=self.physics_settings["friction_deceleration"],
            border_restitution=self.physics_settings["border_restitution"],
            border_tangent_damping=self.physics_settings["border_tangent_damping"],
            stop_speed=self.physics_settings["stop_speed"],
        )

        self.angle = 0.0
        self.power = 55.0
        self.state = self.READY
        self.last_distance_m: float | None = None
        self.border_hits = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._launch()
            elif event.key == pygame.K_r:
                self._reset_shot()
            elif event.key == pygame.K_c:
                self.angle = 0.0
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._change_angle(-self.gameplay["angle_step"])
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._change_angle(self.gameplay["angle_step"])
            elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self._change_power(self.gameplay["power_step"])
            elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_MINUS, pygame.K_KP_MINUS):
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

        if self.state == self.ROLLING:
            hit = self.physics.step_ball(self.ball, dt, self.field.playable_bounds)
            if hit:
                self.border_hits += 1

            if not self.ball.is_moving:
                self.state = self.STOPPED
                self.last_distance_m = self._distance_to_jack_meters()

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        self.field.draw(self.screen)
        self.jack.draw(self.screen)

        if self.state == self.READY:
            self._draw_aim_indicator()

        self.ball.draw(self.screen)
        self._draw_hud()

    def _continuous_keyboard_input(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        angle_speed = self.gameplay["angle_keyboard_speed"]
        power_speed = self.gameplay["power_keyboard_speed"]

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._change_angle(-angle_speed * dt)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._change_angle(angle_speed * dt)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._change_power(power_speed * dt)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._change_power(-power_speed * dt)

    def _aim_at_mouse(self, mouse_pos: tuple[int, int]) -> None:
        mx, my = mouse_pos
        vector = pygame.Vector2(mx, my) - self.field.launch_point

        # Non ha senso mirare dietro al giocatore: se il mouse è troppo in basso,
        # manteniamo comunque un tiro verso il campo.
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
        minimum = self.gameplay["min_power"]
        maximum = self.gameplay["max_power"]
        self.power = max(minimum, min(maximum, self.power + amount))

    def _launch(self) -> None:
        if self.state != self.READY:
            return

        self.ball.launch(
            angle_degrees=self.angle,
            power_percent=self.power,
            min_speed=self.gameplay["min_launch_speed"],
            max_speed=self.gameplay["max_launch_speed"],
        )
        self.state = self.ROLLING
        self.last_distance_m = None
        self.border_hits = 0

    def _reset_shot(self) -> None:
        self.ball.reset(self.field.launch_point)
        self.state = self.READY
        self.last_distance_m = None
        self.border_hits = 0

    def _distance_to_jack_meters(self) -> float:
        pixels = self.ball.position.distance_to(self.jack.position)
        pixels_per_meter = self.field.rect.height / self.gameplay["virtual_field_length_m"]
        return pixels / pixels_per_meter

    def _draw_aim_indicator(self) -> None:
        angle_radians = math.radians(self.angle)
        direction = pygame.Vector2(math.sin(angle_radians), -math.cos(angle_radians))

        start = self.field.launch_point
        length = 95 + (self.power / 100.0) * 155
        end = start + direction * length

        pygame.draw.line(
            self.screen,
            tuple(self.colors["aim"]),
            start,
            end,
            4,
        )

        # Punta della freccia
        side = pygame.Vector2(-direction.y, direction.x)
        tip = end
        left = end - direction * 18 + side * 10
        right = end - direction * 18 - side * 10
        pygame.draw.polygon(self.screen, tuple(self.colors["aim"]), [tip, left, right])

        # Cerchio trasparente attorno alla boccia per comunicare che è selezionata
        pygame.draw.circle(
            self.screen,
            tuple(self.colors["aim_soft"]),
            (round(start.x), round(start.y)),
            self.ball.radius + 9,
            2,
        )

    def _draw_hud(self) -> None:
        x = self.field.rect.right + 48
        y = 42
        width = self.window["width"] - x - 44

        title = self.font_title.render("BOCCIA BATTLE", True, tuple(self.colors["text_primary"]))
        self.screen.blit(title, (x, y))
        y += 48

        version = self.font_small.render("PROTOTIPO 0.1 • FISICA DEL TIRO", True, tuple(self.colors["accent"]))
        self.screen.blit(version, (x, y))
        y += 44

        status_label = {
            self.READY: "PREPARA IL TIRO",
            self.ROLLING: "BOCCIA IN MOVIMENTO",
            self.STOPPED: "TIRO COMPLETATO",
        }[self.state]
        self._draw_panel(x, y, width, 76)
        status = self.font_big.render(status_label, True, tuple(self.colors["text_primary"]))
        self.screen.blit(status, (x + 18, y + 13))
        hint = self.font_small.render(self._status_hint(), True, tuple(self.colors["text_secondary"]))
        self.screen.blit(hint, (x + 18, y + 45))
        y += 94

        self._draw_panel(x, y, width, 174)
        self._draw_value_row(x + 18, y + 16, "Direzione", f"{self.angle:+.1f}°")
        self._draw_value_row(x + 18, y + 50, "Potenza", f"{self.power:.0f}%")
        self._draw_power_bar(x + 18, y + 88, width - 36)
        self._draw_value_row(x + 18, y + 126, "Velocità", f"{self.ball.speed:.0f} px/s")
        y += 194

        self._draw_panel(x, y, width, 116)
        distance_text = "—" if self.last_distance_m is None else f"{self.last_distance_m:.2f} m"
        self._draw_value_row(x + 18, y + 18, "Distanza dal jack", distance_text)
        self._draw_value_row(x + 18, y + 52, "Urti col bordo", str(self.border_hits))
        physics_text = f"Attrito {self.physics_settings['friction_deceleration']:.0f} px/s²"
        physics = self.font_small.render(physics_text, True, tuple(self.colors["text_secondary"]))
        self.screen.blit(physics, (x + 18, y + 84))
        y += 136

        controls = [
            "MOUSE  muovi per mirare • rotella = potenza",
            "CLICK SX  lancia   •   CLICK DX  centra",
            "← → / A D  direzione",
            "↑ ↓ / W S  potenza",
            "SPAZIO / INVIO  lancia",
            "R  rimetti la boccia alla partenza",
            "ESC  esci",
        ]
        heading = self.font_big.render("CONTROLLI", True, tuple(self.colors["text_primary"]))
        self.screen.blit(heading, (x, y))
        y += 38
        for line in controls:
            text = self.font_small.render(line, True, tuple(self.colors["text_secondary"]))
            self.screen.blit(text, (x, y))
            y += 25

        footer = self.font_small.render(
            "0.2: più bocce + collisioni + jack fisico",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(footer, (x, self.window["height"] - 42))

    def _status_hint(self) -> str:
        if self.state == self.READY:
            return "Mira, regola la potenza e lancia."
        if self.state == self.ROLLING:
            return "Osserva attrito e rimbalzi sui bordi."
        return "Premi R per provare un altro tiro."

    def _draw_panel(self, x: int, y: int, width: int, height: int) -> None:
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, tuple(self.colors["panel"]), rect, border_radius=12)
        pygame.draw.rect(self.screen, tuple(self.colors["panel_border"]), rect, 1, border_radius=12)

    def _draw_value_row(self, x: int, y: int, label: str, value: str) -> None:
        label_surface = self.font.render(label, True, tuple(self.colors["text_secondary"]))
        value_surface = self.font.render(value, True, tuple(self.colors["text_primary"]))
        self.screen.blit(label_surface, (x, y))
        self.screen.blit(value_surface, (x + 190, y))

    def _draw_power_bar(self, x: int, y: int, width: int) -> None:
        height = 18
        background = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (34, 41, 49), background, border_radius=8)

        fraction = self.power / 100.0
        fill_width = max(4, round(width * fraction))
        fill = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(self.screen, tuple(self.colors["power"]), fill, border_radius=8)
        pygame.draw.rect(self.screen, tuple(self.colors["panel_border"]), background, 1, border_radius=8)
