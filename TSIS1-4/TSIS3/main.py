import pygame
import sys

from persistence import (
    load_settings, save_settings,
    load_leaderboard, add_leaderboard_entry,
)
from ui import (
    main_menu, name_entry_screen,
    leaderboard_screen, settings_screen, game_over_screen,
)
from racer import run_game

W, H = 700, 750


def main():
    pygame.init()
    pygame.display.set_caption("Racer – Extended Edition (TSIS 3)")
    screen   = pygame.display.set_mode((W, H))
    settings = load_settings()

    state = "menu"

    while True:
        if state == "menu":
            action = main_menu(screen, settings)
            if action == "quit":
                break
            elif action == "play":
                state = "name_entry"
            elif action == "leaderboard":
                state = "leaderboard"
            elif action == "settings":
                state = "settings"

        elif state == "name_entry":
            name = name_entry_screen(screen, settings.get("player_name", "Player"))
            settings["player_name"] = name
            save_settings(settings)
            state = "game"

        elif state == "game":
            stats = run_game(screen, settings)
            # Persist to leaderboard
            add_leaderboard_entry(
                stats["name"], stats["score"],
                stats["distance"], stats["coins"]
            )
            state = "game_over"
            last_stats = stats

        elif state == "game_over":
            action = game_over_screen(screen, last_stats)
            if action == "retry":
                state = "game"
            else:
                state = "menu"

        elif state == "leaderboard":
            entries = load_leaderboard()
            leaderboard_screen(screen, entries)
            state = "menu"

        elif state == "settings":
            _, updated = settings_screen(screen, settings)
            settings = updated
            save_settings(settings)
            state = "menu"

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
