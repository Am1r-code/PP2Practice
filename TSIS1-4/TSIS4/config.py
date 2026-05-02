WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 600
TITLE         = "Snake TSIS 4"
CELL_SIZE     = 20
COLS          = WINDOW_WIDTH  // CELL_SIZE   # 40
ROWS          = WINDOW_HEIGHT // CELL_SIZE   # 30
INITIAL_SPEED       = 8          # frames per second
SPEED_INCREMENT     = 1          # extra FPS per level
FOOD_PER_LEVEL      = 5          # normal food eaten to advance a level
OBSTACLE_START_LVL  = 3          # obstacles appear from this level
OBSTACLES_PER_LEVEL = 3          # extra obstacle blocks added per level beyond 2
FOOD_DISAPPEAR_MS   = 7_000      # timed food vanishes after this
POWERUP_FIELD_MS    = 8_000      # power-up stays on field this long
POWERUP_EFFECT_MS   = 5_000      # active effect duration
FOOD_WEIGHTS = {
    "normal":  1,
    "bonus":   3,
    "poison": -2,   # not used for scoring — triggers shortening
}
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
GREEN       = ( 60, 200,  80)
DARK_GREEN  = ( 30, 120,  50)
RED         = (220,  50,  50)
DARK_RED    = (120,  20,  20)   # poison food
YELLOW      = (240, 220,  60)
ORANGE      = (240, 140,  30)
BLUE        = ( 60, 120, 220)
CYAN        = ( 50, 200, 220)
PURPLE      = (160,  60, 220)
GRAY        = (100, 100, 100)
LIGHT_GRAY  = (180, 180, 180)
DARK_GRAY   = ( 40,  40,  40)
BG_COLOR    = ( 15,  15,  25)
GRID_COLOR  = ( 25,  25,  40)
PANEL_COLOR = ( 20,  20,  35)

POWERUP_COLORS = {
    "speed_boost": ORANGE,
    "slow_motion": CYAN,
    "shield":      PURPLE,
}

DB_DSN = "dbname=snake_db user=postgres password=postgres host=localhost port=5432"
