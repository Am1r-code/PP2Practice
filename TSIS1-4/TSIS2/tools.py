"""
tools.py  –  Drawing tool implementations for the Paint application (TSIS 2)
============================================================================
Each tool is a class that implements a common interface:

    on_mouse_down(canvas, pos, color, size)  – called on MOUSEBUTTONDOWN
    on_mouse_move(canvas, pos, color, size)  – called on MOUSEMOTION (btn held)
    on_mouse_up  (canvas, pos, color, size)  – called on MOUSEBUTTONUP
    draw_preview (overlay, pos, color, size) – draw a live-preview onto a
                                               transparent overlay surface
                                               (called every frame while active)

`canvas`  is the persistent drawing surface (pygame.Surface).
`overlay` is a per-frame transparent surface for in-progress previews.
"""

import pygame
import collections


# ─────────────────────────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────────────────────────

class BaseTool:
    """Provides no-op defaults so subclasses only override what they need."""

    def on_mouse_down(self, canvas, pos, color, size):
        pass

    def on_mouse_move(self, canvas, pos, color, size):
        pass

    def on_mouse_up(self, canvas, pos, color, size):
        pass

    def draw_preview(self, overlay, pos, color, size):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  Pencil (freehand)
# ─────────────────────────────────────────────────────────────────────────────

class PencilTool(BaseTool):
    """
    Draws continuously while the mouse button is held.
    Connects consecutive cursor positions with pygame.draw.line so fast
    movements produce smooth strokes rather than dotted gaps.
    """

    def __init__(self):
        self._last_pos = None

    def on_mouse_down(self, canvas, pos, color, size):
        # Start a new stroke: paint a single dot at the click point.
        pygame.draw.circle(canvas, color, pos, size // 2)
        self._last_pos = pos

    def on_mouse_move(self, canvas, pos, color, size):
        if self._last_pos is not None:
            pygame.draw.line(canvas, color, self._last_pos, pos, size)
            # Draw a circle at each joint so diagonal lines have rounded ends.
            pygame.draw.circle(canvas, color, pos, size // 2)
            self._last_pos = pos

    def on_mouse_up(self, canvas, pos, color, size):
        self._last_pos = None


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  Straight Line tool (with live preview)
# ─────────────────────────────────────────────────────────────────────────────

class LineTool(BaseTool):
    """
    Click → drag → release to draw a straight line.
    A dashed preview is shown on the overlay during drag.
    """

    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start is not None:
            pygame.draw.line(canvas, color, self._start, pos, size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start is not None:
            # Semi-transparent preview line
            preview_color = color + (160,)  # add alpha
            pygame.draw.line(overlay, preview_color, self._start, pos, size)


# ─────────────────────────────────────────────────────────────────────────────
# Rectangle tool (from Practice 10, size-aware)
# ─────────────────────────────────────────────────────────────────────────────

class RectangleTool(BaseTool):
    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            rect = _points_to_rect(self._start, pos)
            pygame.draw.rect(canvas, color, rect, size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            rect = _points_to_rect(self._start, pos)
            pygame.draw.rect(overlay, color + (160,), rect, size)


# ─────────────────────────────────────────────────────────────────────────────
# Filled Rectangle
# ─────────────────────────────────────────────────────────────────────────────

class FilledRectangleTool(BaseTool):
    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            rect = _points_to_rect(self._start, pos)
            pygame.draw.rect(canvas, color, rect)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            rect = _points_to_rect(self._start, pos)
            pygame.draw.rect(overlay, color + (100,), rect)


# ─────────────────────────────────────────────────────────────────────────────
# Circle tool (from Practice 10, size-aware)
# ─────────────────────────────────────────────────────────────────────────────

class CircleTool(BaseTool):
    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            radius = _dist(self._start, pos)
            pygame.draw.circle(canvas, color, self._start, max(1, int(radius)), size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            radius = max(1, int(_dist(self._start, pos)))
            pygame.draw.circle(overlay, color + (160,), self._start, radius, size)


# ─────────────────────────────────────────────────────────────────────────────
# Square tool (Practice 11)
# ─────────────────────────────────────────────────────────────────────────────

class SquareTool(BaseTool):
    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            side = int(max(abs(pos[0] - self._start[0]), abs(pos[1] - self._start[1])))
            sign_x = 1 if pos[0] >= self._start[0] else -1
            sign_y = 1 if pos[1] >= self._start[1] else -1
            end = (self._start[0] + sign_x * side, self._start[1] + sign_y * side)
            rect = _points_to_rect(self._start, end)
            pygame.draw.rect(canvas, color, rect, size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            side = int(max(abs(pos[0] - self._start[0]), abs(pos[1] - self._start[1])))
            sign_x = 1 if pos[0] >= self._start[0] else -1
            sign_y = 1 if pos[1] >= self._start[1] else -1
            end = (self._start[0] + sign_x * side, self._start[1] + sign_y * side)
            rect = _points_to_rect(self._start, end)
            pygame.draw.rect(overlay, color + (160,), rect, size)


# ─────────────────────────────────────────────────────────────────────────────
# Right Triangle tool (Practice 11)
# ─────────────────────────────────────────────────────────────────────────────

class RightTriangleTool(BaseTool):
    def __init__(self):
        self._start = None

    def _points(self, start, end):
        """Return the three vertices of a right triangle from bounding corners."""
        x0, y0 = start
        x1, y1 = end
        return [(x0, y0), (x1, y0), (x1, y1)]

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            pygame.draw.polygon(canvas, color, self._points(self._start, pos), size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            pygame.draw.polygon(overlay, color + (160,), self._points(self._start, pos), size)


# ─────────────────────────────────────────────────────────────────────────────
# Equilateral Triangle tool (Practice 11)
# ─────────────────────────────────────────────────────────────────────────────

class EquilateralTriangleTool(BaseTool):
    """Click = apex, drag to set the size (base midpoint distance)."""

    def __init__(self):
        self._start = None

    def _points(self, apex, end):
        import math
        side = _dist(apex, end) * 1.5
        h = side * (3 ** 0.5) / 2
        cx = apex[0]
        top_y = apex[1]
        bot_y = top_y + h
        return [
            (cx, top_y),
            (cx - side / 2, bot_y),
            (cx + side / 2, bot_y),
        ]

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            pts = self._points(self._start, pos)
            pygame.draw.polygon(canvas, color, pts, size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            pts = self._points(self._start, pos)
            pygame.draw.polygon(overlay, color + (160,), pts, size)


# ─────────────────────────────────────────────────────────────────────────────
# Rhombus tool (Practice 11)
# ─────────────────────────────────────────────────────────────────────────────

class RhombusTool(BaseTool):
    def __init__(self):
        self._start = None

    def _points(self, start, end):
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        return [
            (cx, start[1]),
            (end[0], cy),
            (cx, end[1]),
            (start[0], cy),
        ]

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            pygame.draw.polygon(canvas, color, self._points(self._start, pos), size)
            self._start = None

    def draw_preview(self, overlay, pos, color, size):
        if self._start:
            pygame.draw.polygon(overlay, color + (160,), self._points(self._start, pos), size)


# ─────────────────────────────────────────────────────────────────────────────
# Eraser tool (from Practice 10)
# ─────────────────────────────────────────────────────────────────────────────

class EraserTool(BaseTool):
    """Paints white over the canvas, using size to control eraser width."""

    WHITE = (255, 255, 255)

    def __init__(self):
        self._last_pos = None

    def on_mouse_down(self, canvas, pos, color, size):
        erase_size = size * 4          # eraser is larger than a pencil stroke
        pygame.draw.circle(canvas, self.WHITE, pos, erase_size)
        self._last_pos = pos

    def on_mouse_move(self, canvas, pos, color, size):
        erase_size = size * 4
        if self._last_pos:
            pygame.draw.line(canvas, self.WHITE, self._last_pos, pos, erase_size * 2)
            pygame.draw.circle(canvas, self.WHITE, pos, erase_size)
        self._last_pos = pos

    def on_mouse_up(self, canvas, pos, color, size):
        self._last_pos = None

    def draw_preview(self, overlay, pos, color, size):
        erase_size = size * 4
        pygame.draw.circle(overlay, (180, 180, 180, 120), pos, erase_size, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 3.3  Flood Fill tool
# ─────────────────────────────────────────────────────────────────────────────

class FillTool(BaseTool):
    """
    Bucket flood-fill using an iterative BFS approach.
    Uses pygame.Surface.get_at() / set_at() – no extra libraries required.
    Stops at pixels that differ from the seed colour (exact match).
    """

    def on_mouse_down(self, canvas, pos, color, size):
        _flood_fill(canvas, pos, color)


def _flood_fill(surface: pygame.Surface, seed: tuple, fill_color: tuple):
    """
    Iterative BFS flood fill on a pygame Surface.

    Parameters
    ----------
    surface    : target Surface (modified in place)
    seed       : (x, y) pixel where the fill starts
    fill_color : RGB or RGBA tuple – colour to paint with
    """
    width, height = surface.get_size()
    x0, y0 = int(seed[0]), int(seed[1])

    # Guard: seed must be inside the canvas
    if not (0 <= x0 < width and 0 <= y0 < height):
        return

    # Normalise fill colour to a 3-tuple for comparison
    target_color = surface.get_at((x0, y0))[:3]
    fill_rgb      = fill_color[:3]

    if target_color == fill_rgb:
        return          # nothing to do

    visited = set()
    queue   = collections.deque()
    queue.append((x0, y0))
    visited.add((x0, y0))

    while queue:
        x, y = queue.popleft()
        surface.set_at((x, y), fill_color)

        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if (0 <= nx < width and 0 <= ny < height
                    and (nx, ny) not in visited
                    and surface.get_at((nx, ny))[:3] == target_color):
                visited.add((nx, ny))
                queue.append((nx, ny))


# ─────────────────────────────────────────────────────────────────────────────
# 3.5  Text tool
# ─────────────────────────────────────────────────────────────────────────────

class TextTool(BaseTool):
    """
    Click to place an insertion point; type characters; Enter to commit;
    Escape to cancel.  The live text is drawn via draw_preview() each frame.
    """

    def __init__(self):
        self.active    = False
        self.pos       = (0, 0)
        self.text      = ""
        self._font     = None
        self._font_size = 24

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("dejavusans", self._font_size)
        return self._font

    def on_mouse_down(self, canvas, pos, color, size):
        # Each click repositions the cursor (discards any pending text)
        self.active = True
        self.pos    = pos
        self.text   = ""

    def handle_keydown(self, event, canvas, color) -> bool:
        """
        Call from the main event loop for KEYDOWN events while text tool is
        active.  Returns True when the text has been committed or cancelled.
        """
        if not self.active:
            return False

        if event.key == pygame.K_RETURN:
            self._commit(canvas, color)
            return True
        elif event.key == pygame.K_ESCAPE:
            self.active = False
            self.text   = ""
            return True
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        else:
            char = event.unicode
            if char and char.isprintable():
                self.text += char
        return False

    def _commit(self, canvas, color):
        """Render the current text permanently onto the canvas."""
        if self.text:
            font  = self._get_font()
            surf  = font.render(self.text, True, color)
            canvas.blit(surf, self.pos)
        self.active = False
        self.text   = ""

    def draw_preview(self, overlay, pos, color, size):
        if not self.active:
            return
        font = self._get_font()

        # Render the typed text (or a placeholder)
        display = self.text if self.text else ""
        if display:
            surf = font.render(display, True, color)
            overlay.blit(surf, self.pos)

        # Blinking cursor line
        text_w = font.size(display)[0]
        cx = self.pos[0] + text_w + 2
        cy = self.pos[1]
        if (pygame.time.get_ticks() // 500) % 2 == 0:      # blink every 500 ms
            pygame.draw.line(overlay, color + (200,),
                             (cx, cy), (cx, cy + self._font_size), 2)


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _points_to_rect(p1: tuple, p2: tuple) -> pygame.Rect:
    """Return a normalised pygame.Rect from any two corner points."""
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p2[0] - p1[0])
    h = abs(p2[1] - p1[1])
    return pygame.Rect(x, y, max(w, 1), max(h, 1))


def _dist(p1: tuple, p2: tuple) -> float:
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
