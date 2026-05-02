"""
ui.py  –  Screen renderers for all non-gameplay screens (TSIS 3)
=================================================================
Screens implemented here (all return the next GameState string):
  • main_menu()
  • leaderboard_screen()
  • settings_screen()
  • game_over_screen()
  • name_entry_screen()

Each function runs its own tight event loop and returns a string
action such as "play", "menu", "quit", "leaderboard", "settings".
"""

import pygame
import sys

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG       = (12,  14,  22)
C_ROAD     = (35,  38,  50)
C_ACCENT   = (255, 200,  40)   # yellow
C_WHITE    = (230, 235, 245)
C_MUTED    = (110, 115, 135)
C_RED      = (220,  60,  50)
C_GREEN    = ( 60, 200,  90)
C_BLUE     = ( 60, 130, 255)
C_PANEL    = ( 22,  25,  36)
C_BORDER   = ( 50,  55,  75)

CAR_COLORS = {
    "red":    (220,  60,  50),
    "blue":   ( 60, 130, 255),
    "green":  ( 60, 200,  90),
    "yellow": (255, 200,  40),
    "white":  (230, 235, 245),
}


# ─────────────────────────────────────────────────────────────────────────────
# Reusable drawing primitives
# ─────────────────────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("dejavusans", size, bold=bold)


def _text(surface, text: str, font, color, center):
    surf = font.render(text, True, color)
    surface.blit(surf, surf.get_rect(center=center))
    return surf.get_rect(center=center)


def _button(surface, label: str, rect: pygame.Rect,
            font, bg=C_ROAD, fg=C_WHITE, border=C_BORDER,
            hover=False, active=False) -> pygame.Rect:
    if active:
        bg = C_ACCENT; fg = C_BG
    elif hover:
        bg = C_BORDER
    pygame.draw.rect(surface, bg,     rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)
    _text(surface, label, font, fg, rect.center)
    return rect


def _panel(surface, rect: pygame.Rect, alpha=220):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((*C_PANEL, alpha))
    surface.blit(s, rect.topleft)
    pygame.draw.rect(surface, C_BORDER, rect, 1, border_radius=10)


def _draw_car_icon(surface, cx, cy, color, w=28, h=44):
    """Small car icon used in menus."""
    body = pygame.Rect(cx - w//2, cy - h//2, w, h)
    pygame.draw.rect(surface, color, body, border_radius=6)
    # windshield
    ws = pygame.Rect(cx - w//2 + 4, cy - h//2 + 6, w - 8, 10)
    pygame.draw.rect(surface, (180, 220, 255, 180), ws, border_radius=3)
    # wheels
    for wx, wy in [(cx - w//2 - 3, cy - 12), (cx + w//2 - 5, cy - 12),
                   (cx - w//2 - 3, cy + 6),  (cx + w//2 - 5, cy + 6)]:
        pygame.draw.rect(surface, (30, 30, 30), pygame.Rect(wx, wy, 8, 10), border_radius=2)


# ─────────────────────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────────────────────

def main_menu(screen: pygame.Surface, settings: dict) -> str:
    """Returns: 'play' | 'leaderboard' | 'settings' | 'quit'"""
    W, H   = screen.get_size()
    clock  = pygame.time.Clock()
    f_title = _font(52, bold=True)
    f_sub   = _font(18)
    f_btn   = _font(20, bold=True)

    options = [
        ("▶  PLAY",        "play"),
        ("🏆  LEADERBOARD", "leaderboard"),
        ("⚙  SETTINGS",    "settings"),
        ("✕  QUIT",        "quit"),
    ]
    btn_w, btn_h = 280, 52
    btn_x = W // 2 - btn_w // 2
    btn_rects = [
        pygame.Rect(btn_x, H // 2 - 10 + i * (btn_h + 12), btn_w, btn_h)
        for i in range(len(options))
    ]

    # Animated road lines
    road_y = [H // 3 + i * 60 for i in range(8)]
    tick = 0

    while True:
        tick += 1
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(btn_rects):
                    if rect.collidepoint(mx, my):
                        return options[i][1]

        # BG
        screen.fill(C_BG)

        # Animated dashes down the centre
        for ry in road_y:
            y = (ry + tick * 3) % H
            pygame.draw.rect(screen, C_BORDER, pygame.Rect(W//2 - 3, y, 6, 28), border_radius=2)

        # Title
        _text(screen, "RACER", f_title, C_ACCENT, (W//2, H//4))
        _text(screen, "Extended Edition", f_sub, C_MUTED, (W//2, H//4 + 52))

        # Decorative car icons
        _draw_car_icon(screen, W//2 - 160, H//4 + 8, CAR_COLORS[settings["car_color"]])
        _draw_car_icon(screen, W//2 + 160, H//4 + 8, CAR_COLORS[settings["car_color"]])

        for i, (label, _) in enumerate(options):
            hover = btn_rects[i].collidepoint(mx, my)
            _button(screen, label, btn_rects[i], f_btn, hover=hover)

        # Player name hint
        _text(screen, f"Player: {settings['player_name']}  |  Diff: {settings['difficulty'].title()}",
              f_sub, C_MUTED, (W//2, H - 30))

        pygame.display.flip()
        clock.tick(60)


# ─────────────────────────────────────────────────────────────────────────────
# Name Entry
# ─────────────────────────────────────────────────────────────────────────────

def name_entry_screen(screen: pygame.Surface, default_name: str) -> str:
    """Lets the player enter their name. Returns the entered name."""
    W, H   = screen.get_size()
    clock  = pygame.time.Clock()
    f_hdr  = _font(32, bold=True)
    f_txt  = _font(28)
    f_hint = _font(16)
    name   = default_name
    cursor_tick = 0

    while True:
        cursor_tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    return name.strip()
                elif event.key == pygame.K_ESCAPE:
                    return default_name
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    ch = event.unicode
                    if ch.isprintable() and len(name) < 16:
                        name += ch

        screen.fill(C_BG)
        _panel(screen, pygame.Rect(W//2 - 220, H//2 - 120, 440, 240))
        _text(screen, "Enter Your Name", f_hdr, C_ACCENT, (W//2, H//2 - 80))

        # Input box
        box = pygame.Rect(W//2 - 160, H//2 - 20, 320, 50)
        pygame.draw.rect(screen, C_ROAD, box, border_radius=6)
        pygame.draw.rect(screen, C_ACCENT, box, 2, border_radius=6)
        cursor = "|" if (cursor_tick // 30) % 2 == 0 else " "
        display = name + cursor
        _text(screen, display, f_txt, C_WHITE, box.center)

        _text(screen, "Press ENTER to confirm", f_hint, C_MUTED, (W//2, H//2 + 60))
        pygame.display.flip()
        clock.tick(60)


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard Screen
# ─────────────────────────────────────────────────────────────────────────────

def leaderboard_screen(screen: pygame.Surface, entries: list) -> str:
    """Returns: 'menu'"""
    W, H   = screen.get_size()
    clock  = pygame.time.Clock()
    f_hdr  = _font(34, bold=True)
    f_row  = _font(18)
    f_sub  = _font(15)
    f_btn  = _font(20, bold=True)
    back_rect = pygame.Rect(W//2 - 100, H - 70, 200, 44)

    medals = ["🥇", "🥈", "🥉"]

    while True:
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
                return "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(mx, my):
                    return "menu"

        screen.fill(C_BG)
        _text(screen, "🏆  LEADERBOARD", f_hdr, C_ACCENT, (W//2, 45))

        # Table header
        header_y = 90
        cols = [80, 260, 380, 480, 570]
        headers = ["#", "Name", "Score", "Distance", "Coins"]
        for i, (cx, hdr) in enumerate(zip(cols, headers)):
            surf = f_sub.render(hdr, True, C_MUTED)
            screen.blit(surf, surf.get_rect(centerx=cx, y=header_y))

        pygame.draw.line(screen, C_BORDER, (40, header_y + 22), (W - 40, header_y + 22))

        if not entries:
            _text(screen, "No scores yet. Play to set a record!", f_row, C_MUTED, (W//2, H//2))
        else:
            for i, entry in enumerate(entries[:10]):
                row_y = header_y + 36 + i * 38
                row_color = C_ACCENT if i == 0 else (C_WHITE if i < 3 else C_MUTED)
                rank_label = medals[i] if i < 3 else str(i + 1)

                for cx, val in zip(cols, [
                    rank_label,
                    entry.get("name", "?")[:14],
                    str(entry.get("score", 0)),
                    f"{entry.get('distance', 0)} m",
                    str(entry.get("coins", 0)),
                ]):
                    surf = f_row.render(val, True, row_color)
                    screen.blit(surf, surf.get_rect(centerx=cx, y=row_y))

                if i % 2 == 0:
                    s = pygame.Surface((W - 80, 34), pygame.SRCALPHA)
                    s.fill((255, 255, 255, 8))
                    screen.blit(s, (40, row_y - 4))

        hover = back_rect.collidepoint(mx, my)
        _button(screen, "← BACK", back_rect, f_btn, hover=hover)
        pygame.display.flip()
        clock.tick(60)


# ─────────────────────────────────────────────────────────────────────────────
# Settings Screen
# ─────────────────────────────────────────────────────────────────────────────

def settings_screen(screen: pygame.Surface, settings: dict) -> tuple:
    """
    Returns (action: str, updated_settings: dict)
    action is always 'menu'.
    """
    W, H   = screen.get_size()
    clock  = pygame.time.Clock()
    f_hdr  = _font(34, bold=True)
    f_lbl  = _font(20, bold=True)
    f_opt  = _font(18)
    f_btn  = _font(20, bold=True)

    s = settings.copy()

    back_rect = pygame.Rect(W//2 - 100, H - 70, 200, 44)

    # Row definitions: (label, setting_key, options_list)
    rows = [
        ("Sound",      "sound",      [True, False]),
        ("Car Color",  "car_color",  ["red", "blue", "green", "yellow", "white"]),
        ("Difficulty", "difficulty", ["easy", "normal", "hard"]),
    ]

    row_y_start = 130
    row_h = 72

    def option_rects(row_idx, n_opts):
        btn_w = min(110, (W - 200) // n_opts)
        total = btn_w * n_opts + 8 * (n_opts - 1)
        start_x = W // 2 - total // 2
        y = row_y_start + row_idx * row_h + 28
        return [pygame.Rect(start_x + i * (btn_w + 8), y, btn_w, 34) for i in range(n_opts)]

    while True:
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu", s
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(mx, my):
                    return "menu", s
                for ri, (_, key, opts) in enumerate(rows):
                    for oi, rect in enumerate(option_rects(ri, len(opts))):
                        if rect.collidepoint(mx, my):
                            s[key] = opts[oi]

        screen.fill(C_BG)
        _text(screen, "⚙  SETTINGS", f_hdr, C_ACCENT, (W//2, 45))

        for ri, (label, key, opts) in enumerate(rows):
            row_y = row_y_start + ri * row_h
            _text(screen, label, f_lbl, C_WHITE, (W//2, row_y + 12))

            for oi, rect in enumerate(option_rects(ri, len(opts))):
                val     = opts[oi]
                is_act  = (s[key] == val)
                hover   = rect.collidepoint(mx, my) and not is_act
                disp    = str(val).title() if isinstance(val, str) else ("ON" if val else "OFF")
                # Colour preview for car_color
                if key == "car_color" and isinstance(val, str) and val in CAR_COLORS:
                    _button(screen, disp, rect, f_opt,
                            bg=CAR_COLORS[val] if is_act else C_ROAD,
                            fg=C_BG if is_act else C_WHITE,
                            border=CAR_COLORS[val], hover=hover, active=False)
                else:
                    _button(screen, disp, rect, f_opt, hover=hover, active=is_act)

        hover = back_rect.collidepoint(mx, my)
        _button(screen, "✓  SAVE & BACK", back_rect, f_btn, hover=hover)
        pygame.display.flip()
        clock.tick(60)


# ─────────────────────────────────────────────────────────────────────────────
# Game Over Screen
# ─────────────────────────────────────────────────────────────────────────────

def game_over_screen(screen: pygame.Surface, stats: dict) -> str:
    """
    stats = {score, distance, coins, name}
    Returns: 'retry' | 'menu'
    """
    W, H   = screen.get_size()
    clock  = pygame.time.Clock()
    f_hdr  = _font(44, bold=True)
    f_stat = _font(22)
    f_btn  = _font(22, bold=True)

    btn_w, btn_h = 220, 52
    retry_rect = pygame.Rect(W//2 - btn_w - 16, H * 2//3, btn_w, btn_h)
    menu_rect  = pygame.Rect(W//2 + 16,          H * 2//3, btn_w, btn_h)

    alpha   = 0
    fade_in = True

    while True:
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_m:
                    return "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if retry_rect.collidepoint(mx, my):
                    return "retry"
                if menu_rect.collidepoint(mx, my):
                    return "menu"

        if fade_in:
            alpha = min(alpha + 8, 255)
            if alpha >= 255:
                fade_in = False

        screen.fill(C_BG)

        # Crash flash overlay
        flash = pygame.Surface((W, H), pygame.SRCALPHA)
        flash.fill((200, 40, 40, max(0, 80 - alpha // 3)))
        screen.blit(flash, (0, 0))

        _text(screen, "GAME OVER", f_hdr, C_RED, (W//2, H//5))
        _text(screen, stats.get("name", "Player"), f_stat, C_MUTED, (W//2, H//5 + 58))

        stat_lines = [
            ("Score",    f"{stats.get('score', 0):,}",   C_ACCENT),
            ("Distance", f"{stats.get('distance', 0)} m", C_WHITE),
            ("Coins",    str(stats.get("coins", 0)),      C_GREEN),
        ]
        for i, (lbl, val, col) in enumerate(stat_lines):
            cy = H // 2 - 20 + i * 44
            _text(screen, f"{lbl}:", f_stat, C_MUTED, (W//2 - 80, cy))
            _text(screen, val,       f_stat, col,      (W//2 + 80, cy))

        hover_r = retry_rect.collidepoint(mx, my)
        hover_m = menu_rect.collidepoint(mx, my)
        _button(screen, "↺  RETRY [R]",     retry_rect, f_btn, hover=hover_r)
        _button(screen, "⌂  MENU [M]",      menu_rect,  f_btn, hover=hover_m)

        # Fade-in overlay
        if alpha < 255:
            fade = pygame.Surface((W, H))
            fade.fill(C_BG)
            fade.set_alpha(255 - alpha)
            screen.blit(fade, (0, 0))

        pygame.display.flip()
        clock.tick(60)
