from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from game.player_profile import load_profile, save_profile
from screens.training_screen import TrainingScreen


@dataclass(frozen=True)
class TutorialStep:
    title: str
    instruction: str
    drill_index: int | None = None
    objective: str = ""


STEPS: tuple[TutorialStep, ...] = (
    TutorialStep(
        "1 • PRIMO TIRO",
        "Muovi il mouse sul campo e premi SPAZIO o click sinistro.",
        drill_index=0,
        objective="Completa un tiro.",
    ),
    TutorialStep(
        "2 • ACCOSTO",
        "Porta una boccia entro 50 cm dal jack.",
        drill_index=2,
        objective="Ottieni SUCCESSO nell'esercizio Accosto 50 cm.",
    ),
    TutorialStep(
        "3 • BOCCIATA",
        "Colpisci la boccia blu bersaglio.",
        drill_index=3,
        objective="Genera almeno una collisione boccia-boccia.",
    ),
    TutorialStep(
        "4 • JACK",
        "Colpisci direttamente il jack bianco.",
        drill_index=0,
        objective="Fai muovere il jack con la tua boccia.",
    ),
    TutorialStep(
        "5 • PENALTY",
        "Ferma tutta la boccia dentro il quadrato 35×35 cm.",
        drill_index=6,
        objective="Segna una penalty ball.",
    ),
    TutorialStep(
        "6 • PUNTEGGIO",
        "A fine end segna il lato più vicino al jack: conta ogni sua boccia più vicina della migliore avversaria.",
        drill_index=None,
        objective="Premi N per continuare.",
    ),
    TutorialStep(
        "7 • TIE-BREAK",
        "Sul pareggio dopo gli end regolamentari il jack va sulla croce; il tie-break decide il vincitore senza aumentare il totale regolamentare.",
        drill_index=None,
        objective="Premi N per completare il tutorial.",
    ),
)


class TutorialScreen(TrainingScreen):
    """Interactive first-run tutorial built on the real training physics."""

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        super().__init__(screen, settings)
        self.step_index = 0
        self.step_complete = False
        self._requested_action: str | None = None
        self._last_attempts = 0
        self._last_successes = 0
        self._apply_step()

    @property
    def step(self) -> TutorialStep:
        return STEPS[self.step_index]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
            if self.step_complete or self.step.drill_index is None:
                self._advance_step()
            return

        if self.step.drill_index is None:
            return

        super().handle_event(event)

    def update(self, dt: float) -> None:
        if self.step.drill_index is None:
            return

        old_attempts = self.drill_attempts
        old_successes = self.drill_successes
        old_state = self.state

        super().update(dt)

        shot_finished = (
            old_state == self.ROLLING
            and self.state == self.READY
        )
        if not shot_finished:
            return

        if self.step_index == 0:
            self.step_complete = self.drill_attempts > old_attempts
        elif self.step_index in (1, 2, 4):
            self.step_complete = self.drill_successes > old_successes
        elif self.step_index == 3:
            self.step_complete = self.shot_jack_hits > 0

        if self.step_complete:
            self.drill_message = "OBIETTIVO COMPLETATO ✓ • Premi N"

    def draw(self) -> None:
        super().draw()
        self._draw_tutorial_banner()

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _apply_step(self) -> None:
        self.step_complete = False
        step = self.step

        if step.drill_index is not None:
            self.drill_index = step.drill_index
            self._setup_drill(reset_score=True)

            # Jack-hit lesson is free practice with a fixed central jack.
            if self.step_index == 3:
                self.balls.clear()
                self.jack.position = self.field.cross_position.copy()
                self.jack.velocity.update(0, 0)
                self.drill_message = "Colpisci il jack bianco."
                self._prepare_ball()

        self._last_attempts = self.drill_attempts
        self._last_successes = self.drill_successes

    def _advance_step(self) -> None:
        if self.step_index >= len(STEPS) - 1:
            profile = load_profile()
            profile.mark_tutorial_complete()
            profile.xp += 100
            profile.gold += 100
            save_profile(profile)
            self._requested_action = "menu"
            return

        self.step_index += 1
        self._apply_step()

    def _draw_tutorial_banner(self) -> None:
        width = self.screen.get_width()
        rect = pygame.Rect(430, 24, width - 470, 112)

        overlay = pygame.Surface(
            (rect.width, rect.height),
            pygame.SRCALPHA,
        )
        overlay.fill((12, 17, 22, 235))
        self.screen.blit(overlay, rect.topleft)

        pygame.draw.rect(
            self.screen,
            tuple(self.colors["accent"]),
            rect,
            2,
            border_radius=12,
        )

        title = self.font_big.render(
            self.step.title,
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(title, (rect.x + 16, rect.y + 12))

        instruction = self.font_small.render(
            self.step.instruction[:92],
            True,
            tuple(self.colors["text_primary"]),
        )
        objective = self.font_small.render(
            self.step.objective[:92],
            True,
            tuple(
                self.colors["accent"]
                if self.step_complete
                else self.colors["text_secondary"]
            ),
        )

        self.screen.blit(instruction, (rect.x + 16, rect.y + 48))
        self.screen.blit(objective, (rect.x + 16, rect.y + 76))

        if self.step_complete:
            next_text = self.font_small.render(
                "N = CONTINUA",
                True,
                tuple(self.colors["accent"]),
            )
            self.screen.blit(
                next_text,
                (
                    rect.right - next_text.get_width() - 16,
                    rect.y + 14,
                ),
            )
