"""
racer.py — Practice 10: Car Racing Game
=========================================
Based on the CodersLegacy Pygame tutorial series (Parts 1-3).
Extra features added:
  • Randomly appearing coins on the road
  • Coin counter displayed in the top-right corner
  • Fully commented code
"""

import pygame
import random
import sys

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
WINDOW_W = 500    # window width  in pixels
WINDOW_H = 600    # window height in pixels
FPS      = 60     # target frame rate

# Road geometry (the drivable strip in the centre)
ROAD_LEFT  = 80   # x-coordinate where road starts (left kerb)
ROAD_RIGHT = 420  # x-coordinate where road ends   (right kerb)
ROAD_W     = ROAD_RIGHT - ROAD_LEFT  # road width = 340 px

# Lane positions (centre-x of each of the 3 lanes)
LANE_CENTERS = [
    ROAD_LEFT + ROAD_W // 6,           # left lane
    ROAD_LEFT + ROAD_W // 2,           # centre lane
    ROAD_LEFT + 5 * ROAD_W // 6,       # right lane
]

# Colour palette
COL_SKY    = (30,  35,  55)    # dark sky / background
COL_GRASS  = (30,  90,  40)    # grass verges
COL_ROAD   = (55,  58,  70)    # asphalt
COL_LANE   = (220, 220, 100)   # dashed lane markings
COL_KERB   = (200, 200, 200)   # kerb / white lines
COL_COIN   = (255, 215,  20)   # gold coin
COL_TEXT   = (240, 240, 240)   # HUD white text
COL_COIN_H = (255, 245, 100)   # coin highlight

# Player car dimensions
CAR_W = 48
CAR_H = 80

# Obstacle (enemy) car dimensions
OBS_W = 48
OBS_H = 80

# Coin dimensions
COIN_R = 14   # radius of the coin circle

# Initial scrolling speed of road markings / obstacles (px per frame)
INITIAL_SPEED = 4

# How often the speed increases (frames between each tick-up)
SPEED_INCREASE_EVERY = 300   # roughly every 5 seconds at 60 FPS

# Probability that a coin spawns alongside a new obstacle (0.0–1.0)
COIN_SPAWN_CHANCE = 0.55


# ──────────────────────────────────────────────
# Draw a simple car using pygame primitives
# ──────────────────────────────────────────────
def draw_car(surface, cx, cy, w, h, body_col, window_col=(140, 200, 240)):
    """
    Draw a top-down car centred at (cx, cy).
    body_col   : main car body colour
    window_col : windscreen / window tint
    """
    x = cx - w // 2
    y = cy - h // 2

    # Car body
    pygame.draw.rect(surface, body_col, (x, y, w, h), border_radius=8)

    # Windscreen (top portion)
    ws_margin = 6
    pygame.draw.rect(surface, window_col,
                     (x + ws_margin, y + 8, w - ws_margin * 2, h // 3),
                     border_radius=4)

    # Rear window
    pygame.draw.rect(surface, window_col,
                     (x + ws_margin, y + h - 8 - h // 4, w - ws_margin * 2, h // 4),
                     border_radius=4)

    # Left wheels
    wheel_col = (30, 30, 30)
    pygame.draw.rect(surface, wheel_col, (x - 6, y + 8,      12, 20), border_radius=3)
    pygame.draw.rect(surface, wheel_col, (x - 6, y + h - 28, 12, 20), border_radius=3)
    # Right wheels
    pygame.draw.rect(surface, wheel_col, (x + w - 6, y + 8,      12, 20), border_radius=3)
    pygame.draw.rect(surface, wheel_col, (x + w - 6, y + h - 28, 12, 20), border_radius=3)


# ──────────────────────────────────────────────
# Draw a coin at position (cx, cy)
# ──────────────────────────────────────────────
def draw_coin(surface, cx, cy, radius=COIN_R):
    """Draw a shiny gold coin (circle with highlight)."""
    pygame.draw.circle(surface, COL_COIN, (cx, cy), radius)
    # Shine highlight — small white arc in the top-left quadrant
    pygame.draw.circle(surface, COL_COIN_H, (cx - radius // 4, cy - radius // 4),
                       radius // 3)
    # Outer ring
    pygame.draw.circle(surface, (200, 160, 0), (cx, cy), radius, 2)


# ──────────────────────────────────────────────
# Road dashes (scrolling lane markers)
# ──────────────────────────────────────────────
class RoadDash:
    """A single dashed lane-marking segment that scrolls downward."""

    DASH_H = 40      # height of each dash in pixels
    GAP_H  = 30      # gap between dashes

    def __init__(self, lane_x, start_y):
        """
        lane_x  : x-coordinate of this lane marker column
        start_y : initial y position (can be negative to stagger spawning)
        """
        self.x = lane_x
        self.y = start_y
        self.w = 6    # dash width

    def update(self, speed):
        """Move the dash downward at the current road speed."""
        self.y += speed

    def draw(self, surface):
        pygame.draw.rect(surface, COL_LANE,
                         (self.x - self.w // 2, self.y, self.w, self.DASH_H),
                         border_radius=2)

    def off_screen(self):
        """True when the dash has scrolled past the bottom of the window."""
        return self.y > WINDOW_H


# ──────────────────────────────────────────────
# Obstacle (enemy car)
# ──────────────────────────────────────────────
class Obstacle:
    """An oncoming enemy car that scrolls from top to bottom."""

    # Varied enemy car colours for visual variety
    COLOURS = [
        (200, 60,  60),    # red
        (60,  60, 200),    # blue
        (200, 160, 40),    # yellow
        (60, 180,  90),    # green
        (180, 60, 180),    # purple
    ]

    def __init__(self):
        # Pick a random lane
        self.lane_x = random.choice(LANE_CENTERS)
        # Start just above the top of the screen
        self.y      = -OBS_H
        self.color  = random.choice(self.COLOURS)
        self.w      = OBS_W
        self.h      = OBS_H

    def update(self, speed):
        """Scroll the obstacle downward."""
        self.y += speed

    def draw(self, surface):
        draw_car(surface, self.lane_x, self.y + self.h // 2,
                 self.w, self.h, self.color, window_col=(80, 110, 160))

    def off_screen(self):
        return self.y > WINDOW_H

    def get_rect(self):
        """Collision rectangle (slightly inset for fairness)."""
        return pygame.Rect(
            self.lane_x - self.w // 2 + 4,
            self.y + 4,
            self.w - 8,
            self.h - 8,
        )


# ──────────────────────────────────────────────
# Coin
# ──────────────────────────────────────────────
class Coin:
    """A collectible coin that scrolls down the road."""

    def __init__(self, lane_x, start_y):
        self.x = lane_x         # centre x (lane centre)
        self.y = start_y        # centre y
        self.collected = False  # set True when player drives over it

    def update(self, speed):
        """Scroll downward at road speed."""
        self.y += speed

    def draw(self, surface):
        if not self.collected:
            draw_coin(surface, self.x, self.y)

    def off_screen(self):
        return self.y > WINDOW_H + COIN_R

    def get_rect(self):
        """Circular collision approximated as a square rect."""
        return pygame.Rect(self.x - COIN_R, self.y - COIN_R,
                           COIN_R * 2, COIN_R * 2)


# ──────────────────────────────────────────────
# HUD — coin counter (top-right)
# ──────────────────────────────────────────────
def draw_hud(surface, font, coins, score):
    """Render coin count (top-right) and score (top-left)."""
    # ── Top-right: coin counter ────────────────
    coin_text = font.render(f"🪙 {coins}", True, COL_COIN)
    # Fallback if emoji not supported
    coin_surf = pygame.font.SysFont("consolas", 26, bold=True).render(
        f"COINS: {coins}", True, COL_COIN)
    surface.blit(coin_surf, (WINDOW_W - coin_surf.get_width() - 16, 12))

    # ── Top-left: score ────────────────────────
    score_surf = font.render(f"SCORE: {score}", True, COL_TEXT)
    surface.blit(score_surf, (16, 12))


# ──────────────────────────────────────────────
# Game Over screen
# ──────────────────────────────────────────────
def show_game_over(surface, font_big, font_small, score, coins):
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))

    cx = WINDOW_W // 2

    t1 = font_big.render("GAME OVER",          True, (230, 60, 60))
    t2 = font_small.render(f"Score: {score}",  True, COL_TEXT)
    t3 = font_small.render(f"Coins: {coins}",  True, COL_COIN)
    t4 = font_small.render("R = Retry   Q = Quit", True, (160, 160, 180))

    surface.blit(t1, t1.get_rect(center=(cx, WINDOW_H // 2 - 80)))
    surface.blit(t2, t2.get_rect(center=(cx, WINDOW_H // 2 - 10)))
    surface.blit(t3, t3.get_rect(center=(cx, WINDOW_H // 2 + 35)))
    surface.blit(t4, t4.get_rect(center=(cx, WINDOW_H // 2 + 90)))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()


# ──────────────────────────────────────────────
# Draw the road background
# ──────────────────────────────────────────────
def draw_road(surface):
    # Grass verges
    surface.fill(COL_GRASS)
    # Asphalt strip
    pygame.draw.rect(surface, COL_ROAD, (ROAD_LEFT, 0, ROAD_W, WINDOW_H))
    # Kerb lines (white borders)
    pygame.draw.line(surface, COL_KERB, (ROAD_LEFT,  0), (ROAD_LEFT,  WINDOW_H), 4)
    pygame.draw.line(surface, COL_KERB, (ROAD_RIGHT, 0), (ROAD_RIGHT, WINDOW_H), 4)


# ──────────────────────────────────────────────
# Initial road dashes helper
# ──────────────────────────────────────────────
def create_initial_dashes() -> list:
    """
    Pre-populate the screen with dashes at staggered positions
    so the road looks busy from frame 1.
    """
    dashes = []
    step   = RoadDash.DASH_H + RoadDash.GAP_H
    # Two lane-marker columns between the three lanes
    lane_xs = [
        ROAD_LEFT + ROAD_W // 3,
        ROAD_LEFT + 2 * ROAD_W // 3,
    ]
    for lx in lane_xs:
        y = -RoadDash.DASH_H
        while y < WINDOW_H + step:
            dashes.append(RoadDash(lx, y))
            y += step
    return dashes


# ──────────────────────────────────────────────
# Main game function
# ──────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("🏎  Racer — Practice 10")
    clock = pygame.time.Clock()

    font_hud   = pygame.font.SysFont("consolas", 22, bold=True)
    font_big   = pygame.font.SysFont("consolas", 52, bold=True)
    font_small = pygame.font.SysFont("consolas", 26)

    # ── Game-state reset closure ─────────────────
    def new_game():
        return {
            # Player car starts at bottom-centre of the road
            "player_x": WINDOW_W // 2,
            "player_y": WINDOW_H - 100,
            "speed":    INITIAL_SPEED,    # road scroll speed
            "score":    0,                # distance-based score
            "coins":    0,                # collected coins
            "frame":    0,                # frame counter (used for timing)
            "obstacles": [],              # list of Obstacle objects
            "coins_list": [],             # list of Coin objects
            "dashes":    create_initial_dashes(),
            "alive":    True,
        }

    state = new_game()

    # ── Main loop ────────────────────────────────
    while True:

        # ── 1. Events ─────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        if state["alive"]:
            # ── 2. Player movement ─────────────────
            keys = pygame.key.get_pressed()
            px   = state["player_x"]
            py   = state["player_y"]

            move_speed = 5   # horizontal/vertical movement speed

            # Horizontal movement — keep player inside road kerbs
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
                px = max(ROAD_LEFT  + CAR_W // 2, px - move_speed)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                px = min(ROAD_RIGHT - CAR_W // 2, px + move_speed)

            # Vertical movement — keep player visible on screen
            if keys[pygame.K_UP]   or keys[pygame.K_w]:
                py = max(CAR_H // 2, py - move_speed)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                py = min(WINDOW_H - CAR_H // 2, py + move_speed)

            state["player_x"] = px
            state["player_y"] = py

            # ── 3. Scroll dashes ───────────────────
            spd = state["speed"]
            step = RoadDash.DASH_H + RoadDash.GAP_H

            # Two marker columns (between lanes)
            lane_xs = [ROAD_LEFT + ROAD_W // 3, ROAD_LEFT + 2 * ROAD_W // 3]
            for dash in state["dashes"]:
                dash.update(spd)

            # Remove off-screen dashes; spawn new ones at the top
            new_dashes = [d for d in state["dashes"] if not d.off_screen()]
            for lx in lane_xs:
                # Check if there's a dash near the top for this column
                col_dashes = [d for d in new_dashes if d.x == lx]
                if not col_dashes or min(d.y for d in col_dashes) > 0:
                    new_dashes.append(RoadDash(lx, -RoadDash.DASH_H))
            state["dashes"] = new_dashes

            # ── 4. Spawn obstacles ─────────────────
            # New obstacle every 90 frames (~1.5 s), adjusted for difficulty
            spawn_interval = max(40, 90 - state["frame"] // 200)
            if state["frame"] % spawn_interval == 0:
                obs = Obstacle()
                state["obstacles"].append(obs)

                # Randomly spawn a coin in a different lane alongside the obstacle
                if random.random() < COIN_SPAWN_CHANCE:
                    # Pick a lane that is NOT the obstacle's lane
                    other_lanes = [lc for lc in LANE_CENTERS if lc != obs.lane_x]
                    coin_x = random.choice(other_lanes)
                    # Vertically offset so coin is near the obstacle but not on top
                    coin_y = obs.y - random.randint(20, 80)
                    state["coins_list"].append(Coin(coin_x, coin_y))

            # Also occasionally spawn a solo coin (no obstacle)
            if state["frame"] % 75 == 0 and random.random() < 0.35:
                cx2 = random.choice(LANE_CENTERS)
                state["coins_list"].append(Coin(cx2, -COIN_R))

            # ── 5. Update obstacles & check collisions
            player_rect = pygame.Rect(
                px - CAR_W // 2 + 4,
                py - CAR_H // 2 + 4,
                CAR_W - 8,
                CAR_H - 8,
            )
            for obs in state["obstacles"]:
                obs.update(spd)
                if obs.get_rect().colliderect(player_rect):
                    state["alive"] = False
            state["obstacles"] = [o for o in state["obstacles"] if not o.off_screen()]

            # ── 6. Update coins & check collection ──
            for coin in state["coins_list"]:
                coin.update(spd)
                # Collect coin if player drives over it
                if not coin.collected and coin.get_rect().colliderect(player_rect):
                    coin.collected = True
                    state["coins"] += 1       # increment coin counter
            # Remove coins that are off-screen or already collected
            state["coins_list"] = [
                c for c in state["coins_list"]
                if not c.off_screen() and not c.collected
            ]

            # ── 7. Score & difficulty ──────────────
            state["frame"] += 1
            state["score"]  = state["frame"] // 10   # 1 point per 10 frames

            # Gradually increase road speed every SPEED_INCREASE_EVERY frames
            if state["frame"] % SPEED_INCREASE_EVERY == 0:
                state["speed"] += 1

        # ── 8. Draw ───────────────────────────────
        draw_road(screen)

        # Road dashes
        for dash in state["dashes"]:
            dash.draw(screen)

        # Coins (drawn before cars so cars appear on top)
        for coin in state["coins_list"]:
            coin.draw(screen)

        # Obstacles
        for obs in state["obstacles"]:
            obs.draw(screen)

        # Player car (bright cyan body)
        draw_car(screen, state["player_x"], state["player_y"],
                 CAR_W, CAR_H, body_col=(80, 220, 220))

        # HUD — score (top-left) and coin count (top-right)
        draw_hud(screen, font_hud, state["coins"], state["score"])

        pygame.display.flip()
        clock.tick(FPS)

        # ── 9. Game Over ──────────────────────────
        if not state["alive"]:
            if show_game_over(screen, font_big, font_small,
                              state["score"], state["coins"]):
                state = new_game()


# ──────────────────────────────────────────────
if __name__ == "__main__":
    main()
