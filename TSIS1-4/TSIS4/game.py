import random
import pygame
from config import (
    CELL_SIZE, COLS, ROWS,
    INITIAL_SPEED, SPEED_INCREMENT, FOOD_PER_LEVEL,
    OBSTACLE_START_LVL, OBSTACLES_PER_LEVEL,
    FOOD_DISAPPEAR_MS, POWERUP_FIELD_MS, POWERUP_EFFECT_MS,
    GREEN, DARK_RED, YELLOW, ORANGE,
    POWERUP_COLORS,
)

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

class Food:
    """A single food item placed on the grid."""

    KIND_NORMAL = "normal"
    KIND_BONUS  = "bonus"
    KIND_POISON = "poison"

    COLORS = {
        KIND_NORMAL: (240, 80,  80),
        KIND_BONUS:  YELLOW,
        KIND_POISON: DARK_RED,
    }
    POINTS = {
        KIND_NORMAL: 1,
        KIND_BONUS:  3,
        KIND_POISON: 0,   # handled separately
    }

    def __init__(self, pos: tuple, kind: str, timed: bool = False):
        self.pos      = pos
        self.kind     = kind
        self.timed    = timed
        self.spawned  = pygame.time.get_ticks()

    @property
    def color(self):
        return self.COLORS[self.kind]

    @property
    def points(self):
        return self.POINTS[self.kind]

    def is_expired(self) -> bool:
        if not self.timed:
            return False
        return pygame.time.get_ticks() - self.spawned > FOOD_DISAPPEAR_MS

    def draw(self, surface):
        x, y = self.pos
        rect = pygame.Rect(x * CELL_SIZE + 2, y * CELL_SIZE + 2,
                           CELL_SIZE - 4, CELL_SIZE - 4)
        pygame.draw.rect(surface, self.color, rect, border_radius=4)
        # blinking when about to expire
        if self.timed:
            elapsed = pygame.time.get_ticks() - self.spawned
            if elapsed > FOOD_DISAPPEAR_MS * 0.7:
                if (elapsed // 200) % 2 == 0:
                    pygame.draw.rect(surface, (255, 255, 255), rect, 2,
                                     border_radius=4)


class PowerUp:
    KIND_SPEED  = "speed_boost"
    KIND_SLOW   = "slow_motion"
    KIND_SHIELD = "shield"

    LABELS = {
        KIND_SPEED:  "⚡",
        KIND_SLOW:   "❄",
        KIND_SHIELD: "🛡",
    }

    def __init__(self, pos: tuple, kind: str):
        self.pos     = pos
        self.kind    = kind
        self.spawned = pygame.time.get_ticks()

    @property
    def color(self):
        return POWERUP_COLORS[self.kind]

    def is_field_expired(self) -> bool:
        return pygame.time.get_ticks() - self.spawned > POWERUP_FIELD_MS

    def draw(self, surface, font_small):
        x, y = self.pos
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE,
                           CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, self.color, rect, border_radius=5)
        # pulsing border
        t = pygame.time.get_ticks()
        alpha = abs((t % 1000) - 500) / 500   # 0→1→0
        border_col = tuple(min(255, int(c + 60 * alpha)) for c in self.color)
        pygame.draw.rect(surface, border_col, rect, 2, border_radius=5)

class Snake:
    def __init__(self, color):
        mid_x, mid_y = COLS // 2, ROWS // 2
        self.body      = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.direction = RIGHT
        self.color     = color
        self.grow_by   = 0

    def set_direction(self, new_dir):
        if new_dir != OPPOSITE.get(self.direction):
            self.direction = new_dir

    def move(self) -> tuple:
        """Advance the snake. Returns new head position."""
        hx, hy = self.body[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)
        self.body.insert(0, new_head)
        if self.grow_by > 0:
            self.grow_by -= 1
        else:
            self.body.pop()
        return new_head

    def shorten(self, amount: int):
        """Remove `amount` tail segments."""
        for _ in range(amount):
            if len(self.body) > 1:
                self.body.pop()

    def head(self):
        return self.body[0]

    def occupies(self, pos) -> bool:
        return pos in self.body

    def self_collision(self) -> bool:
        return self.body[0] in self.body[1:]

    def draw(self, surface):
        for i, (x, y) in enumerate(self.body):
            shade = max(30, self.color[1] - i * 3)
            c = (self.color[0], shade, self.color[2])
            rect = pygame.Rect(x * CELL_SIZE + 1, y * CELL_SIZE + 1,
                               CELL_SIZE - 2, CELL_SIZE - 2)
            pygame.draw.rect(surface, c, rect, border_radius=3)
        # eyes on head
        hx, hy = self.body[0]
        pygame.draw.circle(surface, (255, 255, 255),
                           (hx * CELL_SIZE + 5, hy * CELL_SIZE + 6), 3)
        pygame.draw.circle(surface, (255, 255, 255),
                           (hx * CELL_SIZE + 14, hy * CELL_SIZE + 6), 3)
        pygame.draw.circle(surface, (0, 0, 0),
                           (hx * CELL_SIZE + 6, hy * CELL_SIZE + 6), 1)
        pygame.draw.circle(surface, (0, 0, 0),
                           (hx * CELL_SIZE + 15, hy * CELL_SIZE + 6), 1)


class GameState:
    def __init__(self, settings: dict):
        self.settings      = settings
        snake_color        = tuple(settings.get("snake_color", (60, 200, 80)))
        self.snake         = Snake(snake_color)
        self.score         = 0
        self.level         = 1
        self.food_eaten    = 0        # normal/bonus food toward next level
        self.foods: list[Food]       = []
        self.powerup: PowerUp | None = None
        self.obstacles: set          = set()

        # active effect state
        self.active_effect: str | None = None
        self.effect_start:  int        = 0
        self.shield_active: bool       = False

        self.over          = False

        self._spawn_food()

    def _occupied(self) -> set:
        """All cells taken by snake, obstacles, food, powerup."""
        taken = set(self.snake.body) | self.obstacles
        for f in self.foods:
            taken.add(f.pos)
        if self.powerup:
            taken.add(self.powerup.pos)
        return taken

    def _random_free_cell(self) -> tuple | None:
        taken  = self._occupied()
        free   = [(c, r) for c in range(1, COLS - 1)
                          for r in range(1, ROWS - 1)
                          if (c, r) not in taken]
        return random.choice(free) if free else None

    def _spawn_food(self):
        """Keep 2–3 food items on the field."""
        while len(self.foods) < 2:
            pos = self._random_free_cell()
            if pos is None:
                break
            roll = random.random()
            if roll < 0.10:
                kind  = Food.KIND_POISON
                timed = False
            elif roll < 0.25:
                kind  = Food.KIND_BONUS
                timed = True
            else:
                kind  = Food.KIND_NORMAL
                timed = (random.random() < 0.4)
            self.foods.append(Food(pos, kind, timed))

    def _maybe_spawn_powerup(self):
        if self.powerup is not None:
            return
        if random.random() < 0.015:          # ~1.5% each tick
            pos = self._random_free_cell()
            if pos is None:
                return
            kind = random.choice([
                PowerUp.KIND_SPEED,
                PowerUp.KIND_SLOW,
                PowerUp.KIND_SHIELD,
            ])
            self.powerup = PowerUp(pos, kind)

    def _place_obstacles(self):
        if self.level < OBSTACLE_START_LVL:
            return
        count  = OBSTACLES_PER_LEVEL * (self.level - OBSTACLE_START_LVL + 1)
        head   = self.snake.head()
        safety = {(head[0] + dx, head[1] + dy)
                  for dx in range(-4, 5) for dy in range(-4, 5)}
        attempts = 0
        while len(self.obstacles) < count and attempts < 500:
            attempts += 1
            pos = (random.randint(2, COLS - 3), random.randint(2, ROWS - 3))
            if pos in safety or self.snake.occupies(pos):
                continue
            self.obstacles.add(pos)

    def _level_up(self):
        self.level     += 1
        self.food_eaten = 0
        # keep existing obstacles and add more
        self._place_obstacles()

    def _apply_powerup(self, kind: str):
        self.active_effect = kind
        self.effect_start  = pygame.time.get_ticks()
        if kind == PowerUp.KIND_SHIELD:
            self.shield_active = True

    def _check_effect_expiry(self):
        if self.active_effect in (PowerUp.KIND_SPEED, PowerUp.KIND_SLOW):
            if pygame.time.get_ticks() - self.effect_start > POWERUP_EFFECT_MS:
                self.active_effect = None

    def current_fps(self) -> int:
        base = INITIAL_SPEED + (self.level - 1) * SPEED_INCREMENT
        if self.active_effect == PowerUp.KIND_SPEED:
            return base + 4
        if self.active_effect == PowerUp.KIND_SLOW:
            return max(2, base - 4)
        return base

    def update(self):
        if self.over:
            return

        self._check_effect_expiry()
        self._maybe_spawn_powerup()

        # expire timed food / field powerup
        self.foods = [f for f in self.foods if not f.is_expired()]
        if self.powerup and self.powerup.is_field_expired():
            self.powerup = None

        # move snake
        new_head = self.snake.move()
        hx, hy   = new_head

        # border collision
        if not (0 <= hx < COLS and 0 <= hy < ROWS):
            if self.shield_active:
                self.shield_active = False
                self.active_effect = None
                # wrap to opposite side (shield absorbs one wall hit)
                hx = hx % COLS
                hy = hy % ROWS
                self.snake.body[0] = (hx, hy)
            else:
                self.over = True
                return

        # obstacle collision
        if new_head in self.obstacles:
            if self.shield_active:
                self.shield_active = False
                self.active_effect = None
                self.snake.body.pop(0)   # stay in place
                self.snake.body.insert(0, self.snake.body[0])
            else:
                self.over = True
                return

        # self collision
        if self.snake.self_collision():
            if self.shield_active:
                self.shield_active = False
                self.active_effect = None
            else:
                self.over = True
                return

        # food collision
        for food in self.foods[:]:
            if food.pos == new_head:
                self.foods.remove(food)
                if food.kind == Food.KIND_POISON:
                    self.snake.shorten(2)
                    if len(self.snake.body) <= 1:
                        self.over = True
                        return
                else:
                    self.score     += food.points
                    self.food_eaten += 1
                    self.snake.grow_by += 1
                    if self.food_eaten >= FOOD_PER_LEVEL:
                        self._level_up()

        # powerup collision
        if self.powerup and self.powerup.pos == new_head:
            self._apply_powerup(self.powerup.kind)
            self.powerup = None

        self._spawn_food()

    def draw(self, surface, font_small):
        # obstacles
        for (ox, oy) in self.obstacles:
            rect = pygame.Rect(ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, (80, 80, 90), rect)
            pygame.draw.rect(surface, (50, 50, 60), rect, 1)

        # food
        for food in self.foods:
            food.draw(surface)

        # powerup
        if self.powerup:
            self.powerup.draw(surface, font_small)

        # snake
        self.snake.draw(surface)
