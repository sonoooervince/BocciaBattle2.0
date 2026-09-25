from __future__ import annotations

import pygame

from game.config import load_settings
from screens.game_screen import GameScreen
from screens.menu import MenuScreen
from screens.tournament_screen import TournamentScreen


def main() -> None:
    settings = load_settings()

    pygame.init()
    pygame.display.set_caption("Boccia Battle — Versione 0.6")

    window = settings["window"]
    screen = pygame.display.set_mode(
        (window["width"], window["height"])
    )
    clock = pygame.time.Clock()

    current_screen: object = MenuScreen(screen, settings)
    running = True

    while running:
        dt = min(clock.tick(window["fps"]) / 1000.0, 1.0 / 30.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                if isinstance(current_screen, MenuScreen):
                    running = False
                else:
                    current_screen = MenuScreen(screen, settings)
                continue

            current_screen.handle_event(event)

        current_screen.update(dt)

        consume_action = getattr(current_screen, "consume_action", None)
        action = consume_action() if consume_action is not None else None

        if action == "quick":
            current_screen = GameScreen(screen, settings)
        elif action == "tournament":
            current_screen = TournamentScreen(screen, settings)
        elif action == "menu":
            current_screen = MenuScreen(screen, settings)
        elif action == "quit":
            running = False

        if not running:
            break

        current_screen.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
