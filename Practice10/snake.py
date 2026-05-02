"""
snake.py — Practice 10: Snake Game
===================================
Features implemented:
  • Border / wall collision detection  → game over if snake leaves arena
  • Random food placement              → never spawns on a wall or the snake body
  • Level system                       → level up every 3 food items collected
  • Speed increase per level           → FPS rises with each level
  • Score & level counter              → displayed on-screen at all times
  • Fully commented code
"""

import pygame
import random
import sys

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
WINDOW_W  = 640          # window width  in pixels
WINDOW_H  = 520          # window height in pixels
CELL      = 20           # size of one grid cell (snake body / food)
COLS      = WINDOW_W // CELL   # number of columns in the grid
ROWS      = WINDOW_H // CELL   # number of rows    in the grid

# Colour palette
COL_BG        = (15,  20,  30)   # dark navy background
COL_GRID      = (25,  32,  45)   # subtle grid lines
COL_SNAKE_H   = (80, 220, 100)   # bright green head
COL_SNAKE_B   = (50, 160,  70)   # darker green body
COL_FOOD      = (240,  70,  70)  # red food
COL_WALL      = (60,   65,  80)  # border wall tiles
COL_TEXT      = (220, 230, 240)  # HUD text
COL_SCORE_VAL = (255, 220,  60)  # score value colour
COL_LEVEL_VAL = (100, 200, 255)  # level value colour

# Initial game speed (frames per second).
# Each new level adds SPEED_INC to this value.
BASE_FPS   = 7
SPEED_INC  = 2   # extra FPS granted per level

# How many food items the snake must eat to advance one level
FOOD_PER_LEVEL = 3

# Directions as (dx, dy) vectors on the grid
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# Mapping opposite directions — used to prevent 180° turns
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


# ──────────────────────────────────────────────
# Helper: draw a rounded rectangle (missing in old Pygame)
# ──────────────────────────────────────────────
def draw_cell(surface, color, col, row, shrink=2):
    """Draw a filled cell at grid position (col, row) with a small margin."""
    rect = pygame.Rect(
        col * CELL + shrink,
        row * CELL + shrink,
        CELL - shrink * 2,
        CELL - shrink * 2,
    )
    pygame.draw.rect(surface, color, rect, border_radius=4)


# ──────────────────────────────────────────────
# Food placement
# ──────────────────────────────────────────────
def random_food(snake_body: list[tuple]) -> tuple:
    """
    Return a grid cell (col, row) that is:
      • not on the 1-cell-wide border wall
      • not currently occupied by the snake
    """
    # Build the set of forbidden positions — border + snake body
    border = set()
    for c in range(COLS):
        border.add((c, 0))           # top wall
        border.add((c, ROWS - 1))    # bottom wall
    for r in range(ROWS):
        border.add((0, r))           # left wall
        border.add((COLS - 1, r))    # right wall

    forbidden = border | set(snake_body)

    # All safe interior cells
    safe = [
        (c, r)
        for c in range(1, COLS - 1)
        for r in range(1, ROWS - 1)
        if (c, r) not in forbidden
    ]

    # If no safe cell exists (edge case: full board), return centre
    return random.choice(safe) if safe else (COLS // 2, ROWS // 2)


# ──────────────────────────────────────────────
# HUD drawing
# ──────────────────────────────────────────────
def draw_hud(surface, font, score, level, food_count):
    """Render the score, level, and next-level progress in the top-left area."""
    # Panel background — slightly transparent rectangle
    panel = pygame.Surface((220, 70), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 120))
    surface.blit(panel, (8, 8))

    # Score
    score_lbl = font.render("SCORE", True, COL_TEXT)
    score_val = font.render(str(score), True, COL_SCORE_VAL)
    surface.blit(score_lbl, (16, 12))
    surface.blit(score_val, (90, 12))

    # Level
    level_lbl = font.render("LEVEL", True, COL_TEXT)
    level_val = font.render(str(level), True, COL_LEVEL_VAL)
    surface.blit(level_lbl, (16, 42))
    surface.blit(level_val, (90, 42))

    # Progress bar toward next level
    progress = food_count / FOOD_PER_LEVEL
    bar_x, bar_y, bar_w, bar_h = 130, 48, 90, 12
    pygame.draw.rect(surface, (50, 50, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    pygame.draw.rect(surface, COL_LEVEL_VAL,
                     (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=4)


# ──────────────────────────────────────────────
# Wall drawing
# ──────────────────────────────────────────────
def draw_walls(surface):
    """Draw the 1-cell border around the play area."""
    for c in range(COLS):
        draw_cell(surface, COL_WALL, c, 0,        shrink=1)
        draw_cell(surface, COL_WALL, c, ROWS - 1, shrink=1)
    for r in range(1, ROWS - 1):
        draw_cell(surface, COL_WALL, 0,        r, shrink=1)
        draw_cell(surface, COL_WALL, COLS - 1, r, shrink=1)


# ──────────────────────────────────────────────
# Grid drawing (subtle background lines)
# ──────────────────────────────────────────────
def draw_grid(surface):
    for x in range(0, WINDOW_W, CELL):
        pygame.draw.line(surface, COL_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(surface, COL_GRID, (0, y), (WINDOW_W, y))


# ──────────────────────────────────────────────
# Game Over screen
# ──────────────────────────────────────────────
def show_game_over(surface, font_big, font_small, score, level):
    """Block until the player presses R (retry) or Q / closes the window."""
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    cx = WINDOW_W // 2

    title  = font_big.render("GAME OVER", True, (230, 60, 60))
    sub    = font_small.render(f"Score: {score}   Level: {level}", True, COL_TEXT)
    hint   = font_small.render("Press  R  to retry  |  Q  to quit", True, (150, 150, 170))

    surface.blit(title, title.get_rect(center=(cx, WINDOW_H // 2 - 60)))
    surface.blit(sub,   sub.get_rect(center=(cx,   WINDOW_H // 2)))
    surface.blit(hint,  hint.get_rect(center=(cx,  WINDOW_H // 2 + 50)))
    pygame.display.flip()

    # Wait for input
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True    # restart
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()


# ──────────────────────────────────────────────
# Main game function
# ──────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("🐍  Snake — Practice 10")
    clock = pygame.time.Clock()

    # Fonts
    font_hud   = pygame.font.SysFont("consolas", 22, bold=True)
    font_big   = pygame.font.SysFont("consolas", 52, bold=True)
    font_small = pygame.font.SysFont("consolas", 26)

    # ── Game reset closure ───────────────────────
    def new_game():
        """Return the initial game state as a dictionary."""
        start_col = COLS // 2
        start_row = ROWS // 2
        # Snake stored as a list of (col, row) tuples; index 0 is the head
        body = [
            (start_col,     start_row),
            (start_col - 1, start_row),
            (start_col - 2, start_row),
        ]
        return {
            "body":       body,
            "direction":  RIGHT,          # current movement direction
            "next_dir":   RIGHT,          # buffered direction (applied next tick)
            "food":       random_food(body),
            "score":      0,
            "level":      1,
            "food_count": 0,              # food eaten this level
            "alive":      True,
        }

    state = new_game()

    # ── Main loop ────────────────────────────────
    while True:

        # ── 1. Events ─────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                # Map arrow keys (and WASD) → direction vectors.
                # Block 180° reversal: cannot go directly opposite to current direction.
                key_map = {
                    pygame.K_UP:    UP,
                    pygame.K_w:     UP,
                    pygame.K_DOWN:  DOWN,
                    pygame.K_s:     DOWN,
                    pygame.K_LEFT:  LEFT,
                    pygame.K_a:     LEFT,
                    pygame.K_RIGHT: RIGHT,
                    pygame.K_d:     RIGHT,
                }
                if event.key in key_map:
                    desired = key_map[event.key]
                    # Only accept the turn if it's not the opposite of current direction
                    if desired != OPPOSITE[state["direction"]]:
                        state["next_dir"] = desired

        # ── 2. Game logic (tick) ──────────────────
        if state["alive"]:
            # Apply the buffered direction
            state["direction"] = state["next_dir"]
            dx, dy = state["direction"]

            # Compute the new head position
            head_col, head_row = state["body"][0]
            new_head = (head_col + dx, head_row + dy)
            nc, nr   = new_head

            # ── Collision: border wall ─────────────
            # The wall occupies the outermost ring of cells (index 0 and max)
            if nc <= 0 or nc >= COLS - 1 or nr <= 0 or nr >= ROWS - 1:
                state["alive"] = False

            # ── Collision: self ────────────────────
            elif new_head in state["body"]:
                state["alive"] = False

            else:
                # No collision — advance the snake
                state["body"].insert(0, new_head)   # add new head

                # Check if snake ate the food
                if new_head == state["food"]:
                    state["score"]      += 1          # increment score
                    state["food_count"] += 1          # count toward level-up

                    # Level up when enough food has been collected
                    if state["food_count"] >= FOOD_PER_LEVEL:
                        state["level"]      += 1
                        state["food_count"]  = 0

                    # Spawn new food at a valid random position
                    state["food"] = random_food(state["body"])
                    # Do NOT remove tail → snake grows by 1 segment
                else:
                    # No food eaten → remove the tail to keep length constant
                    state["body"].pop()

        # ── 3. Draw ───────────────────────────────
        screen.fill(COL_BG)
        draw_grid(screen)
        draw_walls(screen)

        # Food — pulsing inner circle for visual flair
        fc, fr = state["food"]
        food_rect = pygame.Rect(fc * CELL + 3, fr * CELL + 3, CELL - 6, CELL - 6)
        pygame.draw.ellipse(screen, COL_FOOD, food_rect)

        # Snake body (draw tail-to-neck first, then head on top)
        for i, (c, r) in enumerate(reversed(state["body"])):
            color = COL_SNAKE_H if i == len(state["body"]) - 1 else COL_SNAKE_B
            draw_cell(screen, color, c, r)

        # HUD
        draw_hud(screen, font_hud, state["score"], state["level"], state["food_count"])

        pygame.display.flip()

        # ── 4. Game over check ────────────────────
        if not state["alive"]:
            if show_game_over(screen, font_big, font_small,
                              state["score"], state["level"]):
                state = new_game()   # restart

        # ── 5. Clock — speed depends on level ─────
        fps = BASE_FPS + (state["level"] - 1) * SPEED_INC
        clock.tick(fps)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    main()
