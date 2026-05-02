"""
racer.py — Practice 11: Car Racing Game (Extended)
====================================================
Built on top of Practice 10. New features:

  NEW ► Weighted coins
          Three coin variants with different values and rarities:
            • Bronze  (gold)    — 1 pt,  weight 60 % — most common
            • Silver  (silver)  — 3 pts, weight 30 % — uncommon
            • Gold    (cyan)    — 5 pts, weight 10 % — rare

  NEW ► Enemy speed-up on coin milestones
          Every ENEMY_SPEEDUP_COINS coins collected, enemy cars move
          ENEMY_SPEED_INC px/frame faster. A short on-screen flash
          announces each speed-up to the player.

  Carried from Practice 10:
    • Scrolling 3-lane road with dashed lane markers
    • Random enemy car spawning with collision detection
    • Score (distance) + coin counter HUD
    • Road scroll speed increases over time
    • Game Over / retry loop
"""

import pygame
import random
import sys

# ──────────────────────────────────────────────
# Window constants
# ──────────────────────────────────────────────
WINDOW_W = 500
WINDOW_H = 600
FPS      = 60

# Road geometry
ROAD_LEFT  = 80
ROAD_RIGHT = 420
ROAD_W     = ROAD_RIGHT - ROAD_LEFT   # 340 px

# Lane centre x-coordinates
LANE_CENTERS = [
    ROAD_LEFT + ROAD_W // 6,           # left lane
    ROAD_LEFT + ROAD_W // 2,           # centre lane
    ROAD_LEFT + 5 * ROAD_W // 6,       # right lane
]

# ──────────────────────────────────────────────
# Colour palette
# ──────────────────────────────────────────────
COL_GRASS = (30,  90,  40)
COL_ROAD  = (55,  58,  70)
COL_LANE  = (220, 220, 100)
COL_KERB  = (200, 200, 200)
COL_TEXT  = (240, 240, 240)

# ──────────────────────────────────────────────
# Car / coin dimensions
# ──────────────────────────────────────────────
CAR_W  = 48
CAR_H  = 80
OBS_W  = 48
OBS_H  = 80

# ──────────────────────────────────────────────
# Road scroll speed
# ──────────────────────────────────────────────
INITIAL_ROAD_SPEED    = 4    # px per frame at game start
ROAD_SPEED_INC_EVERY  = 300  # frames between road speed ticks

# ──────────────────────────────────────────────
# Enemy speed
# ──────────────────────────────────────────────
# Enemy cars scroll at road speed + their own bonus speed.
# The bonus increases by ENEMY_SPEED_INC every ENEMY_SPEEDUP_COINS coins.
INITIAL_ENEMY_BONUS   = 0    # enemy starts at road speed (no bonus)
ENEMY_SPEED_INC       = 1    # px/frame added each milestone
ENEMY_SPEEDUP_COINS   = 5    # milestone every N total coins collected

# ──────────────────────────────────────────────
# Weighted coin type definitions
# ──────────────────────────────────────────────
# weight  – relative spawn probability
# value   – score added when collected
# color   – fill colour of the coin disc
# label   – tiny text on the coin
# radius  – visual radius in pixels (bigger = more valuable, easier to see)

COIN_TYPES = [
    {
        "name":   "bronze",
        "weight": 60,
        "value":  1,
        "color":  (205, 127,  50),   # bronze / copper
        "hi":     (230, 170,  90),   # highlight colour
        "label":  "+1",
        "radius": 11,
    },
    {
        "name":   "silver",
        "weight": 30,
        "value":  3,
        "color":  (180, 185, 195),   # silver
        "hi":     (220, 225, 235),
        "label":  "+3",
        "radius": 13,
    },
    {
        "name":   "gold",
        "weight": 10,
        "value":  5,
        "color":  (255, 210,  20),   # bright gold
        "hi":     (255, 245, 130),
        "label":  "+5",
        "radius": 15,
    },
]

_COIN_WEIGHTS = [ct["weight"] for ct in COIN_TYPES]

# Spawn probability that a coin appears alongside a new obstacle
COIN_SPAWN_CHANCE = 0.55
# Additional solo coin spawn probability per 75 frames
SOLO_COIN_CHANCE  = 0.40


# ══════════════════════════════════════════════
# Drawing helpers
# ══════════════════════════════════════════════
def draw_car(surface, cx, cy, w, h, body_col, window_col=(140, 200, 240)):
    """
    Render a top-down car centred at (cx, cy).
    body_col   : main paint colour
    window_col : windscreen and rear-window tint
    """
    x = cx - w // 2
    y = cy - h // 2

    pygame.draw.rect(surface, body_col, (x, y, w, h), border_radius=8)   # body

    m = 6   # window margin
    pygame.draw.rect(surface, window_col,
                     (x + m, y + 8, w - m * 2, h // 3), border_radius=4)  # front window
    pygame.draw.rect(surface, window_col,
                     (x + m, y + h - 8 - h // 4, w - m * 2, h // 4),
                     border_radius=4)                                       # rear window

    wc = (30, 30, 30)   # wheel colour
    pygame.draw.rect(surface, wc, (x - 6, y + 8,      12, 20), border_radius=3)
    pygame.draw.rect(surface, wc, (x - 6, y + h - 28, 12, 20), border_radius=3)
    pygame.draw.rect(surface, wc, (x + w - 6, y + 8,      12, 20), border_radius=3)
    pygame.draw.rect(surface, wc, (x + w - 6, y + h - 28, 12, 20), border_radius=3)


def draw_road(surface):
    """Draw grass verges + asphalt strip + kerb lines."""
    surface.fill(COL_GRASS)
    pygame.draw.rect(surface, COL_ROAD, (ROAD_LEFT, 0, ROAD_W, WINDOW_H))
    pygame.draw.line(surface, COL_KERB, (ROAD_LEFT,  0), (ROAD_LEFT,  WINDOW_H), 4)
    pygame.draw.line(surface, COL_KERB, (ROAD_RIGHT, 0), (ROAD_RIGHT, WINDOW_H), 4)


# ══════════════════════════════════════════════
# Road dash (scrolling lane marking)
# ══════════════════════════════════════════════
class RoadDash:
    """One dashed segment in a lane-marker column."""
    DASH_H = 40
    GAP_H  = 30

    def __init__(self, lane_x, start_y):
        self.x = lane_x
        self.y = start_y
        self.w = 6

    def update(self, speed):
        self.y += speed

    def draw(self, surface):
        pygame.draw.rect(surface, COL_LANE,
                         (self.x - self.w // 2, self.y, self.w, self.DASH_H),
                         border_radius=2)

    def off_screen(self):
        return self.y > WINDOW_H


def create_initial_dashes():
    """Pre-populate dashes so the road looks busy immediately."""
    dashes = []
    step   = RoadDash.DASH_H + RoadDash.GAP_H
    xs     = [ROAD_LEFT + ROAD_W // 3, ROAD_LEFT + 2 * ROAD_W // 3]
    for lx in xs:
        y = -RoadDash.DASH_H
        while y < WINDOW_H + step:
            dashes.append(RoadDash(lx, y))
            y += step
    return dashes


# ══════════════════════════════════════════════
# Obstacle (enemy car)
# ══════════════════════════════════════════════
class Obstacle:
    """Enemy car that scrolls from top to bottom at (road speed + enemy bonus)."""

    COLOURS = [
        (200, 60,  60),   # red
        (60,  60, 200),   # blue
        (200, 160, 40),   # yellow
        (60, 180,  90),   # green
        (180, 60, 180),   # purple
    ]

    def __init__(self):
        self.lane_x = random.choice(LANE_CENTERS)
        self.y      = -OBS_H                        # start above screen
        self.color  = random.choice(self.COLOURS)

    def update(self, road_speed: int, enemy_bonus: int):
        """
        Move the car downward.
        Total speed = road_speed (ambient scroll) + enemy_bonus (extra speed).
        """
        self.y += road_speed + enemy_bonus

    def draw(self, surface):
        draw_car(surface, self.lane_x, self.y + OBS_H // 2,
                 OBS_W, OBS_H, self.color, window_col=(80, 110, 160))

    def off_screen(self):
        return self.y > WINDOW_H

    def get_rect(self):
        """Slightly inset collision rectangle."""
        return pygame.Rect(
            self.lane_x - OBS_W // 2 + 4,
            self.y + 4,
            OBS_W - 8,
            OBS_H - 8,
        )


# ══════════════════════════════════════════════
# Weighted coin
# ══════════════════════════════════════════════
class Coin:
    """
    A coin item with a randomly chosen type (bronze / silver / gold).
    Visual size and point value differ per type.
    """

    def __init__(self, lane_x: int, start_y: int):
        self.x         = lane_x
        self.y         = start_y
        self.collected = False

        # Pick coin type using weighted random selection
        self.ctype = random.choices(COIN_TYPES, weights=_COIN_WEIGHTS, k=1)[0]
        self.value  = self.ctype["value"]
        self.radius = self.ctype["radius"]

    def update(self, speed: int):
        """Scroll downward at road speed."""
        self.y += speed

    def draw(self, surface: pygame.Surface, font_tiny: pygame.font.Font):
        """Draw the coin disc with highlight and value label."""
        if self.collected:
            return

        cx, cy = self.x, self.y
        r      = self.radius
        col    = self.ctype["color"]
        hi     = self.ctype["hi"]

        # Outer disc
        pygame.draw.circle(surface, col, (cx, cy), r)
        # Shine highlight (top-left quadrant)
        pygame.draw.circle(surface, hi, (cx - r // 4, cy - r // 4), r // 3)
        # Outer ring
        pygame.draw.circle(surface, tuple(max(0, c - 60) for c in col),
                           (cx, cy), r, 2)

        # Point label
        lbl = font_tiny.render(self.ctype["label"], True, (30, 20, 10))
        surface.blit(lbl, (cx - lbl.get_width() // 2,
                           cy - lbl.get_height() // 2))

    def off_screen(self):
        return self.y > WINDOW_H + self.radius

    def get_rect(self):
        """Approximate collision as a square bounding rect of the disc."""
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


# ══════════════════════════════════════════════
# HUD
# ══════════════════════════════════════════════
def draw_hud(surface, font, font_tiny,
             coins: int, coin_value: int, score: int,
             enemy_bonus: int, next_milestone: int,
             speedup_msg_timer: int):
    """
    Render:
      • Score (top-left)
      • Coin counter + value (top-right)
      • Enemy speed indicator (below coins)
      • Speed-up flash message when a milestone is just hit
      • Coin legend (bottom-right)
    """
    # ── Score ─────────────────────────────────
    sc_surf = font.render(f"SCORE: {score}", True, COL_TEXT)
    surface.blit(sc_surf, (12, 12))

    # ── Coin counter (top-right) ────────────────
    cx_panel = WINDOW_W - 175
    panel    = pygame.Surface((165, 72), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 140))
    surface.blit(panel, (cx_panel, 8))

    surface.blit(font.render(f"COINS: {coins}", True, (240, 210, 60)),
                 (cx_panel + 8, 12))
    surface.blit(font.render(f"VALUE: {coin_value}", True, (180, 230, 180)),
                 (cx_panel + 8, 40))

    # ── Enemy speed indicator ──────────────────
    spd_lbl = font_tiny.render(
        f"ENEMY SPD +{enemy_bonus}  next:{next_milestone}", True, (220, 120, 120))
    surface.blit(spd_lbl, (cx_panel, 84))

    # ── Speed-up flash message ─────────────────
    if speedup_msg_timer > 0:
        alpha = min(255, speedup_msg_timer * 4)
        flash = font.render("ENEMIES FASTER!", True, (255, 80, 80))
        flash.set_alpha(alpha)
        surface.blit(flash, flash.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 - 80)))

    # ── Coin legend (bottom-right) ─────────────
    lx = WINDOW_W - 90
    ly = WINDOW_H - 14 - len(COIN_TYPES) * 20
    for i, ct in enumerate(COIN_TYPES):
        y = ly + i * 20
        pygame.draw.circle(surface, ct["color"], (lx, y + 8), 7)
        desc = font_tiny.render(f"{ct['label']} {ct['name']}", True, COL_TEXT)
        surface.blit(desc, (lx + 12, y))


# ══════════════════════════════════════════════
# Game Over screen
# ══════════════════════════════════════════════
def show_game_over(surface, font_big, font_sm, score, coins, coin_value):
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))
    cx = WINDOW_W // 2

    t1 = font_big.render("GAME OVER",               True, (230, 60, 60))
    t2 = font_sm.render(f"Score:      {score}",     True, COL_TEXT)
    t3 = font_sm.render(f"Coins:      {coins}",     True, (240, 210, 60))
    t4 = font_sm.render(f"Coin value: {coin_value}",True, (180, 230, 180))
    t5 = font_sm.render("R = Retry   Q = Quit",     True, (160, 160, 180))

    for surf, dy in ((t1, -90), (t2, -20), (t3, 20), (t4, 55), (t5, 105)):
        surface.blit(surf, surf.get_rect(center=(cx, WINDOW_H // 2 + dy)))

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
    pygame.display.set_caption("Racer — Practice 11")
    clock = pygame.time.Clock()

    font_hud  = pygame.font.SysFont("consolas", 20, bold=True)
    font_tiny = pygame.font.SysFont("consolas", 13, bold=True)
    font_big  = pygame.font.SysFont("consolas", 48, bold=True)
    font_sm   = pygame.font.SysFont("consolas", 24)

    # ── Build fresh game state ─────────────────
    def new_game() -> dict:
        return {
            "player_x":     WINDOW_W // 2,
            "player_y":     WINDOW_H - 100,
            "road_speed":   INITIAL_ROAD_SPEED,
            "enemy_bonus":  INITIAL_ENEMY_BONUS,   # extra speed added to enemy cars
            "score":        0,
            "coins":        0,       # total coins collected
            "coin_value":   0,       # total point-value of collected coins
            "frame":        0,
            "obstacles":    [],
            "coins_list":   [],
            "dashes":       create_initial_dashes(),
            "speedup_msg":  0,       # countdown timer for the flash message (frames)
            "alive":        True,
        }

    state = new_game()

    # ── Main loop ─────────────────────────────
    while True:

        # 1. Events
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        if state["alive"]:

            # 2. Player movement
            keys = pygame.key.get_pressed()
            px, py = state["player_x"], state["player_y"]
            ms = 5   # movement speed (px per frame)

            if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
                px = max(ROAD_LEFT  + CAR_W // 2, px - ms)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                px = min(ROAD_RIGHT - CAR_W // 2, px + ms)
            if keys[pygame.K_UP]   or keys[pygame.K_w]:
                py = max(CAR_H // 2, py - ms)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                py = min(WINDOW_H - CAR_H // 2, py + ms)

            state["player_x"] = px
            state["player_y"] = py

            # 3. Scroll road dashes
            spd     = state["road_speed"]
            lane_xs = [ROAD_LEFT + ROAD_W // 3, ROAD_LEFT + 2 * ROAD_W // 3]

            for d in state["dashes"]:
                d.update(spd)

            new_dashes = [d for d in state["dashes"] if not d.off_screen()]
            for lx in lane_xs:
                col_d = [d for d in new_dashes if d.x == lx]
                if not col_d or min(d.y for d in col_d) > 0:
                    new_dashes.append(RoadDash(lx, -RoadDash.DASH_H))
            state["dashes"] = new_dashes

            # 4. Spawn obstacles (and sometimes coins alongside them)
            spawn_interval = max(40, 90 - state["frame"] // 200)
            if state["frame"] % spawn_interval == 0:
                obs = Obstacle()
                state["obstacles"].append(obs)

                # Coin alongside the obstacle (in a different lane)
                if random.random() < COIN_SPAWN_CHANCE:
                    other = [lc for lc in LANE_CENTERS if lc != obs.lane_x]
                    cx2   = random.choice(other)
                    cy2   = obs.y - random.randint(20, 80)
                    state["coins_list"].append(Coin(cx2, cy2))

            # Solo coin spawn (no obstacle required)
            if state["frame"] % 75 == 0 and random.random() < SOLO_COIN_CHANCE:
                state["coins_list"].append(
                    Coin(random.choice(LANE_CENTERS), -15))

            # 5. Update obstacles + collision check
            player_rect = pygame.Rect(
                px - CAR_W // 2 + 4, py - CAR_H // 2 + 4,
                CAR_W - 8, CAR_H - 8,
            )
            for obs in state["obstacles"]:
                # Each obstacle moves at road speed PLUS the current enemy bonus
                obs.update(spd, state["enemy_bonus"])
                if obs.get_rect().colliderect(player_rect):
                    state["alive"] = False

            state["obstacles"] = [
                o for o in state["obstacles"] if not o.off_screen()
            ]

            # 6. Update coins + collection check
            coins_before = state["coins"]

            for coin in state["coins_list"]:
                coin.update(spd)
                if not coin.collected and coin.get_rect().colliderect(player_rect):
                    coin.collected    = True
                    state["coins"]    += 1               # count collected
                    state["coin_value"] += coin.value    # add weighted value

            state["coins_list"] = [
                c for c in state["coins_list"]
                if not c.off_screen() and not c.collected
            ]

            # ── Enemy speed-up milestone check ─────────────────────────────
            # Every ENEMY_SPEEDUP_COINS coins, enemy cars get faster.
            # We compare total coins before vs after this frame's collection.
            new_coins    = state["coins"]
            milestone_before = coins_before // ENEMY_SPEEDUP_COINS
            milestone_after  = new_coins    // ENEMY_SPEEDUP_COINS

            if milestone_after > milestone_before and new_coins > 0:
                # A new milestone was crossed this frame → speed up enemies
                state["enemy_bonus"] += ENEMY_SPEED_INC
                state["speedup_msg"]  = 120   # show flash message for 120 frames (2 s)

            # Countdown the speed-up message timer
            if state["speedup_msg"] > 0:
                state["speedup_msg"] -= 1

            # 7. Score + road speed
            state["frame"] += 1
            state["score"]  = state["frame"] // 10

            if state["frame"] % ROAD_SPEED_INC_EVERY == 0:
                state["road_speed"] += 1

        # 8. Draw
        draw_road(screen)

        for d in state["dashes"]:
            d.draw(screen)

        # Coins (drawn under cars so cars appear on top)
        for coin in state["coins_list"]:
            coin.draw(screen, font_tiny)

        for obs in state["obstacles"]:
            obs.draw(screen)

        # Player car — bright cyan
        draw_car(screen, state["player_x"], state["player_y"],
                 CAR_W, CAR_H, body_col=(80, 220, 220))

        # Next milestone = next multiple of ENEMY_SPEEDUP_COINS
        coins        = state["coins"]
        next_ms_coin = (coins // ENEMY_SPEEDUP_COINS + 1) * ENEMY_SPEEDUP_COINS

        draw_hud(screen, font_hud, font_tiny,
                 coins, state["coin_value"], state["score"],
                 state["enemy_bonus"], next_ms_coin,
                 state["speedup_msg"])

        pygame.display.flip()
        clock.tick(FPS)

        # 9. Game Over
        if not state["alive"]:
            if show_game_over(screen, font_big, font_sm,
                              state["score"], state["coins"],
                              state["coin_value"]):
                state = new_game()


if __name__ == "__main__":
    main()
