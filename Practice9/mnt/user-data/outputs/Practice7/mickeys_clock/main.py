"""
main.py - Mickey Mouse Clock Application
Displays current minutes and seconds using Mickey Mouse hand images as clock hands.

Controls:
  Q / Escape  – quit
"""

import pygame
import sys
import os
import math
import datetime

from clock import seconds_angle, minutes_angle, rotate_image_around_base

# ── Constants ────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 600
FPS           = 60
CENTER        = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

BG_COLOR      = (255, 255, 255)   # white background
FACE_COLOR    = (240, 240, 240)   # clock face
FACE_RADIUS   = 220
CLOCK_BORDER  = (30, 30, 30)

HAND_LENGTH   = 160               # pixels from center to fingertip

# Offset so hand image (pointing UP) aligns correctly.
# Adjust if your mickey_hand.png points a different direction.
HAND_UP_ANGLE = 90               # degrees to pre-rotate so hand points UP


def load_hand_image(path, scale=(30, 160)):
    """Load and scale the Mickey hand image. Returns a pygame.Surface."""
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, scale)
        # Pre-rotate so the image points straight UP
        img = pygame.transform.rotate(img, HAND_UP_ANGLE)
        return img
    else:
        # Fallback: draw a simple rounded rectangle as a hand
        surf = pygame.Surface(scale, pygame.SRCALPHA)
        pygame.draw.rect(surf, (30, 30, 30), surf.get_rect(), border_radius=8)
        surf = pygame.transform.rotate(surf, HAND_UP_ANGLE)
        return surf


def draw_clock_face(surface):
    """Draw the static clock face with tick marks."""
    # Face circle
    pygame.draw.circle(surface, FACE_COLOR, CENTER, FACE_RADIUS)
    pygame.draw.circle(surface, CLOCK_BORDER, CENTER, FACE_RADIUS, 4)

    # 60 tick marks
    for i in range(60):
        angle_rad = math.radians(i * 6 - 90)          # 6° per second
        is_minute = (i % 5 == 0)
        inner_r = FACE_RADIUS - (20 if is_minute else 10)
        outer_r = FACE_RADIUS - 4

        x1 = CENTER[0] + math.cos(angle_rad) * inner_r
        y1 = CENTER[1] + math.sin(angle_rad) * inner_r
        x2 = CENTER[0] + math.cos(angle_rad) * outer_r
        y2 = CENTER[1] + math.sin(angle_rad) * outer_r

        width = 3 if is_minute else 1
        pygame.draw.line(surface, CLOCK_BORDER, (x1, y1), (x2, y2), width)

    # Center dot
    pygame.draw.circle(surface, CLOCK_BORDER, CENTER, 8)


def draw_time_label(surface, font, minutes, seconds):
    """Render a digital time readout at the bottom of the clock face."""
    text = font.render(f"{minutes:02d}:{seconds:02d}", True, (50, 50, 50))
    rect = text.get_rect(center=(CENTER[0], CENTER[1] + FACE_RADIUS - 45))
    surface.blit(text, rect)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Mickey's Clock")
    clock = pygame.time.Clock()

    # Paths
    base_dir   = os.path.dirname(__file__)
    hand_path  = os.path.join(base_dir, "images", "mickey_hand.png")

    # Load hand image (used for both hands, scaled differently)
    minute_hand_img = load_hand_image(hand_path, scale=(28, HAND_LENGTH))
    second_hand_img = load_hand_image(hand_path, scale=(20, HAND_LENGTH))

    # Font for digital readout
    font = pygame.font.SysFont("monospace", 32, bold=True)
    title_font = pygame.font.SysFont("arial", 22)

    # Pre-draw static clock face onto a separate surface (efficiency)
    face_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    draw_clock_face(face_surface)

    running = True
    while running:
        # ── Event handling ──────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        # ── Get time ────────────────────────────────────────────────────────
        now = datetime.datetime.now()
        mins = now.minute
        secs = now.second

        # ── Draw ────────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        screen.blit(face_surface, (0, 0))

        # Minutes hand (right hand) – red
        min_angle = minutes_angle(mins)
        rotate_image_around_base(screen, minute_hand_img, min_angle, CENTER, HAND_LENGTH // 2)

        # Seconds hand (left hand) – blue tint via colorkey trick
        sec_angle = seconds_angle(secs)
        rotate_image_around_base(screen, second_hand_img, sec_angle, CENTER, HAND_LENGTH // 2)

        # Re-draw center dot on top of hands
        pygame.draw.circle(screen, CLOCK_BORDER, CENTER, 8)

        # Digital readout
        draw_time_label(screen, font, mins, secs)

        # Title label
        title = title_font.render("Mickey's Clock  –  MM:SS", True, (120, 120, 120))
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
