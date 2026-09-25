from __future__ import annotations

import pygame

from game.config import load_settings
from game.player_profile import apply_profile_equipment, load_profile
from game.user_settings import apply_user_settings, load_user_settings
from screens.game_screen import GameScreen
from screens.local_game_screen import LocalGameScreen
from screens.menu import MenuScreen
from screens.settings_screen import SettingsScreen
from screens.store_screen import StoreScreen
from screens.tournament_screen import TournamentScreen
from screens.training_screen import TrainingScreen


def main() -> None:
    settings = apply_user_settings(
        load_settings(),
        load_user_settings(),
    )
    settings = apply_profile_equipment(settings, load_profile())
    pygame.init()
    pygame.display.set_caption("Boccia Battle — Versione 0.9")
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
        elif action == "local":
            current_screen = LocalGameScreen(screen, settings)
        elif action == "tournament":
            current_screen = TournamentScreen(screen, settings)
        elif action == "training":
            current_screen = TrainingScreen(screen, settings)
        elif action == "store":
            current_screen = StoreScreen(screen, settings)
        elif action == "settings":
            current_screen = SettingsScreen(screen, settings)
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
