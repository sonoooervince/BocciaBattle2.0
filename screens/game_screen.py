from __future__ import annotations

import math
from typing import Any

import pygame

from game.boccia import Boccia
from game.field import Field
from game.jack import Jack
from game.match import MatchController
from game.physics import PhysicsEngine
from screens.result_screen import ResultScreen


class GameScreen:
    READY = "ready"
    ROLLING = "rolling"
    END_RESULT = "end_result"
    MATCH_RESULT = "match_result"

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.window = settings["window"]
        self.gameplay = settings["gameplay"]
        self.physics_settings = settings["physics"]
        self.match_settings = settings["match"]
        self.colors = settings["colors"]

        self.font_title = pygame.font.SysFont("arial", 34, bold=True)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)
        self.font = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)

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

        self.results = ResultScreen(screen, self.colors)
        self.match = self._new_match_controller()

        self.angle = 0.0
        self.power = 55.0
        self.active_ball: Boccia | None = None
        self.state = self.READY
        self.border_hits = 0
        self.ball_collisions = 0
        self.jack_hits = 0
        self.jack = self._new_jack()

        self._prepare_turn()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._restart_match()
                return

            if self.state == self.END_RESULT:
                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_n,
                ):
                    self._advance_end()
                return

            if self.state == self.MATCH_RESULT:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._restart_match()
                return

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._launch()
            elif event.key == pygame.K_c:
                self.angle = 0.0
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._change_angle(-self.gameplay["angle_step"])
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._change_angle(self.gameplay["angle_step"])
            elif event.key in (
                pygame.K_UP,
                pygame.K_w,
                pygame.K_EQUALS,
                pygame.K_KP_PLUS,
            ):
                self._change_power(self.gameplay["power_step"])
            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s,
                pygame.K_MINUS,
                pygame.K_KP_MINUS,
            ):
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

        if self.state != self.ROLLING:
            return

        report = self.physics.step(
            self.match.all_balls,
            self.jack,
            dt,
            self.field.playable_bounds,
        )
        self.border_hits += report.border_hits
        self.ball_collisions += report.ball_collisions
        self.jack_hits += report.jack_hits

        if not self.physics.is_settled(self.match.all_balls, self.jack):
            return

        self.active_ball = None
        next_key = self.match.choose_next_turn(self.jack.position)

        if next_key is not None:
            self.state = self.READY
            self._prepare_turn()
            return

        self.match.finish_end(self.jack.position)
        self.state = (
            self.MATCH_RESULT
            if self.match.match_over
            else self.END_RESULT
        )

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        self.field.draw(self.screen)
        self._draw_best_distance_lines()

        for ball in self.match.all_balls:
            ball.draw(self.screen)

        self.jack.draw(self.screen)

        if self.state == self.READY and self.active_ball is not None:
            self._draw_aim_indicator()
            self.active_ball.draw(self.screen, selected=True)

        self._draw_hud()

        if self.state == self.END_RESULT and self.match.last_end_score is not None:
            winner_name = (
                self.match.player(self.match.last_end_score.winner).name
                if self.match.last_end_score.winner is not None
                else None
            )
            self.results.draw_end_result(
                end_number=self.match.current_end,
                score=self.match.last_end_score,
                total_scores=self.match.total_scores,
                winner_name=winner_name,
                is_tiebreak=self.match.is_tiebreak,
            )

        elif self.state == self.MATCH_RESULT:
            winner_key = self.match.winner
            if winner_key is not None:
                self.results.draw_match_result(
                    total_scores=self.match.total_scores,
                    winner_name=self.match.player(winner_key).name,
                    total_ends=self.match.current_end,
                )

    def _new_match_controller(self) -> MatchController:
        return MatchController(
            balls_per_player=self.gameplay["balls_per_player"],
            red_color=tuple(self.colors["red_ball"]),
            blue_color=tuple(self.colors["blue_ball"]),
            max_ends=self.match_settings["ends"],
            tie_tolerance_px=self.match_settings["tie_tolerance_px"],
        )

    def _new_jack(self) -> Jack:
        return Jack(
            self.field.jack_default_position,
            radius=self.gameplay["jack_radius"],
            mass=self.gameplay["jack_mass"],
        )

    def _restart_match(self) -> None:
        self.match = self._new_match_controller()
        self.jack = self._new_jack()
        self.state = self.READY
        self._reset_end_counters()
        self._prepare_turn()

    def _advance_end(self) -> None:
        self.match.advance_end()
        self.jack = self._new_jack()
        self.state = self.READY
        self._reset_end_counters()
        self._prepare_turn()

    def _reset_end_counters(self) -> None:
        self.border_hits = 0
        self.ball_collisions = 0
        self.jack_hits = 0

    def _prepare_turn(self) -> None:
        player = self.match.current_player
        if player is None:
            self.active_ball = None
            return

        self.angle = 0.0
        self.power = 55.0
        self.active_ball = Boccia(
            self.field.launch_point,
            radius=self.gameplay["boccia_radius"],
            color=player.color,
            owner_key=player.key,
            mass=self.gameplay["boccia_mass"],
        )

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
        minimum = self.gameplay["min_power"]
        maximum = self.gameplay["max_power"]
        self.power = max(minimum, min(maximum, self.power + amount))

    def _launch(self) -> None:
        if self.state != self.READY or self.active_ball is None:
            return

        self.active_ball.launch(
            angle_degrees=self.angle,
            power_percent=self.power,
            min_speed=self.gameplay["min_launch_speed"],
            max_speed=self.gameplay["max_launch_speed"],
        )
        self.match.register_throw(self.active_ball)
        self.state = self.ROLLING

    def _pixels_to_meters(self, pixels: float) -> float:
        pixels_per_meter = (
            self.field.rect.height / self.gameplay["virtual_field_length_m"]
        )
        return pixels / pixels_per_meter

    def _best_distance_meters(self, key: str) -> float | None:
        distance = self.match.best_distance(key, self.jack.position)
        if distance is None:
            return None
        return self._pixels_to_meters(distance)

    def _draw_best_distance_lines(self) -> None:
        for key in self.match.PLAYER_ORDER:
            ball = self.match.best_ball(key, self.jack.position)
            if ball is None:
                continue

            color = self.match.player(key).color
            line_color = tuple(min(255, channel + 35) for channel in color)
            pygame.draw.line(
                self.screen,
                line_color,
                ball.position,
                self.jack.position,
                2,
            )

    def _draw_aim_indicator(self) -> None:
        angle_radians = math.radians(self.angle)
        direction = pygame.Vector2(
            math.sin(angle_radians),
            -math.cos(angle_radians),
        )

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

        side = pygame.Vector2(-direction.y, direction.x)
        tip = end
        left = end - direction * 18 + side * 10
        right = end - direction * 18 - side * 10
        pygame.draw.polygon(
            self.screen,
            tuple(self.colors["aim"]),
            [tip, left, right],
        )

    def _draw_hud(self) -> None:
        x = self.field.rect.right + 42
        y = 30
        width = self.window["width"] - x - 38

        title = self.font_title.render(
            "BOCCIA BATTLE",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (x, y))
        y += 43

        version = self.font_small.render(
            "VERSIONE 0.3 • PARTITA ED END",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(version, (x, y))
        y += 34

        self._draw_panel(x, y, width, 74)
        status = self.font_big.render(
            self._status_label(),
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(status, (x + 18, y + 10))
        hint = self.font_small.render(
            self._status_hint(),
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(hint, (x + 18, y + 43))
        y += 88

        self._draw_panel(x, y, width, 96)
        end_text = (
            f"TIE-BREAK {self.match.current_end - self.match.max_ends}"
            if self.match.is_tiebreak
            else f"{self.match.current_end} / {self.match.max_ends}"
        )
        self._draw_value_row(x + 18, y + 12, "End", end_text)
        self._draw_value_row(
            x + 18,
            y + 46,
            "Punteggio",
            (
                f"ROSSO {self.match.total_scores['red']}  -  "
                f"{self.match.total_scores['blue']} BLU"
            ),
        )
        y += 110

        self._draw_panel(x, y, width, 112)
        current = self.match.current_player
        turn_text = "—" if current is None else current.name
        self._draw_value_row(x + 18, y + 11, "Turno", turn_text)

        red = self.match.player("red")
        blue = self.match.player("blue")
        self._draw_team_row(x + 18, y + 44, red)
        self._draw_team_row(x + 18, y + 76, blue)
        y += 126

        self._draw_panel(x, y, width, 126)
        self._draw_value_row(
            x + 18,
            y + 10,
            "Direzione",
            f"{self.angle:+.1f}°" if self.state == self.READY else "—",
        )
        self._draw_value_row(
            x + 18,
            y + 40,
            "Potenza",
            f"{self.power:.0f}%" if self.state == self.READY else "—",
        )
        self._draw_power_bar(x + 18, y + 72, width - 36)
        moving_speed = max(
            [ball.speed for ball in self.match.all_balls] + [self.jack.speed],
            default=0.0,
        )
        self._draw_value_row(
            x + 18,
            y + 96,
            "Velocità max",
            f"{moving_speed:.0f} px/s",
        )
        y += 140

        self._draw_panel(x, y, width, 132)
        self._draw_value_row(
            x + 18,
            y + 10,
            "Migliore rosso",
            self._format_distance(self._best_distance_meters("red")),
        )
        self._draw_value_row(
            x + 18,
            y + 40,
            "Migliore blu",
            self._format_distance(self._best_distance_meters("blue")),
        )
        self._draw_value_row(
            x + 18,
            y + 70,
            "Più vicino",
            self._leader_text(),
        )
        debug = (
            f"Collisioni {self.ball_collisions}  •  "
            f"jack {self.jack_hits}  •  bordo {self.border_hits}"
        )
        self.screen.blit(
            self.font_small.render(
                debug,
                True,
                tuple(self.colors["text_secondary"]),
            ),
            (x + 18, y + 104),
        )

        controls = self.font_small.render(
            "Mira: mouse/←→  •  Potenza: rotella/↑↓  •  Lancia: click/SPA ZIO",
            True,
            tuple(self.colors["text_secondary"]),
        )
        # Evitiamo dipendenze grafiche esterne: il testo è intenzionalmente semplice.
        self.screen.blit(controls, (x, self.window["height"] - 48))

        footer = self.font_small.render(
            "C = centra  •  R = nuova partita  •  ESC = esci",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(footer, (x, self.window["height"] - 26))

    def _status_label(self) -> str:
        if self.state == self.READY:
            return "PREPARA IL TIRO"
        if self.state == self.ROLLING:
            return "BOCCE IN MOVIMENTO"
        if self.state == self.END_RESULT:
            return "END COMPLETATO"
        return "PARTITA TERMINATA"

    def _status_hint(self) -> str:
        if self.state == self.READY:
            current = self.match.current_player
            name = "giocatore" if current is None else current.name
            return f"{name}: mira, regola la potenza e lancia."
        if self.state == self.ROLLING:
            return "Ogni collisione può cambiare punteggio e turno."
        if self.state == self.END_RESULT:
            return "Controlla il punteggio dell'end."
        return "La partita è conclusa."

    def _leader_text(self) -> str:
        leader = self.match.leader(self.jack.position)
        if leader is None:
            return "—"
        if leader == "tie":
            return "PARITÀ"
        return self.match.player(leader).name

    def _format_distance(self, value: float | None) -> str:
        if value is None:
            return "—"
        return f"{value:.2f} m"

    def _draw_team_row(self, x: int, y: int, player: Any) -> None:
        pygame.draw.circle(self.screen, player.color, (x + 8, y + 9), 8)
        label = self.font.render(
            player.name,
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(label, (x + 24, y - 2))

        value = self.font.render(
            f"{player.remaining} rimaste",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(value, (x + 200, y - 2))

    def _draw_panel(self, x: int, y: int, width: int, height: int) -> None:
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

    def _draw_value_row(
        self,
        x: int,
        y: int,
        label: str,
        value: str,
    ) -> None:
        label_surface = self.font.render(
            label,
            True,
            tuple(self.colors["text_secondary"]),
        )
        value_surface = self.font.render(
            value,
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(label_surface, (x, y))
        self.screen.blit(value_surface, (x + 190, y))

    def _draw_power_bar(self, x: int, y: int, width: int) -> None:
        height = 15
        background = pygame.Rect(x, y, width, height)
        pygame.draw.rect(
            self.screen,
            (34, 41, 49),
            background,
            border_radius=8,
        )

        fraction = self.power / 100.0 if self.state == self.READY else 0.0
        fill_width = max(0, round(width * fraction))
        if fill_width > 0:
            fill = pygame.Rect(x, y, fill_width, height)
            pygame.draw.rect(
                self.screen,
                tuple(self.colors["power"]),
                fill,
                border_radius=8,
            )

        pygame.draw.rect(
            self.screen,
            tuple(self.colors["panel_border"]),
            background,
            1,
            border_radius=8,
        )
