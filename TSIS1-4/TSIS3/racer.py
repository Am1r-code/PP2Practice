import pygame
import random
import math
import sys

W, H        = 700, 750
ROAD_LEFT   = 130
ROAD_RIGHT  = 570
ROAD_W      = ROAD_RIGHT - ROAD_LEFT
N_LANES     = 4
LANE_W      = ROAD_W // N_LANES
LANE_CENTERS = [ROAD_LEFT + LANE_W * i + LANE_W // 2 for i in range(N_LANES)]
FINISH_DIST = 5000          # metres to finish

C_BG        = (18,  20,  30)
C_ROAD      = (38,  40,  55)
C_KERB_W    = (230, 230, 230)
C_KERB_R    = (200,  40,  40)
C_LINE      = (200, 180,  50)
C_GRASS     = (30,  80,  30)
C_DASH      = (200, 200, 200)
C_HUD_BG    = (0,   0,   0,  160)

CAR_COLORS = {
    "red":    (220,  60,  50),
    "blue":   ( 60, 130, 255),
    "green":  ( 60, 200,  90),
    "yellow": (255, 200,  40),
    "white":  (230, 235, 245),
}

DIFF_PARAMS = {
    "easy":   {"base_speed": 4,  "spawn_rate": 0.008, "obstacle_rate": 0.004},
    "normal": {"base_speed": 6,  "spawn_rate": 0.014, "obstacle_rate": 0.008},
    "hard":   {"base_speed": 9,  "spawn_rate": 0.022, "obstacle_rate": 0.014},
}

PU_NITRO  = "nitro"
PU_SHIELD = "shield"
PU_REPAIR = "repair"
PU_COLORS = {PU_NITRO: (255, 180, 0), PU_SHIELD: (0, 180, 255), PU_REPAIR: (60, 220, 80)}
PU_LABELS = {PU_NITRO: "⚡NITRO", PU_SHIELD: "🛡SHIELD", PU_REPAIR: "🔧REPAIR"}
PU_LIFETIME = 6000    # ms before disappearing if uncollected

COIN_WEIGHTS = [(1, 50), (2, 30), (5, 15), (10, 5)]    # (value, weight)


def _weighted_coin_value():
    vals, wts = zip(*COIN_WEIGHTS)
    return random.choices(vals, weights=wts)[0]


def _lane(n):
    return LANE_CENTERS[n % N_LANES]


def _draw_car(surface, x, y, color, w=36, h=52, shadow=False):
    """Draw a simple car shape."""
    if shadow:
        s = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 60), s.get_rect())
        surface.blit(s, (x - w//2 - 3, y - h//2 + 8))

    body = pygame.Rect(x - w//2, y - h//2, w, h)
    pygame.draw.rect(surface, color, body, border_radius=7)

    # Windshields
    ws_f = pygame.Rect(x - w//2 + 5, y - h//2 + 8,  w - 10, 12)
    ws_r = pygame.Rect(x - w//2 + 5, y + h//2 - 20, w - 10, 10)
    pygame.draw.rect(surface, (160, 210, 255), ws_f, border_radius=3)
    pygame.draw.rect(surface, (120, 160, 200), ws_r, border_radius=2)

    # Wheels
    wc = (20, 20, 20)
    for wx, wy in [(x - w//2 - 4, y - 18), (x + w//2 - 4, y - 18),
                   (x - w//2 - 4, y + 8),  (x + w//2 - 4, y + 8)]:
        pygame.draw.rect(surface, wc, pygame.Rect(wx, wy, 8, 12), border_radius=2)


def _draw_obstacle(surface, kind, x, y):
    if kind == "oil":
        pygame.draw.ellipse(surface, (20, 20, 60), pygame.Rect(x-22, y-10, 44, 20))
        pygame.draw.ellipse(surface, (40, 40, 120, 180), pygame.Rect(x-20, y-8, 40, 16))
        # rainbow sheen
        for i, c in enumerate([(255,0,0,60),(0,255,0,60),(0,0,255,60)]):
            pygame.draw.arc(surface, c[:3], pygame.Rect(x-18+i*2, y-6, 32-i*4, 12), 0, math.pi, 2)
    elif kind == "barrier":
        pygame.draw.rect(surface, (255, 80, 20), pygame.Rect(x-24, y-10, 48, 20), border_radius=4)
        pygame.draw.rect(surface, (255, 200, 0), pygame.Rect(x-24, y-10, 48, 20), 2, border_radius=4)
        for bx in range(x-20, x+20, 10):
            pygame.draw.line(surface, (255, 200, 0), (bx, y-10), (bx+6, y+10), 2)
    elif kind == "pothole":
        pygame.draw.ellipse(surface, (10, 10, 10), pygame.Rect(x-18, y-10, 36, 20))
        pygame.draw.ellipse(surface, (30, 30, 30), pygame.Rect(x-14, y-7,  28, 14))
    elif kind == "bump":
        pygame.draw.ellipse(surface, (100, 90, 70), pygame.Rect(x-26, y-8, 52, 16))
        pygame.draw.ellipse(surface, (130, 120, 90), pygame.Rect(x-22, y-5, 44, 10))
    elif kind == "nitro_strip":
        # Orange glowing strip across the lane
        s = pygame.Surface((LANE_W - 4, 18), pygame.SRCALPHA)
        s.fill((255, 150, 0, 120))
        surface.blit(s, (x - LANE_W//2 + 2, y - 9))
        pygame.draw.rect(surface, (255, 200, 80),
                         pygame.Rect(x - LANE_W//2 + 2, y - 9, LANE_W - 4, 18), 2, border_radius=3)
        font = pygame.font.SysFont("dejavusans", 11, bold=True)
        lbl = font.render("NITRO", True, (255, 255, 100))
        surface.blit(lbl, lbl.get_rect(center=(x, y)))


def _draw_powerup(surface, kind, x, y, age_frac):
    """age_frac 0→1 as the power-up ages; pulse when almost gone."""
    r = 18
    pulse = 1 + 0.15 * math.sin(pygame.time.get_ticks() / 180)
    if age_frac > 0.7:
        pulse = 1 + 0.3 * math.sin(pygame.time.get_ticks() / 80)
    r = int(r * pulse)
    col = PU_COLORS[kind]
    pygame.draw.circle(surface, col,                  (x, y), r)
    pygame.draw.circle(surface, (255, 255, 255, 180), (x, y), r, 2)
    font = pygame.font.SysFont("dejavusans", 9, bold=True)
    lbl  = font.render(kind.upper(), True, (0, 0, 0))
    surface.blit(lbl, lbl.get_rect(center=(x, y)))


def _draw_coin(surface, x, y, value):
    colors = {1: (230,200,30), 2: (200,220,50), 5: (80,200,255), 10: (255,80,200)}
    col = colors.get(value, (230, 200, 30))
    pygame.draw.circle(surface, col, (x, y), 11)
    pygame.draw.circle(surface, (255, 255, 255), (x, y), 11, 2)
    font = pygame.font.SysFont("dejavusans", 11, bold=True)
    lbl  = font.render(str(value), True, (0, 0, 0))
    surface.blit(lbl, lbl.get_rect(center=(x, y)))


def run_game(screen: pygame.Surface, settings: dict) -> dict:
    """
    Run one race. Returns stats dict:
      {name, score, distance, coins}
    """
    clock     = pygame.time.Clock()
    FPS       = 60
    diff      = settings.get("difficulty", "normal")
    params    = DIFF_PARAMS.get(diff, DIFF_PARAMS["normal"])
    car_color = CAR_COLORS.get(settings.get("car_color", "red"), CAR_COLORS["red"])
    name      = settings.get("player_name", "Player")

    fonts = {
        "sm":  pygame.font.SysFont("dejavusans", 15),
        "med": pygame.font.SysFont("dejavusans", 18, bold=True),
        "lg":  pygame.font.SysFont("dejavusans", 24, bold=True),
        "xl":  pygame.font.SysFont("dejavusans", 32, bold=True),
    }

    player_lane  = 1          # 0–3
    player_x     = _lane(player_lane)
    player_y     = H - 120
    player_speed = params["base_speed"]
    base_speed   = params["base_speed"]

    coins_collected = 0
    score           = 0
    distance        = 0       # pixels → metres at 0.1 scale
    road_scroll     = 0

    active_pu       = None    # PU_NITRO | PU_SHIELD | PU_REPAIR | None
    pu_timer        = 0       # ms remaining for timed power-ups
    shielded        = False
    crashed_once    = False   # Repair tracks "one crash forgiven"

    # Each entry: {"x","y","kind",...}
    traffic      = []
    obstacles    = []     # kind: oil | barrier | pothole | bump | nitro_strip
    coins        = []     # {"x","y","value"}
    powerups     = []     # {"x","y","kind","spawned_at"}
    road_dashes  = [{"y": y} for y in range(0, H, 60)]

    # Moving barrier event state
    mov_barrier  = None   # {"x","y","dx"}
    mov_timer    = 0

    # Hazard lane set (changes every ~5 seconds)
    hazard_lanes    = set()
    hazard_timer    = 0
    HAZARD_INTERVAL = 5000

    def _reset_hazard_lanes():
        n = random.randint(1, 2)
        return set(random.sample(range(N_LANES), n))

    hazard_lanes = _reset_hazard_lanes()

    target_x   = player_x
    LANE_SPEED = 12

    def current_spawn_rate():
        level = coins_collected // 10
        factor = 1 + level * 0.15
        return min(params["spawn_rate"] * factor, 0.06)

    def current_obstacle_rate():
        level = coins_collected // 10
        factor = 1 + level * 0.12
        return min(params["obstacle_rate"] * factor, 0.04)

    def traffic_speed():
        level = coins_collected // 10
        return base_speed + level * 0.5 + (3 if active_pu == PU_NITRO else 0)

    def draw_road():
        # Grass shoulders
        pygame.draw.rect(screen, (30, 80, 30), pygame.Rect(0, 0, ROAD_LEFT, H))
        pygame.draw.rect(screen, (30, 80, 30), pygame.Rect(ROAD_RIGHT, 0, W - ROAD_RIGHT, H))

        # Road surface
        pygame.draw.rect(screen, C_ROAD, pygame.Rect(ROAD_LEFT, 0, ROAD_W, H))

        # Kerb stripes
        stripe_h = 30
        for ky in range(0, H + stripe_h, stripe_h * 2):
            sy = (ky - road_scroll % (stripe_h * 2))
            for side_x, col in [(ROAD_LEFT - 10, C_KERB_R), (ROAD_RIGHT, C_KERB_R)]:
                pygame.draw.rect(screen, col, pygame.Rect(side_x, sy, 10, stripe_h))
                pygame.draw.rect(screen, C_KERB_W, pygame.Rect(side_x, sy + stripe_h, 10, stripe_h))

        # Lane dashes
        for d in road_dashes:
            pygame.draw.rect(screen, C_DASH,
                             pygame.Rect(ROAD_LEFT + LANE_W - 2, d["y"], 4, 28), border_radius=2)
            pygame.draw.rect(screen, C_DASH,
                             pygame.Rect(ROAD_LEFT + LANE_W * 2 - 2, d["y"], 4, 28), border_radius=2)
            pygame.draw.rect(screen, C_DASH,
                             pygame.Rect(ROAD_LEFT + LANE_W * 3 - 2, d["y"], 4, 28), border_radius=2)

        # Hazard lane tint
        for hl in hazard_lanes:
            s = pygame.Surface((LANE_W, H), pygame.SRCALPHA)
            s.fill((255, 60, 60, 18))
            screen.blit(s, (ROAD_LEFT + hl * LANE_W, 0))

    def draw_hud():
        # Left panel
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(0, 0, ROAD_LEFT, H))

        def hud_line(label, val, y, col=(200, 200, 210)):
            lbl = fonts["sm"].render(label, True, (120, 125, 145))
            screen.blit(lbl, (6, y))
            v = fonts["med"].render(str(val), True, col)
            screen.blit(v, (6, y + 16))

        hud_line("SCORE",  f"{score:,}",         20,  (255, 200, 40))
        hud_line("COINS",  coins_collected,       70,  (60, 220, 80))
        hud_line("DIST",   f"{distance}m",        120, (60, 180, 255))
        finish_left = max(0, FINISH_DIST - distance)
        hud_line("LEFT",   f"{finish_left}m",     170, (200, 200, 210))
        hud_line("SPEED",  f"{'x'+str(round(player_speed/base_speed,1))}", 220)

        # Progress bar
        frac = min(distance / FINISH_DIST, 1.0)
        bar_rect = pygame.Rect(6, 270, ROAD_LEFT - 12, 10)
        pygame.draw.rect(screen, (50, 55, 70), bar_rect, border_radius=4)
        pygame.draw.rect(screen, (60, 200, 80),
                         pygame.Rect(6, 270, int((ROAD_LEFT - 12) * frac), 10), border_radius=4)
        pygame.draw.rect(screen, (80, 85, 100), bar_rect, 1, border_radius=4)

        # Power-up status
        if active_pu:
            col = PU_COLORS[active_pu]
            lbl = fonts["med"].render(PU_LABELS[active_pu], True, col)
            screen.blit(lbl, (4, 300))
            if active_pu == PU_NITRO and pu_timer > 0:
                secs = pu_timer / 1000
                t = fonts["sm"].render(f"{secs:.1f}s", True, col)
                screen.blit(t, (4, 322))
        elif shielded:
            lbl = fonts["med"].render("🛡SHIELD", True, PU_COLORS[PU_SHIELD])
            screen.blit(lbl, (4, 300))

        # Right panel (difficulty + name)
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(ROAD_RIGHT, 0, W - ROAD_RIGHT, H))
        nm = fonts["sm"].render(name[:10], True, (150, 155, 170))
        screen.blit(nm, (ROAD_RIGHT + 4, 20))
        dif = fonts["sm"].render(diff.upper(), True, (200, 150, 60))
        screen.blit(dif, (ROAD_RIGHT + 4, 40))

    def player_rect():
        return pygame.Rect(player_x - 18, player_y - 26, 36, 52)

    def collides(px, py, ex, ey, pr=22, er=20):
        return abs(px - ex) < (pr + er) and abs(py - ey) < (pr + er)


    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a) and player_lane > 0:
                    player_lane -= 1
                    target_x = _lane(player_lane)
                if event.key in (pygame.K_RIGHT, pygame.K_d) and player_lane < N_LANES - 1:
                    player_lane += 1
                    target_x = _lane(player_lane)
                if event.key == pygame.K_ESCAPE:
                    return {"name": name, "score": score,
                            "distance": distance, "coins": coins_collected}

        if player_x < target_x:
            player_x = min(player_x + LANE_SPEED, target_x)
        elif player_x > target_x:
            player_x = max(player_x - LANE_SPEED, target_x)

        spd = player_speed
        road_scroll += spd
        distance = int(road_scroll * 0.05)

        for d in road_dashes:
            d["y"] = (d["y"] + spd) % H

        if active_pu == PU_NITRO:
            pu_timer -= dt
            player_speed = base_speed * 1.8
            if pu_timer <= 0:
                active_pu    = None
                player_speed = base_speed
        else:
            player_speed = base_speed

        hazard_timer += dt
        if hazard_timer >= HAZARD_INTERVAL:
            hazard_lanes  = _reset_hazard_lanes()
            hazard_timer  = 0

        sr = current_spawn_rate()
        or_ = current_obstacle_rate()

        # Traffic car
        if random.random() < sr:
            lane = random.randint(0, N_LANES - 1)
            cx   = _lane(lane)
            # Safe spawn: don't appear on player
            if not (lane == player_lane and abs(-60 - player_y) < 80):
                tc = (200, random.randint(40, 60), random.randint(40, 200))
                traffic.append({"x": cx, "y": -60, "color": tc, "lane": lane})

        # Obstacle
        if random.random() < or_:
            lane = random.randint(0, N_LANES - 1)
            if lane != player_lane:
                kind = random.choices(
                    ["oil", "barrier", "pothole", "bump", "nitro_strip"],
                    weights=[25, 20, 25, 20, 10])[0]
                obstacles.append({"x": _lane(lane), "y": -30, "kind": kind, "lane": lane})

        # Coin
        if random.random() < sr * 1.2:
            lane = random.randint(0, N_LANES - 1)
            val  = _weighted_coin_value()
            coins.append({"x": _lane(lane), "y": -20, "value": val})

        # Power-up (low chance, only one at a time on screen)
        if len(powerups) == 0 and random.random() < 0.003:
            lane = random.randint(0, N_LANES - 1)
            kind = random.choice([PU_NITRO, PU_SHIELD, PU_REPAIR])
            powerups.append({
                "x": _lane(lane), "y": -20, "kind": kind,
                "spawned_at": pygame.time.get_ticks()
            })

        # Moving barrier event (occasional)
        mov_timer += dt
        if mov_timer > 8000 and mov_barrier is None:
            mov_timer  = 0
            bx = random.choice(LANE_CENTERS)
            mov_barrier = {"x": bx, "y": -30, "dx": random.choice([-2, 2])}

        ts = traffic_speed()

        # Traffic
        for t in traffic:
            t["y"] += ts
        traffic = [t for t in traffic if t["y"] < H + 80]

        # Obstacles
        for o in obstacles:
            o["y"] += spd * 0.7
        obstacles = [o for o in obstacles if o["y"] < H + 40]

        # Coins
        for c in coins:
            c["y"] += spd * 0.7
        coins = [c for c in coins if c["y"] < H + 30]

        # Power-ups
        now = pygame.time.get_ticks()
        for p in powerups:
            p["y"] += spd * 0.7
        powerups = [p for p in powerups
                    if p["y"] < H + 30 and now - p["spawned_at"] < PU_LIFETIME]

        # Moving barrier
        if mov_barrier:
            mov_barrier["y"] += spd * 0.6
            mov_barrier["x"] += mov_barrier["dx"]
            if mov_barrier["x"] < ROAD_LEFT + 20 or mov_barrier["x"] > ROAD_RIGHT - 20:
                mov_barrier["dx"] *= -1
            if mov_barrier["y"] > H + 40:
                mov_barrier = None

        # Coins
        collected = []
        for c in coins:
            if collides(player_x, player_y, c["x"], c["y"], 20, 14):
                coins_collected += 1
                score += c["value"] * 10
                collected.append(c)
        coins = [c for c in coins if c not in collected]

        # Power-ups
        collected_pu = []
        for p in powerups:
            if collides(player_x, player_y, p["x"], p["y"], 20, 18):
                collected_pu.append(p)
                kind = p["kind"]
                if kind == PU_NITRO:
                    active_pu  = PU_NITRO
                    pu_timer   = 4000
                    score     += 50
                elif kind == PU_SHIELD:
                    shielded   = True
                    active_pu  = PU_SHIELD
                    score     += 30
                elif kind == PU_REPAIR:
                    crashed_once = False    # clear crash debt
                    active_pu    = PU_REPAIR
                    score       += 20
                    # Repair briefly shows then clears
                    pygame.time.delay(200)
                    active_pu = None
        powerups = [p for p in powerups if p not in collected_pu]

        # Traffic collision
        game_over = False
        for t in traffic:
            if collides(player_x, player_y, t["x"], t["y"], 18, 22):
                if shielded:
                    shielded  = False
                    active_pu = None
                    traffic.remove(t)
                    break
                else:
                    game_over = True
                    break

        # Obstacle collision
        if not game_over:
            for o in obstacles:
                if collides(player_x, player_y, o["x"], o["y"], 18, 20):
                    kind = o["kind"]
                    if kind == "nitro_strip":
                        active_pu  = PU_NITRO
                        pu_timer   = 2500
                    elif kind == "oil":
                        if shielded:
                            shielded = False; active_pu = None
                        else:
                            player_speed = base_speed * 0.5
                            pygame.time.delay(150)
                            player_speed = base_speed
                    elif kind in ("barrier", "pothole"):
                        if shielded:
                            shielded = False; active_pu = None
                        elif not crashed_once:
                            crashed_once = True   # first hit: slow down
                            score = max(0, score - 30)
                        else:
                            game_over = True
                    obstacles.remove(o)
                    break

        # Moving barrier collision
        if mov_barrier and not game_over:
            if collides(player_x, player_y, mov_barrier["x"], mov_barrier["y"], 18, 24):
                if shielded:
                    shielded = False; active_pu = None
                    mov_barrier = None
                else:
                    game_over = True

        score = coins_collected * 10 + distance // 5

        if distance >= FINISH_DIST:
            score += 2000     # finish bonus
            return {"name": name, "score": score,
                    "distance": distance, "coins": coins_collected}

        if game_over:
            return {"name": name, "score": score,
                    "distance": distance, "coins": coins_collected}

        screen.fill(C_BG)
        draw_road()

        for o in obstacles:
            _draw_obstacle(screen, o["kind"], o["x"], o["y"])
        for c in coins:
            _draw_coin(screen, c["x"], c["y"], c["value"])
        for p in powerups:
            age_frac = (now - p["spawned_at"]) / PU_LIFETIME
            _draw_powerup(screen, p["kind"], p["x"], p["y"], age_frac)
        for t in traffic:
            _draw_car(screen, t["x"], t["y"], t["color"], shadow=True)
        if mov_barrier:
            _draw_obstacle(screen, "barrier", mov_barrier["x"], mov_barrier["y"])

        # Shield glow around player
        if shielded:
            pygame.draw.circle(screen, (*PU_COLORS[PU_SHIELD], 80),
                               (int(player_x), int(player_y)), 32, 4)
        _draw_car(screen, int(player_x), player_y, car_color, shadow=True)

        draw_hud()
        pygame.display.flip()

    return {"name": name, "score": score, "distance": distance, "coins": coins_collected}
