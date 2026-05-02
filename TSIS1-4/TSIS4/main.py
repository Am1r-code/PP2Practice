# main.py — Entry point: screens, main loop, settings I/O

import sys
import json
import pygame

import db
from game import GameState, PowerUp, UP, DOWN, LEFT, RIGHT
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, CELL_SIZE, COLS, ROWS,
    BG_COLOR, GRID_COLOR, PANEL_COLOR, WHITE, BLACK,
    GREEN, DARK_GREEN, RED, GRAY, LIGHT_GRAY, DARK_GRAY,
    YELLOW, ORANGE, CYAN, PURPLE, BLUE,
    POWERUP_COLORS,
)

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {"snake_color": [60, 200, 80], "grid_overlay": True, "sound": False}


# ══════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════

def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
        # fill missing keys with defaults
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(s: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=4)
    except Exception as e:
        print(f"[settings] save error: {e}")


def draw_bg(surface, settings):
    surface.fill(BG_COLOR)
    if settings.get("grid_overlay", True):
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(surface, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))


class Button:
    def __init__(self, rect, text, font,
                 color=DARK_GREEN, hover=(50, 160, 70), text_color=WHITE):
        self.rect       = pygame.Rect(rect)
        self.text       = text
        self.font       = font
        self.color      = color
        self.hover      = hover
        self.text_color = text_color

    def draw(self, surface):
        mx, my = pygame.mouse.get_pos()
        col = self.hover if self.rect.collidepoint(mx, my) else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        lbl = self.font.render(self.text, True, self.text_color)
        surface.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ══════════════════════════════════════════════
# Screen: Username entry
# ══════════════════════════════════════════════

def screen_username(surface, clock, font_big, font_med, font_small, settings) -> str | None:
    username    = ""
    error_msg   = ""
    input_rect  = pygame.Rect(WINDOW_WIDTH // 2 - 160, 280, 320, 50)
    btn_play    = Button((WINDOW_WIDTH // 2 - 80, 370, 160, 48), "PLAY", font_med)
    btn_quit    = Button((WINDOW_WIDTH // 2 - 80, 435, 160, 48), "QUIT", font_med,
                         color=(100, 30, 30), hover=(160, 50, 50))

    while True:
        draw_bg(surface, settings)

        # title
        title = font_big.render("🐍  SNAKE", True, GREEN)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 120)))
        sub = font_small.render("TSIS 4  ·  Database Edition", True, LIGHT_GRAY)
        surface.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 170)))

        # username label
        lbl = font_med.render("Enter your username:", True, WHITE)
        surface.blit(lbl, lbl.get_rect(center=(WINDOW_WIDTH // 2, 245)))

        # input box
        active_color = GREEN if len(username) > 0 else GRAY
        pygame.draw.rect(surface, PANEL_COLOR, input_rect, border_radius=8)
        pygame.draw.rect(surface, active_color, input_rect, 2, border_radius=8)
        name_surf = font_med.render(username + "|", True, WHITE)
        surface.blit(name_surf, (input_rect.x + 12, input_rect.y + 10))

        if error_msg:
            err = font_small.render(error_msg, True, RED)
            surface.blit(err, err.get_rect(center=(WINDOW_WIDTH // 2, 340)))

        btn_play.draw(surface)
        btn_quit.draw(surface)

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if username.strip():
                        return username.strip()
                    else:
                        error_msg = "Username cannot be empty."
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    if len(username) < 20 and event.unicode.isprintable():
                        username += event.unicode
            if btn_play.clicked(event):
                if username.strip():
                    return username.strip()
                else:
                    error_msg = "Username cannot be empty."
            if btn_quit.clicked(event):
                return None


# ══════════════════════════════════════════════
# Screen: Main Menu
# ══════════════════════════════════════════════

def screen_main_menu(surface, clock, font_big, font_med, font_small, settings) -> str:
    cx = WINDOW_WIDTH // 2
    btn_play  = Button((cx - 100, 270, 200, 52), "PLAY",        font_med)
    btn_lb    = Button((cx - 100, 340, 200, 52), "LEADERBOARD", font_med,
                       color=(40, 80, 140), hover=(60, 110, 190))
    btn_set   = Button((cx - 100, 410, 200, 52), "SETTINGS",    font_med,
                       color=(80, 60, 120), hover=(110, 80, 160))
    btn_quit  = Button((cx - 100, 480, 200, 52), "QUIT",        font_med,
                       color=(100, 30, 30), hover=(160, 50, 50))

    while True:
        draw_bg(surface, settings)
        title = font_big.render("🐍  SNAKE", True, GREEN)
        surface.blit(title, title.get_rect(center=(cx, 120)))
        sub = font_small.render("Use arrow keys · Collect food · Survive", True, LIGHT_GRAY)
        surface.blit(sub, sub.get_rect(center=(cx, 185)))

        for btn in (btn_play, btn_lb, btn_set, btn_quit):
            btn.draw(surface)

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if btn_play.clicked(event):
                return "play"
            if btn_lb.clicked(event):
                return "leaderboard"
            if btn_set.clicked(event):
                return "settings"
            if btn_quit.clicked(event):
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"


# ══════════════════════════════════════════════
# Screen: Leaderboard
# ══════════════════════════════════════════════

def screen_leaderboard(surface, clock, font_big, font_med, font_small, settings, db_ok: bool):
    rows   = db.get_leaderboard(10) if db_ok else []
    cx     = WINDOW_WIDTH // 2
    btn_back = Button((cx - 80, 550, 160, 44), "BACK", font_med,
                      color=(80, 60, 120), hover=(110, 80, 160))

    while True:
        draw_bg(surface, settings)
        title = font_big.render("🏆  LEADERBOARD", True, YELLOW)
        surface.blit(title, title.get_rect(center=(cx, 55)))

        if not db_ok:
            msg = font_med.render("Database not connected.", True, RED)
            surface.blit(msg, msg.get_rect(center=(cx, 300)))
        elif not rows:
            msg = font_med.render("No records yet — be the first!", True, LIGHT_GRAY)
            surface.blit(msg, msg.get_rect(center=(cx, 300)))
        else:
            headers = ["#", "Username", "Score", "Level", "Date"]
            col_x   = [60, 140, 400, 490, 590]
            # header
            for h, x in zip(headers, col_x):
                hs = font_small.render(h, True, YELLOW)
                surface.blit(hs, (x, 105))
            pygame.draw.line(surface, GRAY, (50, 125), (750, 125), 1)

            for i, row in enumerate(rows):
                y   = 140 + i * 38
                col = WHITE if i % 2 == 0 else LIGHT_GRAY
                vals = [
                    str(row["rank"]),
                    row["username"][:14],
                    str(row["score"]),
                    str(row["level_reached"]),
                    row["played_at"],
                ]
                for val, x in zip(vals, col_x):
                    vs = font_small.render(val, True, col)
                    surface.blit(vs, (x, y))

        btn_back.draw(surface)
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if btn_back.clicked(event):
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return


# ══════════════════════════════════════════════
# Screen: Settings
# ══════════════════════════════════════════════

PRESET_COLORS = [
    (60,  200,  80),   # default green
    (80,  160, 220),   # blue
    (220, 200,  60),   # yellow
    (200,  80, 200),   # pink/purple
    (220, 100,  50),   # orange
    (200, 200, 200),   # white
]


def screen_settings(surface, clock, font_big, font_med, font_small, settings):
    local    = dict(settings)
    cx       = WINDOW_WIDTH // 2
    btn_save = Button((cx - 100, 500, 200, 50), "SAVE & BACK", font_med,
                      color=(40, 120, 60), hover=(60, 160, 80))

    while True:
        draw_bg(surface, local)
        title = font_big.render("⚙  SETTINGS", True, CYAN)
        surface.blit(title, title.get_rect(center=(cx, 60)))

        # Grid toggle
        grid_lbl = font_med.render(
            f"Grid Overlay:   {'ON' if local['grid_overlay'] else 'OFF'}", True, WHITE)
        surface.blit(grid_lbl, (cx - 180, 155))
        btn_grid = pygame.Rect(cx + 130, 150, 100, 40)
        pygame.draw.rect(surface, (60, 100, 60) if local["grid_overlay"] else (80, 40, 40),
                         btn_grid, border_radius=6)
        pygame.draw.rect(surface, WHITE, btn_grid, 2, border_radius=6)
        tgl = font_small.render("Toggle", True, WHITE)
        surface.blit(tgl, tgl.get_rect(center=btn_grid.center))

        # Sound toggle
        sound_lbl = font_med.render(
            f"Sound:              {'ON' if local['sound'] else 'OFF'}", True, WHITE)
        surface.blit(sound_lbl, (cx - 180, 230))
        btn_sound = pygame.Rect(cx + 130, 225, 100, 40)
        pygame.draw.rect(surface, (60, 100, 60) if local["sound"] else (80, 40, 40),
                         btn_sound, border_radius=6)
        pygame.draw.rect(surface, WHITE, btn_sound, 2, border_radius=6)
        tgl2 = font_small.render("Toggle", True, WHITE)
        surface.blit(tgl2, tgl2.get_rect(center=btn_sound.center))

        # Color picker
        col_lbl = font_med.render("Snake Color:", True, WHITE)
        surface.blit(col_lbl, (cx - 180, 305))
        sw = 44
        for i, preset in enumerate(PRESET_COLORS):
            rx = cx - 180 + i * (sw + 6)
            ry = 345
            swatch = pygame.Rect(rx, ry, sw, sw)
            pygame.draw.rect(surface, preset, swatch, border_radius=6)
            if list(preset) == list(local["snake_color"]):
                pygame.draw.rect(surface, WHITE, swatch, 3, border_radius=6)

        btn_save.draw(surface)
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                settings.update(local)
                save_settings(settings)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_grid.collidepoint(event.pos):
                    local["grid_overlay"] = not local["grid_overlay"]
                if btn_sound.collidepoint(event.pos):
                    local["sound"] = not local["sound"]
                # color swatches
                for i, preset in enumerate(PRESET_COLORS):
                    rx = cx - 180 + i * (sw + 6)
                    ry = 345
                    if pygame.Rect(rx, ry, sw, sw).collidepoint(event.pos):
                        local["snake_color"] = list(preset)
                if btn_save.clicked(event):
                    settings.update(local)
                    save_settings(settings)
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                settings.update(local)
                save_settings(settings)
                return


# ══════════════════════════════════════════════
# HUD during gameplay
# ══════════════════════════════════════════════

def draw_hud(surface, state: GameState, personal_best: int,
             font_med, font_small, username: str):
    # semi-transparent side panel
    panel = pygame.Surface((160, WINDOW_HEIGHT), pygame.SRCALPHA)
    panel.fill((10, 10, 20, 200))
    surface.blit(panel, (WINDOW_WIDTH - 160, 0))

    x = WINDOW_WIDTH - 150
    y = 20

    def row(label, value, color=WHITE):
        nonlocal y
        ls = font_small.render(label, True, GRAY)
        vs = font_med.render(str(value), True, color)
        surface.blit(ls, (x, y));    y += 20
        surface.blit(vs, (x, y));    y += 32

    row("PLAYER", username[:12], CYAN)
    row("SCORE",  state.score, YELLOW)
    row("BEST",   personal_best, (180, 220, 100))
    row("LEVEL",  state.level, ORANGE)

    # active power-up indicator
    if state.active_effect:
        y += 10
        pname = {"speed_boost": "⚡ SPEED",
                 "slow_motion":  "❄ SLOW",
                 "shield":       "🛡 SHIELD"}.get(state.active_effect, "")
        pcol  = POWERUP_COLORS.get(state.active_effect, WHITE)
        ps    = font_small.render("POWER-UP", True, GRAY)
        pv    = font_med.render(pname, True, pcol)
        surface.blit(ps, (x, y)); y += 20
        surface.blit(pv, (x, y)); y += 32

        # time remaining bar
        if state.active_effect != PowerUp.KIND_SHIELD:
            elapsed  = pygame.time.get_ticks() - state.effect_start
            ratio    = max(0, 1 - elapsed / 5000)
            bar_rect = pygame.Rect(x, y, 130, 8)
            fill_rect= pygame.Rect(x, y, int(130 * ratio), 8)
            pygame.draw.rect(surface, DARK_GRAY, bar_rect, border_radius=4)
            pygame.draw.rect(surface, pcol, fill_rect, border_radius=4)
            y += 18

    # legend
    y = WINDOW_HEIGHT - 140
    for label, col in [("🔴 Normal", (240, 80, 80)),
                       ("⭐ Bonus x3", YELLOW),
                       ("☠ Poison", (120, 20, 20)),
                       ("⚡ Speed", ORANGE),
                       ("❄ Slow",  CYAN),
                       ("🛡 Shield", PURPLE)]:
        ls = font_small.render(label, True, col)
        surface.blit(ls, (x, y)); y += 20


# ══════════════════════════════════════════════
# Screen: Game Over
# ══════════════════════════════════════════════

def screen_game_over(surface, clock, font_big, font_med, font_small,
                     settings, score, level, personal_best) -> str:
    cx       = WINDOW_WIDTH // 2
    is_best  = score >= personal_best
    btn_retry = Button((cx - 110, 420, 200, 52), "RETRY",     font_med)
    btn_menu  = Button((cx + 110, 420, 200, 52), "MAIN MENU", font_med,
                       color=(40, 80, 140), hover=(60, 110, 190))

    while True:
        draw_bg(surface, settings)

        title = font_big.render("GAME OVER", True, RED)
        surface.blit(title, title.get_rect(center=(cx, 110)))

        lines = [
            (f"Score:  {score}",           YELLOW),
            (f"Level:  {level}",           WHITE),
            (f"Personal Best:  {personal_best}",
             GREEN if is_best else LIGHT_GRAY),
        ]
        if is_best and score > 0:
            nb = font_med.render("🎉 New personal best!", True, GREEN)
            surface.blit(nb, nb.get_rect(center=(cx, 195)))

        y = 240
        for text, col in lines:
            s = font_med.render(text, True, col)
            surface.blit(s, s.get_rect(center=(cx, y)))
            y += 52

        btn_retry.draw(surface)
        btn_menu.draw(surface)

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if btn_retry.clicked(event):
                return "retry"
            if btn_menu.clicked(event):
                return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key == pygame.K_ESCAPE:
                    return "menu"


# ══════════════════════════════════════════════
# Gameplay loop
# ══════════════════════════════════════════════

def run_game(surface, clock, font_med, font_small,
             settings, player_id, username, personal_best, db_ok) -> tuple:
    """
    Returns (final_score, final_level, new_personal_best).
    """
    state      = GameState(settings)
    best       = personal_best
    tick_event = pygame.USEREVENT + 1

    def set_timer():
        pygame.time.set_timer(tick_event, 1000 // state.current_fps())

    set_timer()

    running = True
    while running:
        clock.tick(120)   # rendering FPS — logic is event-driven

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.time.set_timer(tick_event, 0)
                return state.score, state.level, best

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP,    pygame.K_w): state.snake.set_direction(UP)
                if event.key in (pygame.K_DOWN,  pygame.K_s): state.snake.set_direction(DOWN)
                if event.key in (pygame.K_LEFT,  pygame.K_a): state.snake.set_direction(LEFT)
                if event.key in (pygame.K_RIGHT, pygame.K_d): state.snake.set_direction(RIGHT)
                if event.key == pygame.K_ESCAPE:
                    pygame.time.set_timer(tick_event, 0)
                    return state.score, state.level, best

            if event.type == tick_event:
                prev_fps = state.current_fps()
                state.update()
                if state.current_fps() != prev_fps:
                    set_timer()
                if state.over:
                    running = False

        # draw
        draw_bg(surface, settings)
        state.draw(surface, font_small)
        draw_hud(surface, state, best, font_med, font_small, username)
        pygame.display.flip()

    pygame.time.set_timer(tick_event, 0)

    # save to DB
    if db_ok and player_id is not None:
        db.save_session(player_id, state.score, state.level)
        best = max(best, state.score)

    return state.score, state.level, best


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock   = pygame.time.Clock()

    font_big   = pygame.font.SysFont("consolas", 56, bold=True)
    font_med   = pygame.font.SysFont("consolas", 28, bold=True)
    font_small = pygame.font.SysFont("consolas", 20)

    settings = load_settings()

    # DB init
    db_ok = db.init_db()
    if not db_ok:
        print("[main] Running without database (offline mode).")

    # username screen
    username = screen_username(surface, clock, font_big, font_med, font_small, settings)
    if username is None:
        pygame.quit()
        sys.exit()

    player_id     = db.get_or_create_player(username) if db_ok else None
    personal_best = db.get_personal_best(player_id)   if db_ok and player_id else 0

    # Main loop over screens
    current_screen = "menu"
    while True:
        if current_screen == "menu":
            action = screen_main_menu(surface, clock, font_big, font_med, font_small, settings)
            if action == "quit":
                break
            current_screen = action

        elif current_screen == "play":
            score, level, personal_best = run_game(
                surface, clock, font_med, font_small,
                settings, player_id, username, personal_best, db_ok
            )
            action = screen_game_over(
                surface, clock, font_big, font_med, font_small,
                settings, score, level, personal_best
            )
            if action == "quit":
                break
            current_screen = "play" if action == "retry" else "menu"

        elif current_screen == "leaderboard":
            screen_leaderboard(surface, clock, font_big, font_med, font_small,
                               settings, db_ok)
            current_screen = "menu"

        elif current_screen == "settings":
            screen_settings(surface, clock, font_big, font_med, font_small, settings)
            current_screen = "menu"

        else:
            current_screen = "menu"

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
