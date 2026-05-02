"""
ball.py - Ball Entity
Encapsulates the ball's position, size, and movement logic.
"""

import pygame


class Ball:
    """
    A red ball that moves around the screen in discrete steps.

    Attributes
    ----------
    x, y    : int  – current centre position
    radius  : int  – ball radius (25 px → 50×50 bounding box)
    step    : int  – pixels moved per key press (20 px)
    color   : tuple – RGB colour of the ball
    """

    RADIUS = 25
    STEP   = 20
    COLOR  = (220, 40, 40)      # red
    BORDER_COLOR = (160, 20, 20)

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_w = screen_width
        self.screen_h = screen_height
        self.radius   = self.RADIUS
        self.step     = self.STEP
        # Start in the centre of the screen
        self.x = screen_width  // 2
        self.y = screen_height // 2

    # ── Movement ──────────────────────────────────────────────────────────────

    def move_up(self):
        """Move ball up by one step, ignoring the move if it would go off-screen."""
        new_y = self.y - self.step
        if new_y - self.radius >= 0:
            self.y = new_y

    def move_down(self):
        """Move ball down by one step, ignoring the move if it would go off-screen."""
        new_y = self.y + self.step
        if new_y + self.radius <= self.screen_h:
            self.y = new_y

    def move_left(self):
        """Move ball left by one step, ignoring the move if it would go off-screen."""
        new_x = self.x - self.step
        if new_x - self.radius >= 0:
            self.x = new_x

    def move_right(self):
        """Move ball right by one step, ignoring the move if it would go off-screen."""
        new_x = self.x + self.step
        if new_x + self.radius <= self.screen_w:
            self.x = new_x

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        """Render the ball onto `surface`."""
        center = (self.x, self.y)
        # Slightly darker outline for depth
        pygame.draw.circle(surface, self.BORDER_COLOR, center, self.radius + 2)
        pygame.draw.circle(surface, self.COLOR, center, self.radius)
        # Tiny specular highlight
        highlight_pos = (self.x - self.radius // 3, self.y - self.radius // 3)
        pygame.draw.circle(surface, (255, 120, 120), highlight_pos, self.radius // 5)
