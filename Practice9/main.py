"""
main.py - Moving Ball Game
A red ball that moves around the screen using arrow keys.

Controls
--------
  Arrow keys   – Move the ball (Up / Down / Left / Right)
  Q / Escape   – Quit
"""

import pygame
import sys

from ball import Ball

# ── Constants ────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 600
FPS           = 60

BG_COLOR      = (255, 255, 255)   # white background
GRID_COLOR    = (235, 235, 235)   # subtle grid lines
TEXT_COLOR    = (80,  80,  80)

GRID_STEP     = 40                # pixels between grid lines


def draw_grid(surface):
    """Draw a light reference grid on the background."""
    for x in range(0, WINDOW_WIDTH,  GRID_STEP):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, GRID_STEP):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))


def draw_hud(surface, font, ball: Ball):
    """Show the ball's current position in the corner."""
    text = font.render(f"x: {ball.x}   y: {ball.y}", True, TEXT_COLOR)
    surface.blit(text, (10, 10))

    hint = font.render("Arrow keys to move  |  Q to quit", True, (160, 160, 160))
    surface.blit(hint, (10, WINDOW_HEIGHT - 28))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Moving Ball")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 16)
    ball = Ball(WINDOW_WIDTH, WINDOW_HEIGHT)

    running = True
    while running:
        # ── Event handling ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Quit
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

                # Movement – each key press moves the ball by exactly 20 px
                # The Ball class ignores moves that would go off-screen.
                elif event.key == pygame.K_UP:
                    ball.move_up()
                elif event.key == pygame.K_DOWN:
                    ball.move_down()
                elif event.key == pygame.K_LEFT:
                    ball.move_left()
                elif event.key == pygame.K_RIGHT:
                    ball.move_right()

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        draw_grid(screen)
        ball.draw(screen)
        draw_hud(screen, font, ball)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
