from __future__ import annotations

import math
import random
from typing import Any

import pygame

from game.ai import BocciaAI
from game.boccia import Boccia
from game.boccia_profiles import (
    BOCCIA_PROFILES,
    cycle_boccia_profile,
    get_boccia_profile,
)
from game.brands import get_brand
from game.field import Field
from game.jack import Jack
from game.match import MatchController
from game.official_rules import (
    BETWEEN_ENDS_SECONDS,
    RULES_VERSION,
    WARMUP_SECONDS,
    get_event_format,
    other_side,
)
from game.physics import PhysicsEngine
from screens.result_screen import ResultScreen


class GameScreen:
    WARMUP = "warmup"
    JACK_READY = "jack_ready"
    JACK_ROLLING = "jack_rolling"
    READY = "ready"
    ROLLING = "rolling"
    END_RESULT = "end_result"
    BETWEEN_ENDS = "between_ends"
    MATCH_RESULT = "match_result"
    AI_THINKING = "ai_thinking"
    AI_THINKING_JACK = "ai_thinking_jack"

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.window = settings["window"]
        self.gameplay = settings["gameplay"]
        self.physics_settings = settings["physics"]
        self.match_settings = settings["match"]
        self.colors = settings["colors"]
        self.random = random.Random()

        self.font_title = pygame.font.SysFont("arial", 30, bold=True)
        self.font_big = pygame.font.SysFont("arial", 21, bold=True)
        self.font = pygame.font.SysFont("arial", 17)
        self.font_small = pygame.font.SysFont("arial", 13)

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
            boundary_mode="open",
        )
        self.results = ResultScreen(screen, self.colors)

        self.sport_class = self.gameplay.get("sport_class", "BC2")
        self.event_format = get_event_format("individual", self.sport_class)

        self.coin_toss_winner = self.random.choice(("human", "computer"))
        # Strategy choice: whoever wins the toss chooses red.
        self.human_key = (
            "red" if self.coin_toss_winner == "human" else "blue"
        )
        self.ai_key = other_side(self.human_key)
        self.coin_toss_text = (
            "TU hai vinto il sorteggio e scelto ROSSO"
            if self.coin_toss_winner == "human"
            else "COMPUTER ha vinto il sorteggio e scelto ROSSO"
        )

        self.match = self._new_match_controller()
        self.ai = BocciaAI(
            min_speed=self.gameplay["min_launch_speed"],
            max_speed=self.gameplay["max_launch_speed"],
            friction_deceleration=self.physics_settings["friction_deceleration"],
            difficulty=self.gameplay.get("ai_difficulty", "normal"),
            level=self.gameplay.get("ai_level", 10),
        )

        self.selected_boccia_type = self.gameplay.get(
            "selected_boccia_type",
            "medie",
        )
        self.selected_brand = self.gameplay.get(
            "selected_brand",
            "handi_life_sport",
        )
        self.show_distance_guides = self.gameplay.get(
            "show_distance_guides",
            True,
        )

        self.angle = 0.0
        self.power = 55.0
        self.active_ball: Boccia | None = None
        self.last_launched_ball: Boccia | None = None
        self.jack = self._new_jack_at_cross()
        self.ai_think_timer = 0.0
        self.ai_plan = None
        self.state = self.WARMUP
        self.warmup_remaining = float(WARMUP_SECONDS)
        self.between_ends_remaining = 0.0
        self.referee_message = self.coin_toss_text
        self.ball_collisions = 0
        self.jack_hits = 0
        self.dead_ball_events = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            if self._human_can_aim():
                if event.type == pygame.MOUSEMOTION:
                    self._aim_at_mouse(event.pos)
                elif event.type == pygame.MOUSEWHEEL:
                    self._change_power(
                        event.y * self.gameplay["power_step"]
                    )
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if (
                        event.button == 1
                        and self.field.rect.collidepoint(event.pos)
                    ):
                        self._aim_at_mouse(event.pos)
                        self._launch_human()
                    elif event.button == 3:
                        self.angle = 0.0
            return

        if event.key == pygame.K_r and self.state != self.WARMUP:
            self._restart_match()
            return

        if self.state == self.WARMUP:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_match_after_warmup()
            return

        if self.state == self.END_RESULT:
            if event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_n,
            ):
                self._prepare_next_end_interval()
            return

        if self.state == self.BETWEEN_ENDS:
            if event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_n,
            ):
                self._start_current_end()
            return

        if self.state == self.MATCH_RESULT:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._restart_match()
            return

        if not self._human_can_aim():
            return

        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._launch_human()
        elif event.key == pygame.K_p and self.state == self.READY:
            self._pass_remaining_human_balls()
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
        elif event.key == pygame.K_c:
            self.angle = 0.0
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._change_angle(-self.gameplay["angle_step"])
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._change_angle(self.gameplay["angle_step"])
        elif event.key in (pygame.K_UP, pygame.K_w):
            self._change_power(self.gameplay["power_step"])
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._change_power(-self.gameplay["power_step"])

    def update(self, dt: float) -> None:
        if self.state == self.WARMUP:
            self.warmup_remaining = max(
                0.0,
                self.warmup_remaining - dt,
            )
            if self.warmup_remaining <= 0.0:
                self._start_match_after_warmup()
            return

        if self.state == self.BETWEEN_ENDS:
            self.between_ends_remaining = max(
                0.0,
                self.between_ends_remaining - dt,
            )
            if self.between_ends_remaining <= 0.0:
                self._start_current_end()
            return

        self._consume_official_clock(dt)

        if self.state in (self.AI_THINKING, self.AI_THINKING_JACK):
            self.ai_think_timer -= dt
            if self.ai_think_timer <= 0.0:
                if self.state == self.AI_THINKING_JACK:
                    self._launch_ai_jack()
                else:
                    self._launch_ai_ball()
            return

        if self.state in (self.READY, self.JACK_READY):
            self._continuous_keyboard_input(dt)
            return

        if self.state == self.JACK_ROLLING:
            self._update_jack_roll(dt)
            return

        if self.state == self.ROLLING:
            self._update_coloured_roll(dt)

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        self.field.draw(self.screen)
        self._draw_best_distance_lines()

        for ball in self.match.all_balls:
            ball.draw(self.screen)

        if self.state != self.WARMUP:
            self.jack.draw(self.screen)

        if self._human_can_aim():
            self._draw_aim_indicator()
            if self.state == self.READY and self.active_ball is not None:
                self.active_ball.draw(self.screen, selected=True)

        self._draw_hud()

        if self.state == self.WARMUP:
            self.results.draw_message(
                "RISCALDAMENTO",
                "2 minuti regolamentari",
                self._clock(self.warmup_remaining),
                "INVIO quando entrambi i lati hanno finito",
            )
        elif (
            self.state == self.END_RESULT
            and self.match.last_end_score is not None
        ):
            self.results.draw_end_result(
                end_number=self.match.current_end,
                score=self.match.last_end_score,
                total_scores=self.match.total_scores,
                winner_name=None,
                is_tiebreak=self.match.is_tiebreak,
            )
        elif self.state == self.BETWEEN_ENDS:
            self.results.draw_message(
                "TRA GLI END",
                "Massimo un minuto",
                self._clock(self.between_ends_remaining),
                "INVIO quando sei pronto",
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
            balls_per_player=self.event_format.balls_per_side,
            red_color=tuple(self.colors["red_ball"]),
            blue_color=tuple(self.colors["blue_ball"]),
            max_ends=self.event_format.ends,
            tie_tolerance_px=self.match_settings["tie_tolerance_px"],
            red_name="TU" if self.human_key == "red" else "COMPUTER",
            blue_name="TU" if self.human_key == "blue" else "COMPUTER",
            seconds_per_side=self.event_format.seconds_per_side,
        )

    def _new_jack_at_cross(self) -> Jack:
        return Jack(
            self.field.cross_position,
            radius=self.gameplay["jack_radius"],
            mass=self.gameplay["jack_mass"],
        )

    def _new_jack_for_thrower(self, key: str) -> Jack:
        return Jack(
            self.field.launch_point_for(key),
            radius=self.gameplay["jack_radius"],
            mass=self.gameplay["jack_mass"],
        )

    def _restart_match(self) -> None:
        self.coin_toss_winner = self.random.choice(("human", "computer"))
        self.human_key = (
            "red" if self.coin_toss_winner == "human" else "blue"
        )
        self.ai_key = other_side(self.human_key)
        self.coin_toss_text = (
            "TU hai vinto il sorteggio e scelto ROSSO"
            if self.coin_toss_winner == "human"
            else "COMPUTER ha vinto il sorteggio e scelto ROSSO"
        )
        self.match = self._new_match_controller()
        self.jack = self._new_jack_at_cross()
        self.state = self.WARMUP
        self.warmup_remaining = float(WARMUP_SECONDS)
        self.referee_message = self.coin_toss_text
        self._reset_end_counters()

    def _start_match_after_warmup(self) -> None:
        self._start_current_end()

    def _start_current_end(self) -> None:
        self._reset_end_counters()
        self.angle = 0.0
        self.power = 55.0
        self.active_ball = None
        self.last_launched_ball = None
        self.ai_plan = None

        if self.match.is_tiebreak:
            self.jack = self._new_jack_at_cross()
            self.jack.has_entered_playing_area = True
            self.referee_message = (
                f"Tie-break: inizia {self.match.player(self.match.current_key).name}"
            )
            self._prepare_coloured_turn()
            return

        key = self.match.begin_jack()
        self.jack = self._new_jack_for_thrower(key)
        self.referee_message = (
            f"Jack a {self.match.player(key).name}"
        )
        self._prepare_jack_turn()

    def _prepare_next_end_interval(self) -> None:
        if self.match.match_over:
            self.state = self.MATCH_RESULT
            return
        first_tiebreak_key = None
        if self.match.needs_tiebreak:
            first_tiebreak_key = self.random.choice(("red", "blue"))
            self.referee_message = (
                f"Sorteggio tie-break: inizia "
                f"{self.match.player(first_tiebreak_key).name}"
            )
        self.match.advance_end(
            first_tiebreak_key=first_tiebreak_key,
        )
        self.between_ends_remaining = float(BETWEEN_ENDS_SECONDS)
        self.state = self.BETWEEN_ENDS

    def _prepare_jack_turn(self) -> None:
        key = self.match.current_key
        if key is None:
            return
        self.angle = 0.0
        self.power = 48.0
        self.active_ball = None
        if key == self.ai_key:
            self.ai_think_timer = self.gameplay.get("ai_think_time", 0.9)
            self.state = self.AI_THINKING_JACK
        else:
            self.state = self.JACK_READY

    def _prepare_coloured_turn(self) -> None:
        player = self.match.current_player
        if player is None:
            self._finish_end()
            return
        self.angle = 0.0
        self.power = 55.0
        self.active_ball = None
        self.ai_plan = None
        if player.key == self.ai_key:
            self.ai_think_timer = self.gameplay.get("ai_think_time", 0.9)
            self.state = self.AI_THINKING
            return
        self.state = self.READY
        self.active_ball = self._make_ball(player.key)

    def _make_ball(self, key: str, ai: bool = False) -> Boccia:
        player = self.match.player(key)
        return Boccia(
            self.field.launch_point_for(key),
            radius=self.gameplay["boccia_radius"],
            color=player.color,
            owner_key=key,
            mass=self.gameplay["boccia_mass"],
            boccia_type=(
                "medie" if ai else self.selected_boccia_type
            ),
        )

    def _launch_human(self) -> None:
        if self.match.current_key != self.human_key:
            return
        if self.state == self.JACK_READY:
            self.jack.launch(
                self.angle,
                self.power,
                self.gameplay["min_launch_speed"],
                self.gameplay["max_launch_speed"],
            )
            self.state = self.JACK_ROLLING
            return
        if self.state != self.READY or self.active_ball is None:
            return
        self._launch_coloured_ball(self.active_ball)

    def _launch_ai_jack(self) -> None:
        key = self.match.current_key
        if key != self.ai_key:
            return
        plan = self.ai.choose_jack_shot(
            self.field.launch_point_for(key),
            self.field.cross_position,
        )
        self.ai_plan = plan
        self.angle = plan.angle
        self.power = plan.power
        self.jack.launch(
            plan.angle,
            plan.power,
            self.gameplay["min_launch_speed"],
            self.gameplay["max_launch_speed"],
        )
        self.state = self.JACK_ROLLING

    def _launch_ai_ball(self) -> None:
        key = self.match.current_key
        if key != self.ai_key:
            return
        plan = self.ai.choose_shot_from_launch(
            self.match,
            self.jack,
            self.field.launch_point_for(key),
            side_key=key,
        )
        self.ai_plan = plan
        self.angle = plan.angle
        self.power = plan.power
        ball = self._make_ball(key, ai=True)
        ball.launch(
            plan.angle,
            plan.power,
            self.gameplay["min_launch_speed"],
            self.gameplay["max_launch_speed"],
        )
        self._register_launched_ball(ball)

    def _launch_coloured_ball(self, ball: Boccia) -> None:
        ball.launch(
            self.angle,
            self.power,
            self.gameplay["min_launch_speed"],
            self.gameplay["max_launch_speed"],
        )
        self._register_launched_ball(ball)

    def _register_launched_ball(self, ball: Boccia) -> None:
        self.match.register_throw(ball)
        self.last_launched_ball = ball
        self.active_ball = None
        self.state = self.ROLLING

    def _update_jack_roll(self, dt: float) -> None:
        key = self.match.current_key
        self.physics.step([], self.jack, dt, self.field.playable_bounds)
        if self.field.has_entered_playing_area(self.jack):
            self.jack.has_entered_playing_area = True

        if self.field.touches_exterior_boundary(self.jack):
            self._handle_fouled_jack("Jack fuori dal campo")
            return

        if self.jack.is_moving:
            return

        if self.field.is_valid_jack_position(self.jack):
            self.match.confirm_valid_jack()
            self.referee_message = "Jack valido"
            if key is not None and self.match.time_remaining[key] <= 0.0:
                self.match.expire_side_time(key)
            self._prepare_coloured_turn()
        else:
            self._handle_fouled_jack("Jack non oltre la V-line")

    def _handle_fouled_jack(self, reason: str) -> None:
        self.jack.velocity.update(0, 0)
        old_key = self.match.current_key
        next_key = self.match.foul_jack()
        self.referee_message = (
            f"{reason} • Jack passa a {self.match.player(next_key).name}"
        )
        if (
            old_key is not None
            and self.match.time_remaining[old_key] <= 0.0
        ):
            self.match.expire_side_time(old_key)

        if (
            self.match.player("red").remaining <= 0
            and self.match.player("blue").remaining <= 0
        ):
            self.jack = self._new_jack_at_cross()
            self.jack.has_entered_playing_area = True
            self.match.jack_valid = True
            self._finish_end()
            return

        self.jack = self._new_jack_for_thrower(next_key)
        self._prepare_jack_turn()

    def _update_coloured_roll(self, dt: float) -> None:
        thrower = self.match.last_throw_key
        report = self.physics.step(
            self.match.all_balls,
            self.jack,
            dt,
            self.field.playable_bounds,
        )
        self.ball_collisions += report.ball_collisions
        self.jack_hits += report.jack_hits

        for ball in list(self.match.all_balls):
            if self.field.has_entered_playing_area(ball):
                ball.has_entered_playing_area = True
            if self.field.touches_exterior_boundary(ball):
                ball.velocity.update(0, 0)
                self.match.mark_ball_dead(ball)
                self.dead_ball_events += 1
                if ball is self.last_launched_ball:
                    self.referee_message = "Dead ball: boccia fuori"

        if (
            self.field.touches_exterior_boundary(self.jack)
            or self.field.jack_is_in_non_valid_area(self.jack)
        ):
            self.jack.position = self.field.replacement_jack_position(
                self.match.all_balls,
                self.jack.radius,
            )
            self.jack.velocity.update(0, 0)
            self.jack.has_entered_playing_area = True
            self.referee_message = "Jack riposizionato sulla croce"

        if not self.physics.is_settled(self.match.all_balls, self.jack):
            return

        ball = self.last_launched_ball
        if ball is not None and ball in self.match.all_balls:
            if not ball.has_entered_playing_area:
                self.match.mark_ball_dead(ball)
                self.dead_ball_events += 1
                self.referee_message = "Dead ball: non entra nell'area di gioco"
            else:
                self.match.confirm_ball_in_play(ball)

        if thrower is not None and self.match.time_remaining[thrower] <= 0.0:
            self.match.expire_side_time(thrower)

        self.last_launched_ball = None
        next_key = self.match.choose_next_turn(self.jack.position)
        if next_key is None:
            self._finish_end()
        else:
            self._prepare_coloured_turn()

    def _finish_end(self) -> None:
        self.match.finish_end(self.jack.position)
        self.state = (
            self.MATCH_RESULT
            if self.match.match_over
            else self.END_RESULT
        )

    def _pass_remaining_human_balls(self) -> None:
        self.match.pass_remaining_balls(self.human_key)
        self.referee_message = "Bocce rimanenti dichiarate Dead Ball"
        next_key = self.match.choose_next_turn(self.jack.position)
        if next_key is None:
            self._finish_end()
        else:
            self._prepare_coloured_turn()

    def _consume_official_clock(self, dt: float) -> None:
        timed_states = {
            self.JACK_READY,
            self.JACK_ROLLING,
            self.READY,
            self.ROLLING,
            self.AI_THINKING,
            self.AI_THINKING_JACK,
        }
        if self.state not in timed_states:
            return
        key = self.match.current_key
        if key is None:
            return
        remaining = self.match.consume_time(key, dt)
        if remaining > 0.0:
            return
        if self.state in (self.JACK_ROLLING, self.ROLLING):
            return

        self.match.expire_side_time(key)
        self.referee_message = (
            f"Tempo scaduto per {self.match.player(key).name}"
        )
        if self.state in (self.JACK_READY, self.AI_THINKING_JACK):
            self._handle_fouled_jack("Tempo scaduto sul Jack")
            return
        next_key = self.match.choose_next_turn(self.jack.position)
        if next_key is None:
            self._finish_end()
        else:
            self._prepare_coloured_turn()

    def _human_can_aim(self) -> bool:
        return (
            self.match.current_key == self.human_key
            and self.state in (self.READY, self.JACK_READY)
        )

    def _current_launch_point(self) -> pygame.Vector2:
        key = self.match.current_key or self.human_key
        return self.field.launch_point_for(key)

    def _select_boccia_type(self, index: int) -> None:
        if self.state != self.READY:
            return
        if not (0 <= index < len(BOCCIA_PROFILES)):
            return
        self.selected_boccia_type = BOCCIA_PROFILES[index].key
        self.active_ball = self._make_ball(self.human_key)

    def _cycle_boccia_type(self, direction: int) -> None:
        if self.state != self.READY:
            return
        self.selected_boccia_type = cycle_boccia_profile(
            self.selected_boccia_type,
            direction,
        ).key
        self.active_ball = self._make_ball(self.human_key)

    def _continuous_keyboard_input(self, dt: float) -> None:
        if not self._human_can_aim():
            return
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
        vector = pygame.Vector2(mouse_pos) - self._current_launch_point()
        if vector.length_squared() < 4:
            return
        angle = math.degrees(math.atan2(vector.x, -vector.y))
        limit = self.gameplay["max_aim_angle"]
        self.angle = max(-limit, min(limit, angle))

    def _change_angle(self, amount: float) -> None:
        if not self._human_can_aim():
            return
        limit = self.gameplay["max_aim_angle"]
        self.angle = max(-limit, min(limit, self.angle + amount))

    def _change_power(self, amount: float) -> None:
        if not self._human_can_aim():
            return
        self.power = max(
            self.gameplay["min_power"],
            min(self.gameplay["max_power"], self.power + amount),
        )

    def _draw_aim_indicator(self) -> None:
        angle_radians = math.radians(self.angle)
        direction = pygame.Vector2(
            math.sin(angle_radians),
            -math.cos(angle_radians),
        )
        start = self._current_launch_point()
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

    def _draw_best_distance_lines(self) -> None:
        if not self.show_distance_guides or not self.match.jack_valid:
            return
        for key in self.match.PLAYER_ORDER:
            ball = self.match.best_ball(key, self.jack.position)
            if ball is not None:
                pygame.draw.line(
                    self.screen,
                    self.match.player(key).color,
                    ball.position,
                    self.jack.position,
                    2,
                )

    def _draw_hud(self) -> None:
        x = self.field.rect.right + 36
        y = 28
        width = self.window["width"] - x - 32

        self.screen.blit(
            self.font_title.render(
                "BOCCIA BATTLE • OFFICIAL",
                True,
                tuple(self.colors["text_primary"]),
            ),
            (x, y),
        )
        y += 38
        self.screen.blit(
            self.font_small.render(
                f"VERSIONE 0.8 • {RULES_VERSION}",
                True,
                tuple(self.colors["accent"]),
            ),
            (x, y),
        )
        y += 28

        self._panel(x, y, width, 75)
        self._row(x + 16, y + 10, "Stato", self._status_label())
        self._row(
            x + 16,
            y + 40,
            "Arbitro",
            self.referee_message[:44],
        )
        y += 88

        self._panel(x, y, width, 105)
        end_text = (
            f"TIE-BREAK {self.match.tiebreak_count}"
            if self.match.is_tiebreak
            else f"{self.match.current_end} / {self.match.max_ends}"
        )
        self._row(x + 16, y + 10, "End", end_text)
        self._row(
            x + 16,
            y + 40,
            "Punteggio",
            f"R {self.match.total_scores['red']} - {self.match.total_scores['blue']} B",
        )
        self._row(
            x + 16,
            y + 70,
            "Classe",
            self.sport_class,
        )
        y += 118

        self._panel(x, y, width, 135)
        self._row(
            x + 16,
            y + 10,
            "Rosso",
            f"{self.match.player('red').name} • {self.match.player('red').remaining} bocce",
        )
        self._row(
            x + 16,
            y + 40,
            "Tempo R",
            self._clock(self.match.time_remaining["red"]),
        )
        self._row(
            x + 16,
            y + 70,
            "Blu",
            f"{self.match.player('blue').name} • {self.match.player('blue').remaining} bocce",
        )
        self._row(
            x + 16,
            y + 100,
            "Tempo B",
            self._clock(self.match.time_remaining["blue"]),
        )
        y += 148

        self._panel(x, y, width, 135)
        self._row(
            x + 16,
            y + 10,
            "Direzione",
            f"{self.angle:+.1f}°" if self._human_can_aim() else "—",
        )
        self._row(
            x + 16,
            y + 40,
            "Potenza",
            f"{self.power:.0f}%" if self._human_can_aim() else "—",
        )
        self._row(
            x + 16,
            y + 70,
            "Boccia",
            get_boccia_profile(self.selected_boccia_type).label,
        )
        self._row(
            x + 16,
            y + 100,
            "Marca",
            get_brand(self.selected_brand).display_name,
        )
        y += 148

        self._panel(x, y, width, 110)
        self._row(
            x + 16,
            y + 10,
            "Più vicino",
            self._leader_text(),
        )
        self._row(
            x + 16,
            y + 40,
            "Dead ball",
            str(
                self.match.dead_balls["red"]
                + self.match.dead_balls["blue"]
            ),
        )
        self._row(
            x + 16,
            y + 70,
            "Collisioni",
            f"{self.ball_collisions} • Jack {self.jack_hits}",
        )

        footer = (
            "Mira mouse/←→ • Potenza rotella/↑↓ • SPAZIO lancia • "
            "P rinuncia alle bocce • ESC menu"
        )
        self.screen.blit(
            self.font_small.render(
                footer,
                True,
                tuple(self.colors["text_secondary"]),
            ),
            (x, self.window["height"] - 28),
        )

    def _status_label(self) -> str:
        if self.state == self.WARMUP:
            return "RISCALDAMENTO"
        if self.state in (self.JACK_READY, self.AI_THINKING_JACK):
            return "LANCIO DEL JACK"
        if self.state == self.JACK_ROLLING:
            return "JACK IN MOVIMENTO"
        if self.state == self.AI_THINKING:
            return "IL COMPUTER STA PENSANDO"
        if self.state == self.READY:
            return "PREPARA IL TIRO"
        if self.state == self.ROLLING:
            return "BOCCIA IN MOVIMENTO"
        if self.state == self.END_RESULT:
            return "END COMPLETATO"
        if self.state == self.BETWEEN_ENDS:
            return "INTERVALLO"
        return "PARTITA TERMINATA"

    def _leader_text(self) -> str:
        leader = self.match.leader(self.jack.position)
        if leader is None:
            return "—"
        if leader == "tie":
            return "EQUIDISTANTI"
        return self.match.player(leader).name

    def _reset_end_counters(self) -> None:
        self.ball_collisions = 0
        self.jack_hits = 0
        self.dead_ball_events = 0

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
        self.screen.blit(right, (x + 145, y))

    @staticmethod
    def _clock(seconds: float) -> str:
        value = max(0, int(math.ceil(seconds)))
        minutes, remainder = divmod(value, 60)
        return f"{minutes}:{remainder:02d}"
