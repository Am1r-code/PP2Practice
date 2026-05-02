"""
main.py - Music Player Application
An interactive music player with keyboard controls and a clean UI.

Keyboard Controls
-----------------
  P        – Play current track
  S        – Stop playback
  SPACE    – Pause / Resume
  N        – Next track
  B        – Back (previous track)
  UP       – Volume up
  DOWN     – Volume down
  Q/ESC    – Quit
"""

import pygame
import sys
import os

from player import MusicPlayer

# ── Constants ────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 480
FPS           = 30

# Colour palette
BG_COLOR       = (18,  18,  28)
PANEL_COLOR    = (28,  28,  45)
ACCENT_COLOR   = (92, 184, 255)
TEXT_COLOR     = (230, 230, 240)
MUTED_COLOR    = (100, 100, 130)
PLAYING_COLOR  = (80, 220, 140)
STOPPED_COLOR  = (200, 80,  80)
PAUSED_COLOR   = (240, 180,  40)

PADDING = 30


def status_color(player: MusicPlayer):
    if player.is_paused:
        return PAUSED_COLOR
    if player.is_playing:
        return PLAYING_COLOR
    return STOPPED_COLOR


def draw_ui(screen, player: MusicPlayer, fonts: dict):
    """Render the full player UI each frame."""
    screen.fill(BG_COLOR)

    w, h = screen.get_size()

    # ── Title bar ────────────────────────────────────────────────────────────
    title_surf = fonts["title"].render("🎵  Music Player", True, ACCENT_COLOR)
    screen.blit(title_surf, (PADDING, PADDING))

    # ── Track info panel ─────────────────────────────────────────────────────
    panel_rect = pygame.Rect(PADDING, 90, w - PADDING * 2, 130)
    pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=12)
    pygame.draw.rect(screen, ACCENT_COLOR, panel_rect, width=1, border_radius=12)

    # Track name (truncate if too long)
    name = player.current_track_name
    max_chars = 36
    if len(name) > max_chars:
        name = name[:max_chars - 1] + "…"

    track_surf = fonts["track"].render(name, True, TEXT_COLOR)
    screen.blit(track_surf, (PADDING + 18, 108))

    pos_surf = fonts["normal"].render(player.position_str, True, MUTED_COLOR)
    screen.blit(pos_surf, (PADDING + 18, 148))

    # Status indicator
    status_surf = fonts["normal"].render(player.status_str, True, status_color(player))
    screen.blit(status_surf, (PADDING + 18, 178))

    # ── Volume bar ────────────────────────────────────────────────────────────
    vol_surf = fonts["mono"].render(player.volume_bar, True, ACCENT_COLOR)
    screen.blit(vol_surf, (PADDING, 250))

    # ── Key hint table ───────────────────────────────────────────────────────
    hints = [
        ("[P]", "Play"),
        ("[S]", "Stop"),
        ("[SPACE]", "Pause / Resume"),
        ("[N]", "Next track"),
        ("[B]", "Previous track"),
        ("[↑/↓]", "Volume"),
        ("[Q]", "Quit"),
    ]

    hint_y = 300
    col1_x = PADDING
    col2_x = PADDING + 120

    sep_surf = fonts["small"].render("─" * 60, True, MUTED_COLOR)
    screen.blit(sep_surf, (col1_x, hint_y - 10))

    for key, action in hints:
        k_surf = fonts["small"].render(key,    True, ACCENT_COLOR)
        a_surf = fonts["small"].render(action, True, MUTED_COLOR)
        screen.blit(k_surf, (col1_x, hint_y))
        screen.blit(a_surf, (col2_x, hint_y))
        hint_y += 22

    if not player.tracks:
        warn = fonts["normal"].render("⚠  No audio files found in music/", True, STOPPED_COLOR)
        screen.blit(warn, (PADDING, h - 50))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Music Player")
    clock = pygame.time.Clock()

    # ── Fonts ─────────────────────────────────────────────────────────────────
    fonts = {
        "title":  pygame.font.SysFont("arial",   28, bold=True),
        "track":  pygame.font.SysFont("arial",   22, bold=True),
        "normal": pygame.font.SysFont("arial",   18),
        "small":  pygame.font.SysFont("arial",   15),
        "mono":   pygame.font.SysFont("monospace", 16),
    }

    # ── Music directory ───────────────────────────────────────────────────────
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    music_dir  = os.path.join(base_dir, "music")
    player     = MusicPlayer(music_dir)

    running = True
    while running:
        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

                elif event.key == pygame.K_p:
                    player.play()

                elif event.key == pygame.K_s:
                    player.stop()

                elif event.key == pygame.K_SPACE:
                    player.pause_toggle()

                elif event.key == pygame.K_n:
                    player.next_track()

                elif event.key == pygame.K_b:
                    player.prev_track()

                elif event.key == pygame.K_UP:
                    player.volume_up()

                elif event.key == pygame.K_DOWN:
                    player.volume_down()

        # ── Auto-advance when track ends ──────────────────────────────────────
        player.check_track_ended()

        # ── Draw ──────────────────────────────────────────────────────────────
        draw_ui(screen, player, fonts)
        pygame.display.flip()
        clock.tick(FPS)

    player.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
