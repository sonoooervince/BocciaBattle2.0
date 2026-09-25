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
from game.disrupted_end import (
    capture_disrupted_end,
    restore_disrupted_end,
)
from game.field import Field
from game.jack import Jack
from game.match import MatchController
from game.official_rules import (
    BETWEEN_ENDS_SECONDS,
    PENALTY_BALL_SECONDS,
    RULES_VERSION,
    WARMUP_SECONDS,
    get_event_format,
    other_side,
)
from game.measurement import measure_balls, needs_precision_measurement
from game.physics import PhysicsEngine
from game.player_profile import load_profile, save_profile
from game.replay import ReplayRecorder, ShotReplay
from game.shot_simulator import ShotSimulator
from game.store_catalog import (
    approximate_profile_key,
    get_real_set,
)
from screens.result_screen import ResultScreen


class GameScreen:
    COIN_CHOICE = "coin_choice"
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
    PENALTY_READY = "penalty_ready"
    PENALTY_ROLLING = "penalty_rolling"
    AI_THINKING_PENALTY = "ai_thinking_penalty"
    TIMEOUT = "timeout"
    REPLAY = "replay"

    def __init__(
        self,
        screen: pygame.Surface,
        settings: dict[str, Any],
        progression_enabled: bool = True,
    ) -> None:
        self.screen = screen
        self.settings = settings
        self.window = settings["window"]
        self.gameplay = settings["gameplay"]
        self.physics_settings = settings["physics"]
        self.match_settings = settings["match"]
        self.colors = settings["colors"]
        self.random = random.Random()
        self.progression_enabled = progression_enabled
        self.reward_awarded = False
        self.reward_text = ""
        self.player_profile = load_profile()
        self.precise_measurement = False
        self.current_shot_owner: str | None = None
        self.current_shot_ball_collision_start = 0
        self.current_shot_jack_hit_start = 0
        self.replay_recorder = ReplayRecorder(capture_fps=30.0)
        self.last_replay: ShotReplay | None = None
        self.replay_return_state = self.READY
        self.replay_index = 0
        self.replay_elapsed = 0.0

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
            solver_iterations=self.physics_settings.get(
                "solver_iterations",
                6,
            ),
        )
        self.results = ResultScreen(screen, self.colors)

        self.sport_class = self.gameplay.get("sport_class", "BC2")
        self.event_format = get_event_format("individual", self.sport_class)

        self.coin_toss_winner = self.random.choice(("human", "computer"))
        if self.coin_toss_winner == "human":
            self.human_key = "red"
            self.ai_key = "blue"
            self.coin_toss_text = "Hai vinto il sorteggio: scegli ROSSO o BLU"
        else:
            self.human_key = "blue"
            self.ai_key = "red"
            self.coin_toss_text = "COMPUTER vince il sorteggio e sceglie ROSSO"

        self.match = self._new_match_controller()
        self.shot_simulator = ShotSimulator(
            physics_settings=self.physics_settings,
            bounds=self.field.playable_bounds,
            cross_position=self.field.cross_position,
            ball_radius=self.gameplay["boccia_radius"],
            ball_mass=self.gameplay["boccia_mass"],
            min_speed=self.gameplay["min_launch_speed"],
            max_speed=self.gameplay["max_launch_speed"],
        )
        self.ai = BocciaAI(
            min_speed=self.gameplay["min_launch_speed"],
            max_speed=self.gameplay["max_launch_speed"],
            friction_deceleration=self.physics_settings["friction_deceleration"],
            difficulty=self.gameplay.get("ai_difficulty", "normal"),
            level=self.gameplay.get("ai_level", 10),
            simulator=self.shot_simulator,
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
        self.aim_mode = self.gameplay.get("aim_mode", "target")
        self.selected_set_id = self.gameplay.get(
            "selected_set_id",
            "handi_standard_pro",
        )
        self.selected_set_name = self.gameplay.get(
            "selected_set_name",
            get_real_set(self.selected_set_id).model,
        )
        self.target_marker: pygame.Vector2 | None = None
        self.human_available_slots = list(range(6))
        self.selected_loadout_slot = 0

        self.angle = 0.0
        self.power = 55.0
        self.active_ball: Boccia | None = None
        self.last_launched_ball: Boccia | None = None
        self.penalty_ball: Boccia | None = None
        self.penalty_dummy_jack = Jack(
            pygame.Vector2(-1000, -1000),
            radius=self.gameplay["jack_radius"],
            mass=self.gameplay["jack_mass"],
        )
        self.penalty_time_remaining = 0.0
        self.penalty_announced: set[int] = set()
        self.clock_announced = {"red": set(), "blue": set()}
        self.between_ends_announced = False
        self.timeout_remaining = 0.0
        self.timeout_kind = ""
        self.timeout_return_state: str | None = None
        self.jack = self._new_jack_at_cross()
        self.last_legitimate_snapshot = capture_disrupted_end(
            self.match,
            self.jack,
        )
        self.ai_think_timer = 0.0
        self.ai_plan = None
        self.state = (
            self.COIN_CHOICE
            if self.coin_toss_winner == "human"
            else self.WARMUP
        )
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

        if self.state == self.REPLAY:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_v,
                pygame.K_SPACE,
                pygame.K_RETURN,
            ):
                self._stop_replay()
            return

        if self.state == self.COIN_CHOICE:
            if event.key == pygame.K_r:
                self._choose_colour("red")
            elif event.key == pygame.K_b:
                self._choose_colour("blue")
            return

        if self.state == self.TIMEOUT:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._resume_timeout()
            elif event.key == pygame.K_f:
                self.match.forfeit(self.human_key)
                self.state = self.MATCH_RESULT
            return

        if event.key == pygame.K_v and self.last_replay is not None:
            self._start_replay()
            return

        if event.key == pygame.K_z:
            self.precise_measurement = not self.precise_measurement
            return

        if event.key in (pygame.K_m, pygame.K_t) and self._timeout_can_be_called():
            kind = "medical" if event.key == pygame.K_m else "technical"
            self._start_timeout(kind)
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
            pygame.K_6,
        ):
            self._select_loadout_slot(event.key - pygame.K_1)
        elif event.key == pygame.K_q:
            self._cycle_loadout_slot(-1)
        elif event.key == pygame.K_e:
            self._cycle_loadout_slot(1)
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
        if self.state == self.REPLAY:
            self._update_replay(dt)
            return

        if self.state == self.COIN_CHOICE:
            return

        if self.state == self.TIMEOUT:
            self.timeout_remaining = max(
                0.0,
                self.timeout_remaining - dt,
            )
            if self.timeout_remaining <= 0.0:
                self._resume_timeout()
            return

        if self.state == self.WARMUP:
            self.warmup_remaining = max(
                0.0,
                self.warmup_remaining - dt,
            )
            if self.warmup_remaining <= 0.0:
                self._start_match_after_warmup()
            return

        if self.state == self.BETWEEN_ENDS:
            previous = self.between_ends_remaining
            self.between_ends_remaining = max(
                0.0,
                self.between_ends_remaining - dt,
            )
            if (
                previous > 15.0 >= self.between_ends_remaining
                and not self.between_ends_announced
            ):
                self.between_ends_announced = True
                self.referee_message = "15 secondi!"
            if self.between_ends_remaining <= 0.0:
                self.referee_message = "Time!"
                self._start_current_end()
            return

        if self.state in (
            self.PENALTY_READY,
            self.AI_THINKING_PENALTY,
            self.PENALTY_ROLLING,
        ):
            self._update_penalty_phase(dt)
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

        if self.state == self.REPLAY:
            self._draw_replay_frame()
        else:
            for ball in self.match.all_balls:
                ball.draw(self.screen)

        if self.state not in (
            self.WARMUP,
            self.COIN_CHOICE,
            self.PENALTY_READY,
            self.AI_THINKING_PENALTY,
            self.PENALTY_ROLLING,
            self.REPLAY,
        ):
            self.jack.draw(self.screen)

        if self._human_can_aim():
            self._draw_aim_indicator()
            if self.state == self.READY and self.active_ball is not None:
                self.active_ball.draw(self.screen, selected=True)
            elif (
                self.state == self.PENALTY_READY
                and self.penalty_ball is not None
            ):
                self.penalty_ball.draw(self.screen, selected=True)

        if (
            self.state == self.PENALTY_ROLLING
            and self.penalty_ball is not None
        ):
            self.penalty_ball.draw(self.screen)

        self._draw_hud()
        self._draw_measurement_panel()

        if self.state == self.TIMEOUT:
            self.results.draw_message(
                "TIME OUT",
                self.timeout_kind.upper(),
                self._clock(self.timeout_remaining),
                "INVIO = riprendi • F = impossibile continuare / forfait",
            )
        elif self.state == self.COIN_CHOICE:
            self.results.draw_message(
                "SORTEGGIO",
                "Hai vinto",
                "R = ROSSO    B = BLU",
                "Scegli il colore con cui giocare",
            )
        elif self.state == self.WARMUP:
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
        if self.coin_toss_winner == "human":
            self.human_key = "red"
            self.ai_key = "blue"
            self.coin_toss_text = "Hai vinto il sorteggio: scegli ROSSO o BLU"
            self.state = self.COIN_CHOICE
        else:
            self.human_key = "blue"
            self.ai_key = "red"
            self.coin_toss_text = "COMPUTER vince il sorteggio e sceglie ROSSO"
            self.state = self.WARMUP
        self.match = self._new_match_controller()
        self.jack = self._new_jack_at_cross()
        self.warmup_remaining = float(WARMUP_SECONDS)
        self.referee_message = self.coin_toss_text
        self.penalty_ball = None
        self.clock_announced = {"red": set(), "blue": set()}
        self._reset_end_counters()

    def _choose_colour(self, key: str) -> None:
        self.human_key = key
        self.ai_key = other_side(key)
        self.coin_toss_text = (
            f"Hai scelto {'ROSSO' if key == 'red' else 'BLU'}"
        )
        self.match = self._new_match_controller()
        self.referee_message = self.coin_toss_text
        self.warmup_remaining = float(WARMUP_SECONDS)
        self.state = self.WARMUP

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
        self.between_ends_announced = False
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

        if (
            self.human_available_slots
            and self.selected_loadout_slot not in self.human_available_slots
        ):
            self.selected_loadout_slot = self.human_available_slots[0]

        self.state = self.READY
        self.active_ball = self._make_ball(player.key)

    def _make_ball(self, key: str, ai: bool = False) -> Boccia:
        player = self.match.player(key)
        boccia_type = "medie" if ai else self.selected_boccia_type
        set_id = ""
        hardness = ""

        loadout_slot = -1
        if key == self.human_key and not ai:
            available = self.human_available_slots or list(range(6))
            slot_index = (
                self.selected_loadout_slot
                if self.selected_loadout_slot in available
                else available[0]
            )
            spec = self.player_profile.get_ball_slot(slot_index)
            set_id = spec["set_id"]
            hardness = spec["hardness"]
            boccia_type = approximate_profile_key(hardness)
            loadout_slot = slot_index

        return Boccia(
            self.field.launch_point_for(key),
            radius=self.gameplay["boccia_radius"],
            color=player.color,
            owner_key=key,
            mass=self.gameplay["boccia_mass"],
            boccia_type=boccia_type,
            set_id=set_id,
            hardness=hardness,
            loadout_slot=loadout_slot,
        )

    def _launch_human(self) -> None:
        if self.match.current_key != self.human_key:
            return
        if self.state == self.PENALTY_READY:
            if self.penalty_ball is None:
                return
            self._capture_legitimate_state()
            self.penalty_ball.launch(
                self.angle,
                self.power,
                self.gameplay["min_launch_speed"],
                self.gameplay["max_launch_speed"],
            )
            self.state = self.PENALTY_ROLLING
            return
        if self.state == self.JACK_READY:
            self._capture_legitimate_state()
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
        self._capture_legitimate_state()
        self._launch_coloured_ball(self.active_ball)

    def _launch_ai_jack(self) -> None:
        key = self.match.current_key
        if key != self.ai_key:
            return
        self._capture_legitimate_state()
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
        self._capture_legitimate_state()
        plan = self.ai.choose_shot_from_launch(
            self.match,
            self.jack,
            self.field.launch_point_for(key),
            side_key=key,
            boccia_type="medie",
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
        self.current_shot_owner = ball.owner_key
        self.current_shot_ball_collision_start = self.ball_collisions
        self.current_shot_jack_hit_start = self.jack_hits
        self.match.register_throw(ball)
        if (
            ball.owner_key == self.human_key
            and ball.loadout_slot in self.human_available_slots
        ):
            self.human_available_slots.remove(ball.loadout_slot)
            if self.human_available_slots:
                self.selected_loadout_slot = self.human_available_slots[0]
        self.last_launched_ball = ball
        self.replay_recorder.start(
            self.match.all_balls,
            self.jack,
        )
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
        jack_replaced = False
        report = self.physics.step(
            self.match.all_balls,
            self.jack,
            dt,
            self.field.playable_bounds,
        )
        self.replay_recorder.capture(
            self.match.all_balls,
            self.jack,
            dt,
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
            jack_replaced = True
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

        self.replay_recorder.capture(
            self.match.all_balls,
            self.jack,
            dt,
            force=True,
        )
        replay = self.replay_recorder.finish(
            self.match.all_balls,
            self.jack,
        )
        if replay.available:
            self.last_replay = replay

        self._record_completed_shot(ball, thrower)
        self.last_launched_ball = None
        next_key = self.match.choose_next_turn(
            self.jack.position,
            jack_knocker_if_empty=(
                thrower
                if jack_replaced and not self.match.all_balls
                else None
            ),
        )
        if next_key is None:
            self._finish_end()
        else:
            self._prepare_coloured_turn()

    def _finish_end(self) -> None:
        if self.match.has_pending_penalty_balls:
            self._start_penalty_phase()
            return
        self._finalize_end_score()

    def _finalize_end_score(self) -> None:
        self.match.finish_end(self.jack.position)
        self.state = (
            self.MATCH_RESULT
            if self.match.match_over
            else self.END_RESULT
        )
        if self.match.match_over:
            self._award_progression_once()

    def _award_progression_once(self) -> None:
        if self.reward_awarded or not self.progression_enabled:
            return
        winner = self.match.winner
        if winner is None:
            return
        profile = load_profile()
        won = winner == self.human_key
        xp_gain, gold_gain = profile.reward_match(
            won,
            set_id=self.selected_set_id,
        )
        save_profile(profile)
        self.reward_awarded = True
        self.reward_text = f"+{xp_gain} XP • +{gold_gain} GOLD"

    def _start_penalty_phase(self) -> None:
        key = self.match.begin_penalty_phase(self.jack.position)
        if key is None:
            self._finalize_end_score()
            return

        self.match.player("red").balls.clear()
        self.match.player("blue").balls.clear()
        self.last_launched_ball = None
        self.active_ball = None
        self.penalty_ball = None
        self.referee_message = "One minute! Penalty ball"
        self._prepare_penalty_attempt()

    def _prepare_penalty_attempt(self) -> None:
        key = self.match.current_key
        if key is None:
            self.penalty_ball = None
            self._finalize_end_score()
            return

        self.angle = 0.0
        self.power = 45.0
        self.penalty_time_remaining = float(PENALTY_BALL_SECONDS)
        self.penalty_announced = set()
        self.penalty_ball = self._make_ball(
            key,
            ai=(key == self.ai_key),
        )
        self.referee_message = (
            f"One minute! Penalty ball a {self.match.player(key).name}"
        )
        if key == self.ai_key:
            self.ai_think_timer = self.gameplay.get("ai_think_time", 0.9)
            self.state = self.AI_THINKING_PENALTY
        else:
            self.state = self.PENALTY_READY

    def _launch_ai_penalty(self) -> None:
        key = self.match.current_key
        if key != self.ai_key or self.penalty_ball is None:
            return
        self._capture_legitimate_state()
        plan = self.ai.choose_jack_shot(
            self.field.launch_point_for(key),
            self.field.cross_position,
        )
        self.ai_plan = plan
        self.angle = plan.angle
        self.power = plan.power
        self.penalty_ball.launch(
            plan.angle,
            plan.power,
            self.gameplay["min_launch_speed"],
            self.gameplay["max_launch_speed"],
        )
        self.state = self.PENALTY_ROLLING

    def _update_penalty_phase(self, dt: float) -> None:
        if self.state in (
            self.PENALTY_READY,
            self.AI_THINKING_PENALTY,
        ):
            previous = self.penalty_time_remaining
            self.penalty_time_remaining = max(
                0.0,
                self.penalty_time_remaining - dt,
            )
            self._announce_countdown(
                previous,
                self.penalty_time_remaining,
                self.penalty_announced,
                "Penalty",
            )
            if self.penalty_time_remaining <= 0.0:
                self.referee_message = "Time! Penalty ball non giocata"
                self._complete_penalty_attempt(False)
                return

            if self.state == self.AI_THINKING_PENALTY:
                self.ai_think_timer -= dt
                if self.ai_think_timer <= 0.0:
                    self._launch_ai_penalty()
            return

        if self.state != self.PENALTY_ROLLING or self.penalty_ball is None:
            return

        self.physics.step(
            [self.penalty_ball],
            self.penalty_dummy_jack,
            dt,
            self.field.playable_bounds,
        )
        if self.field.touches_exterior_boundary(self.penalty_ball):
            self.penalty_ball.velocity.update(0, 0)
            self._complete_penalty_attempt(False)
            return
        if self.penalty_ball.is_moving:
            return

        self._complete_penalty_attempt(
            self.field.ball_scores_penalty(self.penalty_ball)
        )

    def _complete_penalty_attempt(self, scored: bool) -> None:
        key = self.match.current_key
        if key is None:
            return
        self.match.record_penalty_attempt(key, scored)
        self.referee_message = (
            "Penalty point!"
            if scored
            else "Penalty ball: nessun punto"
        )
        self.penalty_ball = None
        if self.match.current_key is None:
            self._finalize_end_score()
        else:
            self._prepare_penalty_attempt()

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
        previous = self.match.time_remaining[key]
        remaining = self.match.consume_time(key, dt)
        self._announce_countdown(
            previous,
            remaining,
            self.clock_announced[key],
            self.match.player(key).name,
        )
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

    def _start_replay(self) -> None:
        if self.last_replay is None or not self.last_replay.available:
            return
        self.replay_return_state = self.state
        self.replay_index = 0
        self.replay_elapsed = 0.0
        self.state = self.REPLAY

    def _stop_replay(self) -> None:
        self.state = self.replay_return_state
        self.replay_index = 0
        self.replay_elapsed = 0.0

    def _update_replay(self, dt: float) -> None:
        replay = self.last_replay
        if replay is None or not replay.available:
            self._stop_replay()
            return

        self.replay_elapsed += max(0.0, dt)
        frame_duration = 1.0 / max(1.0, replay.capture_fps * 0.5)

        while self.replay_elapsed >= frame_duration:
            self.replay_elapsed -= frame_duration
            self.replay_index += 1
            if self.replay_index >= len(replay.frames):
                self.replay_index = len(replay.frames) - 1
                self._stop_replay()
                return

    def _draw_replay_frame(self) -> None:
        replay = self.last_replay
        if replay is None or not replay.frames:
            return

        frame = replay.frames[
            max(0, min(self.replay_index, len(replay.frames) - 1))
        ]

        for ball in frame.balls:
            radius = max(ball.radius, 4)
            center = (round(ball.x), round(ball.y))
            pygame.draw.circle(
                self.screen,
                ball.color,
                center,
                radius,
            )
            pygame.draw.circle(
                self.screen,
                (245, 245, 245),
                center,
                radius,
                1,
            )

        jack_center = (round(frame.jack_x), round(frame.jack_y))
        jack_radius = max(frame.jack_radius, 4)
        pygame.draw.circle(
            self.screen,
            (248, 248, 242),
            jack_center,
            jack_radius,
        )
        pygame.draw.circle(
            self.screen,
            (105, 105, 105),
            jack_center,
            jack_radius,
            1,
        )

        label = self.font_big.render(
            "REPLAY 0.5×",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(
            label,
            (
                self.field.rect.left + 10,
                self.field.rect.bottom - 34,
            ),
        )

    def _record_completed_shot(
        self,
        ball: Boccia | None,
        thrower: str | None,
    ) -> None:
        if (
            thrower != self.human_key
            or self.current_shot_owner != self.human_key
        ):
            return

        distance_cm: float | None = None
        set_id = self.selected_set_id

        if ball is not None:
            set_id = ball.set_id or set_id
            if ball in self.match.all_balls:
                distance_px = ball.position.distance_to(self.jack.position)
                distance_cm = (
                    distance_px
                    / self.field.rect.height
                    * self.field.COURT_LENGTH_M
                    * 100.0
                )

        hit_ball = (
            self.ball_collisions
            > self.current_shot_ball_collision_start
        )
        hit_jack = self.jack_hits > self.current_shot_jack_hit_start

        self.player_profile = load_profile()
        self.player_profile.record_shot(
            distance_cm=distance_cm,
            hit_ball=hit_ball,
            hit_jack=hit_jack,
            set_id=set_id,
        )
        save_profile(self.player_profile)

    def _draw_measurement_panel(self) -> None:
        if not self.match.jack_valid:
            return

        values = measure_balls(
            self.match.all_balls,
            self.jack.position,
            self.field.rect.height,
        )
        if not values:
            return

        auto = needs_precision_measurement(values)
        if not self.precise_measurement and not auto:
            return

        x = self.field.rect.left + 8
        y = self.field.rect.top + 8
        width = 238
        height = 30 + min(6, len(values)) * 24

        panel = pygame.Rect(x, y, width, height)
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((15, 20, 25, 222))
        self.screen.blit(overlay, panel.topleft)
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["accent"]),
            panel,
            1,
            border_radius=7,
        )

        title = self.font_small.render(
            "MISURAZIONE AUTOMATICA" if auto else "MISURAZIONE",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(title, (x + 8, y + 7))

        for index, item in enumerate(values[:6]):
            label = (
                "R" if item.owner_key == "red" else "B"
            )
            precision = (
                f"{item.distance_cm:.1f} cm"
                if item.distance_cm >= 10.0
                else f"{item.distance_cm * 10.0:.0f} mm"
            )
            line = self.font_small.render(
                f"{index + 1}. {label}  {precision}",
                True,
                tuple(self.match.player(item.owner_key).color),
            )
            self.screen.blit(
                line,
                (x + 8, y + 31 + index * 24),
            )

    def _capture_legitimate_state(self) -> None:
        self.last_legitimate_snapshot = capture_disrupted_end(
            self.match,
            self.jack,
        )

    def restore_last_legitimate_state(self) -> None:
        """Referee hook for rule 12 disrupted-end restoration."""
        self.match, self.jack = restore_disrupted_end(
            self.last_legitimate_snapshot
        )
        self.penalty_ball = None
        self.last_launched_ball = None
        self.active_ball = None
        self.referee_message = "Disrupted end: stato precedente ripristinato"
        if not self.match.jack_valid and not self.match.is_tiebreak:
            self._prepare_jack_turn()
        else:
            self._prepare_coloured_turn()

    def _timeout_can_be_called(self) -> bool:
        return self.state in {
            self.JACK_READY,
            self.JACK_ROLLING,
            self.READY,
            self.ROLLING,
            self.AI_THINKING,
            self.AI_THINKING_JACK,
            self.PENALTY_READY,
            self.PENALTY_ROLLING,
            self.AI_THINKING_PENALTY,
        }

    def _start_timeout(self, kind: str) -> None:
        if kind == "medical":
            accepted = self.match.request_medical_timeout(self.human_key)
        else:
            accepted = self.match.request_technical_timeout(self.human_key)

        if not accepted:
            self.referee_message = (
                f"{kind.capitalize()} time out già utilizzato"
            )
            return

        self.timeout_return_state = self.state
        self.timeout_kind = f"{kind} time out"
        self.timeout_remaining = 10 * 60.0
        self.referee_message = (
            f"{self.timeout_kind}: cronometro di gara fermato"
        )
        self.state = self.TIMEOUT

    def _resume_timeout(self) -> None:
        self.referee_message = f"{self.timeout_kind} terminato"
        self.state = self.timeout_return_state or self.READY
        self.timeout_return_state = None
        self.timeout_kind = ""
        self.timeout_remaining = 0.0

    def _announce_countdown(
        self,
        previous: float,
        remaining: float,
        announced: set[int],
        prefix: str,
    ) -> None:
        labels = {
            60: "1 minuto",
            30: "30 secondi",
            10: "10 secondi",
        }
        for threshold in (60, 30, 10):
            if (
                previous > threshold >= remaining
                and threshold not in announced
            ):
                announced.add(threshold)
                self.referee_message = (
                    f"{prefix}: {labels[threshold]}"
                )
                break

    def _human_can_aim(self) -> bool:
        return (
            self.match.current_key == self.human_key
            and self.state in (
                self.READY,
                self.JACK_READY,
                self.PENALTY_READY,
            )
        )

    def _current_launch_point(self) -> pygame.Vector2:
        key = self.match.current_key or self.human_key
        return self.field.launch_point_for(key)

    def _select_boccia_type(self, index: int) -> None:
        if self.state not in (self.READY, self.PENALTY_READY):
            return
        if not (0 <= index < len(BOCCIA_PROFILES)):
            return
        self.selected_boccia_type = BOCCIA_PROFILES[index].key
        if self.state == self.PENALTY_READY:
            self.penalty_ball = self._make_ball(self.human_key)
        else:
            self.active_ball = self._make_ball(self.human_key)

    def _cycle_boccia_type(self, direction: int) -> None:
        if self.state not in (self.READY, self.PENALTY_READY):
            return
        self.selected_boccia_type = cycle_boccia_profile(
            self.selected_boccia_type,
            direction,
        ).key
        if self.state == self.PENALTY_READY:
            self.penalty_ball = self._make_ball(self.human_key)
        else:
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
        target = pygame.Vector2(mouse_pos)
        vector = target - self._current_launch_point()
        if vector.length_squared() < 4:
            return

        self.target_marker = target
        angle = math.degrees(math.atan2(vector.x, -vector.y))
        limit = self.gameplay["max_aim_angle"]
        self.angle = max(-limit, min(limit, angle))

        if self.aim_mode != "target":
            return

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
        target_power = normalized * 100.0
        self.power = max(
            self.gameplay["min_power"],
            min(self.gameplay["max_power"], target_power),
        )

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
        if self.aim_mode == "target" and self.target_marker is not None:
            center = (
                round(self.target_marker.x),
                round(self.target_marker.y),
            )
            pygame.draw.circle(
                self.screen,
                tuple(self.colors["aim"]),
                center,
                10,
                2,
            )
            pygame.draw.line(
                self.screen,
                tuple(self.colors["aim"]),
                (center[0] - 14, center[1]),
                (center[0] + 14, center[1]),
                1,
            )
            pygame.draw.line(
                self.screen,
                tuple(self.colors["aim"]),
                (center[0], center[1] - 14),
                (center[0], center[1] + 14),
                1,
            )

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
                f"VERSIONE 0.9.1 • {RULES_VERSION}",
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
            "Set",
            self.selected_set_name[:28],
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
            f"Controllo {self.aim_mode.upper()} • mouse/←→ • rotella/↑↓ • "
            "SPAZIO lancia • V replay • Z misura • P rinuncia • ESC menu"
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
        if self.state == self.REPLAY:
            return "REPLAY 0.5×"
        if self.state == self.TIMEOUT:
            return "TIME OUT"
        if self.state == self.COIN_CHOICE:
            return "SORTEGGIO"
        if self.state == self.WARMUP:
            return "RISCALDAMENTO"
        if self.state in (self.JACK_READY, self.AI_THINKING_JACK):
            return "LANCIO DEL JACK"
        if self.state == self.JACK_ROLLING:
            return "JACK IN MOVIMENTO"
        if self.state == self.AI_THINKING:
            return "IL COMPUTER STA PENSANDO"
        if self.state in (
            self.PENALTY_READY,
            self.AI_THINKING_PENALTY,
            self.PENALTY_ROLLING,
        ):
            return f"PENALTY BALL • {self._clock(self.penalty_time_remaining)}"
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
        self.clock_announced = {"red": set(), "blue": set()}
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
