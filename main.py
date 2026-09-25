from __future__ import annotations

import pygame

from game.config import load_settings
from screens.game_screen import GameScreen


def main() -> None:
    settings = load_settings()

    pygame.init()
    pygame.display.set_caption("Boccia Battle — Versione 0.2")

    window = settings["window"]
    screen = pygame.display.set_mode((window["width"], window["height"]))
    clock = pygame.time.Clock()

    game = GameScreen(screen, settings)
    running = True

    while running:
        dt = min(clock.tick(window["fps"]) / 1000.0, 1.0 / 30.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
