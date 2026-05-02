"""
snake.py — Practice 11: Snake Game (Extended)
===============================================
Built on top of Practice 10. New features:

  NEW ► Weighted food system
          Three food types with different point values and rarities:
            • Normal  (red)    — 1 pt,  weight 60 % — permanent
            • Bonus   (yellow) — 3 pts, weight 30 % — disappears after 5 s
            • Mega    (cyan)   — 5 pts, weight 10 % — disappears after 3.5 s

  NEW ► Disappearing food (timer)
          • Timed food shows a shrinking countdown bar underneath the cell.
          • In the last 1.5 s the item blinks rapidly to warn the player.
          • When a timed food expires it is replaced by a Normal food.

  Carried from Practice 10:
    • Border / wall collision detection
    • Random food placement (avoids walls and snake body)
    • Level system  (FOOD_PER_LEVEL items eaten → level up)
    • Speed increase per level
    • Score, level HUD + food legend
"""

import pygame
import random
import sys

# ──────────────────────────────────────────────
# Window / grid constants
# ──────────────────────────────────────────────
WINDOW_W = 640
WINDOW_H = 520
CELL     = 20
COLS     = WINDOW_W // CELL   # 32
ROWS     = WINDOW_H // CELL   # 26

# ──────────────────────────────────────────────
# Colour palette
# ──────────────────────────────────────────────
COL_BG        = (15,  20,  30)
COL_GRID      = (25,  32,  45)
COL_SNAKE_H   = (80, 220, 100)
COL_SNAKE_B   = (50, 160,  70)
COL_WALL      = (60,  65,  80)
COL_TEXT      = (220, 230, 240)
COL_SCORE_VAL = (255, 220,  60)
COL_LEVEL_VAL = (100, 200, 255)

# ──────────────────────────────────────────────
# Game-play parameters
# ──────────────────────────────────────────────
BASE_FPS       = 7     # starting speed (frames per second)
SPEED_INC      = 2     # extra FPS per level
FOOD_PER_LEVEL = 3     # items eaten before level-up

# ──────────────────────────────────────────────
# Weighted food type definitions
# ──────────────────────────────────────────────
# Each dictionary fully describes one food variant.
# "weight"  – relative probability of being chosen when a new food spawns
# "points"  – score added when the snake eats this food
# "color"   – RGB colour of the food cell
# "timed"   – True → item disappears after ttl_ms milliseconds
# "ttl_ms"  – lifetime in ms (None for permanent food)
# "label"   – tiny text drawn on the food cell showing its value

FOOD_TYPES = [
    {
        "name":   "normal",
        "weight": 60,                      # 60 % of new spawns
        "points": 1,
        "color":  (230,  70,  70),         # red
        "timed":  False,
        "ttl_ms": None,
        "label":  "x1",
    },
    {
        "name":   "bonus",
        "weight": 30,                      # 30 % of new spawns
        "points": 3,
        "color":  (240, 220,  40),         # yellow
        "timed":  True,
        "ttl_ms": 5_000,                   # vanishes in 5 s
        "label":  "x3",
    },
    {
        "name":   "mega",
        "weight": 10,                      # 10 % of new spawns
        "points": 5,
        "color":  ( 60, 220, 220),         # cyan
        "timed":  True,
        "ttl_ms": 3_500,                   # vanishes in 3.5 s
        "label":  "x5",
    },
]

# Flat list of weights extracted for random.choices()
_WEIGHTS = [ft["weight"] for ft in FOOD_TYPES]

# Direction vectors (dx, dy) on the grid
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# Reverse-direction map — prevents 180° U-turns
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


# ══════════════════════════════════════════════
# FoodItem class
# ══════════════════════════════════════════════
class FoodItem:
    """
    One food pellet on the grid.
    Handles its own lifetime tracking and rendering.
    """

    def __init__(self, col: int, row: int, food_type: dict):
        # Grid position
        self.col = col
        self.row = row

        # Type metadata (reference to one entry in FOOD_TYPES)
        self.food_type = food_type
        self.points    = food_type["points"]
        self.color     = food_type["color"]
        self.timed     = food_type["timed"]
        self.ttl_ms    = food_type["ttl_ms"]

        # Record spawn time only for timed items
        self.spawned_at = pygame.time.get_ticks() if self.timed else None

    # ── Lifetime helpers ──────────────────────
    def age_ms(self) -> int:
        """Milliseconds elapsed since this item appeared on the board."""
        return (pygame.time.get_ticks() - self.spawned_at) if self.timed else 0

    def is_expired(self) -> bool:
        """True once the item has outlived its ttl_ms."""
        return self.timed and self.age_ms() >= self.ttl_ms

    def remaining_ratio(self) -> float:
        """
        Fraction of lifetime still remaining.
        1.0 = just spawned, 0.0 = expired.
        """
        if not self.timed or self.ttl_ms == 0:
            return 1.0
        return max(0.0, 1.0 - self.age_ms() / self.ttl_ms)

    # ── Drawing ───────────────────────────────
    def draw(self, surface: pygame.Surface, font_tiny: pygame.font.Font):
        """
        Draw the food cell.
        Timed food also shows:
          • A colour-shifting countdown bar at the bottom of the cell.
          • A rapid blink in the last 1.5 s of its life.
        """
        x = self.col * CELL
        y = self.row * CELL

        # Blink when less than 1500 ms remain
        if self.timed:
            remaining_ms = self.ttl_ms - self.age_ms()
            if remaining_ms < 1_500:
                # Toggle every 200 ms → blink
                if (pygame.time.get_ticks() // 200) % 2 == 1:
                    return   # skip this frame (invisible half of blink)

        # Food body — slightly inset rounded square
        body_rect = pygame.Rect(x + 3, y + 3, CELL - 6, CELL - 6)
        pygame.draw.rect(surface, self.color, body_rect, border_radius=4)

        # Point label centred on cell
        lbl = font_tiny.render(self.food_type["label"], True, (10, 10, 10))
        surface.blit(lbl, (
            x + CELL // 2 - lbl.get_width()  // 2,
            y + CELL // 2 - lbl.get_height() // 2,
        ))

        # Countdown bar (timed food only)
        if self.timed:
            ratio    = self.remaining_ratio()
            bar_w    = CELL - 4
            bar_x    = x + 2
            bar_y    = y + CELL - 4   # pinned to bottom of cell
            filled_w = int(bar_w * ratio)

            # Grey background track
            pygame.draw.rect(surface, (50, 50, 50),
                             (bar_x, bar_y, bar_w, 3))
            # Filled portion: green → red as time runs out
            bar_color = (
                int(255 * (1 - ratio)),   # R: increases as ratio falls
                int(200 * ratio),         # G: decreases as ratio falls
                0,                        # B: always 0
            )
            if filled_w > 0:
                pygame.draw.rect(surface, bar_color,
                                 (bar_x, bar_y, filled_w, 3))


# ══════════════════════════════════════════════
# Spawning helper
# ══════════════════════════════════════════════
def spawn_food(snake_body: list, existing: list | None = None) -> FoodItem:
    """
    Choose a free cell (not occupied by the wall, snake, or existing food),
    then pick a weighted-random food type and return a new FoodItem.
    """
    # Collect all cells that are currently in use
    occupied = set(snake_body)
    if existing:
        occupied |= {(f.col, f.row) for f in existing}

    # Inner grid — excludes the 1-cell border wall
    free = [
        (c, r)
        for c in range(1, COLS - 1)
        for r in range(1, ROWS - 1)
        if (c, r) not in occupied
    ]
    # Fallback: centre cell if board is somehow full
    if not free:
        free = [(COLS // 2, ROWS // 2)]

    col, row   = random.choice(free)
    food_type  = random.choices(FOOD_TYPES, weights=_WEIGHTS, k=1)[0]
    return FoodItem(col, row, food_type)


# ══════════════════════════════════════════════
# Rendering helpers
# ══════════════════════════════════════════════
def draw_cell(surface, color, col, row, shrink=2):
    """Draw a filled, slightly rounded cell at grid (col, row)."""
    rect = pygame.Rect(
        col * CELL + shrink,
        row * CELL + shrink,
        CELL - shrink * 2,
        CELL - shrink * 2,
    )
    pygame.draw.rect(surface, color, rect, border_radius=4)


def draw_grid(surface):
    """Faint grid lines across the whole window."""
    for x in range(0, WINDOW_W, CELL):
        pygame.draw.line(surface, COL_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(surface, COL_GRID, (0, y), (WINDOW_W, y))


def draw_walls(surface):
    """1-cell border wall rendered as dark tiles."""
    for c in range(COLS):
        draw_cell(surface, COL_WALL, c, 0,        shrink=1)
        draw_cell(surface, COL_WALL, c, ROWS - 1, shrink=1)
    for r in range(1, ROWS - 1):
        draw_cell(surface, COL_WALL, 0,        r, shrink=1)
        draw_cell(surface, COL_WALL, COLS - 1, r, shrink=1)


def draw_snake(surface, body):
    """Render snake from tail to head so the head always appears on top."""
    for i, (c, r) in enumerate(reversed(body)):
        color = COL_SNAKE_H if i == len(body) - 1 else COL_SNAKE_B
        draw_cell(surface, color, c, r)


def draw_hud(surface, font, font_tiny, score, level, food_count):
    """Score / level panel (top-left) and food type legend (top-right)."""

    # Semi-transparent score panel
    panel = pygame.Surface((230, 72), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 130))
    surface.blit(panel, (8, 8))

    surface.blit(font.render("SCORE", True, COL_TEXT),         (16, 12))
    surface.blit(font.render(str(score), True, COL_SCORE_VAL), (100, 12))
    surface.blit(font.render("LEVEL", True, COL_TEXT),         (16, 42))
    surface.blit(font.render(str(level), True, COL_LEVEL_VAL), (100, 42))

    # Level progress bar
    ratio = food_count / FOOD_PER_LEVEL
    pygame.draw.rect(surface, (50, 50, 70),    (152, 48, 78, 12), border_radius=4)
    pygame.draw.rect(surface, COL_LEVEL_VAL,
                     (152, 48, int(78 * ratio), 12), border_radius=4)

    # Food legend — top-right corner shows each type, colour, and timer info
    lx = WINDOW_W - 112
    ly = 10
    leg_h  = len(FOOD_TYPES) * 22 + 8
    leg_bg = pygame.Surface((106, leg_h), pygame.SRCALPHA)
    leg_bg.fill((0, 0, 0, 130))
    surface.blit(leg_bg, (lx - 4, ly))

    for i, ft in enumerate(FOOD_TYPES):
        y = ly + 4 + i * 22
        # Colour swatch
        pygame.draw.rect(surface, ft["color"], (lx, y + 2, 14, 14), border_radius=3)
        # Text description
        timer_str = f" {ft['ttl_ms'] // 1000}s" if ft["timed"] else " perm"
        desc = font_tiny.render(
            f"{ft['label']} {ft['name']}{timer_str}", True, COL_TEXT)
        surface.blit(desc, (lx + 18, y))


# ══════════════════════════════════════════════
# Game Over overlay
# ══════════════════════════════════════════════
def show_game_over(surface, font_big, font_sm, score, level) -> bool:
    """Render game-over screen; return True to restart."""
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    cx = WINDOW_W // 2

    t = font_big.render("GAME OVER", True, (230, 60, 60))
    surface.blit(t, t.get_rect(center=(cx, WINDOW_H // 2 - 60)))

    s = font_sm.render(f"Score: {score}   Level: {level}", True, COL_TEXT)
    surface.blit(s, s.get_rect(center=(cx, WINDOW_H // 2)))

    h = font_sm.render("R = retry   Q = quit", True, (150, 150, 170))
    surface.blit(h, h.get_rect(center=(cx, WINDOW_H // 2 + 50)))

    pygame.display.flip()

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r: return True
                if ev.key == pygame.K_q:
                    pygame.quit(); sys.exit()


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Snake — Practice 11")
    clock = pygame.time.Clock()

    font_hud  = pygame.font.SysFont("consolas", 22, bold=True)
    font_tiny = pygame.font.SysFont("consolas", 11, bold=True)
    font_big  = pygame.font.SysFont("consolas", 52, bold=True)
    font_sm   = pygame.font.SysFont("consolas", 26)

    # ── Build fresh game state ─────────────────
    def new_game() -> dict:
        sc, sr = COLS // 2, ROWS // 2
        body   = [(sc, sr), (sc - 1, sr), (sc - 2, sr)]
        return {
            "body":       body,
            "direction":  RIGHT,
            "next_dir":   RIGHT,
            "foods":      [spawn_food(body)],  # start with one food item
            "score":      0,
            "level":      1,
            "food_count": 0,
            "alive":      True,
        }

    state = new_game()

    # ── Main game loop ─────────────────────────
    while True:

        # 1. Input
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                key_map = {
                    pygame.K_UP:    UP,    pygame.K_w: UP,
                    pygame.K_DOWN:  DOWN,  pygame.K_s: DOWN,
                    pygame.K_LEFT:  LEFT,  pygame.K_a: LEFT,
                    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
                }
                if ev.key in key_map:
                    d = key_map[ev.key]
                    if d != OPPOSITE[state["direction"]]:
                        state["next_dir"] = d

        # 2. Game logic
        if state["alive"]:
            state["direction"] = state["next_dir"]
            dx, dy   = state["direction"]
            hc, hr   = state["body"][0]
            new_head = (hc + dx, hr + dy)
            nc, nr   = new_head

            # Border collision → die
            if nc <= 0 or nc >= COLS - 1 or nr <= 0 or nr >= ROWS - 1:
                state["alive"] = False

            # Self collision → die
            elif new_head in state["body"]:
                state["alive"] = False

            else:
                state["body"].insert(0, new_head)   # move head forward

                # Check whether the new head overlaps any food item
                eaten = next(
                    (f for f in state["foods"] if (f.col, f.row) == new_head),
                    None
                )
                if eaten:
                    state["score"]      += eaten.points  # weighted score
                    state["food_count"] += 1
                    state["foods"].remove(eaten)

                    # Level up when enough food eaten
                    if state["food_count"] >= FOOD_PER_LEVEL:
                        state["level"]      += 1
                        state["food_count"]  = 0

                    # Spawn replacement food
                    state["foods"].append(spawn_food(state["body"], state["foods"]))
                    # Snake grows: do NOT pop the tail
                else:
                    state["body"].pop()   # no growth → remove tail

            # Handle expired timed food items
            # For each expired item: remove it and replace with a Normal food
            # so the board always has at least one item available.
            normal_type = next(ft for ft in FOOD_TYPES if ft["name"] == "normal")
            expired = [f for f in state["foods"] if f.is_expired()]
            for f in expired:
                state["foods"].remove(f)
                # Spawn a fresh position, then force Normal type
                replacement = spawn_food(state["body"], state["foods"])
                state["foods"].append(
                    FoodItem(replacement.col, replacement.row, normal_type)
                )

        # 3. Render
        screen.fill(COL_BG)
        draw_grid(screen)
        draw_walls(screen)

        for food in state["foods"]:
            food.draw(screen, font_tiny)

        draw_snake(screen, state["body"])
        draw_hud(screen, font_hud, font_tiny,
                 state["score"], state["level"], state["food_count"])

        pygame.display.flip()

        # 4. Game Over check
        if not state["alive"]:
            if show_game_over(screen, font_big, font_sm,
                              state["score"], state["level"]):
                state = new_game()

        # 5. Speed tied to level
        clock.tick(BASE_FPS + (state["level"] - 1) * SPEED_INC)


if __name__ == "__main__":
    main()
