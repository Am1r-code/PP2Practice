"""
paint.py — Practice 10: Paint Application
==========================================
Based on the NerdParadise Pygame tutorial (Part 6).
Extra features added:
  • Draw rectangle  (click-drag to size, then click to place)
  • Draw circle     (click-drag from centre, radius = drag distance)
  • Eraser tool     (paints with background colour)
  • Colour selection panel (palette of preset swatches + active preview)
  • Fully commented code
"""

import pygame
import sys
import math

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
WINDOW_W  = 900     # total window width
WINDOW_H  = 650     # total window height
PANEL_W   = 130     # width of the left tool / colour panel
CANVAS_X  = PANEL_W # canvas starts after the panel
CANVAS_W  = WINDOW_W - PANEL_W
CANVAS_H  = WINDOW_H

# Colours
COL_PANEL  = (30,  32,  42)    # tool panel background
COL_CANVAS = (245, 245, 240)   # default canvas (off-white)
COL_BORDER = (60,  65,  80)    # divider line between panel and canvas

# Default drawing settings
DEFAULT_COLOR     = (40,  40, 200)   # starting draw colour (blue)
DEFAULT_THICKNESS = 3               # pen/pencil stroke width in pixels
ERASER_SIZE       = 24              # diameter of the eraser

# Colour palette swatches shown in the panel
PALETTE = [
    (20,  20,  20),    # near-black
    (200, 200, 200),   # light grey
    (255, 255, 255),   # white
    (220,  40,  40),   # red
    (230, 130,  30),   # orange
    (240, 220,  40),   # yellow
    (60,  180,  60),   # green
    (40,  80,  200),   # blue
    (100,  40, 200),   # purple
    (200,  50, 150),   # pink
    (40,  180, 200),   # cyan
    (140,  80,  40),   # brown
]

# Available tools
TOOL_PENCIL = "pencil"
TOOL_RECT   = "rect"
TOOL_CIRCLE = "circle"
TOOL_ERASER = "eraser"

TOOLS = [TOOL_PENCIL, TOOL_RECT, TOOL_CIRCLE, TOOL_ERASER]
TOOL_LABELS = {
    TOOL_PENCIL: "✏ Pen",
    TOOL_RECT:   "▭ Rect",
    TOOL_CIRCLE: "○ Circle",
    TOOL_ERASER: "⌫ Erase",
}
# Fallback ASCII labels in case system font lacks the symbols
TOOL_LABELS_ASCII = {
    TOOL_PENCIL: "PEN",
    TOOL_RECT:   "RECT",
    TOOL_CIRCLE: "CIRC",
    TOOL_ERASER: "ERASE",
}


# ──────────────────────────────────────────────
# Panel layout helpers
# ──────────────────────────────────────────────
def swatch_rect(index: int) -> pygame.Rect:
    """Return the screen rectangle for palette swatch at `index`."""
    SWATCH = 28     # swatch size in pixels
    GAP    = 4      # gap between swatches
    cols   = 3      # swatches per row
    row    = index // cols
    col    = index  % cols
    x = 10 + col * (SWATCH + GAP)
    y = 310 + row * (SWATCH + GAP)
    return pygame.Rect(x, y, SWATCH, SWATCH)


def tool_rect(index: int) -> pygame.Rect:
    """Return the screen rectangle for tool button at `index`."""
    return pygame.Rect(10, 80 + index * 50, PANEL_W - 20, 40)


# ──────────────────────────────────────────────
# Draw the side panel
# ──────────────────────────────────────────────
def draw_panel(surface, font, current_tool, current_color, thickness):
    """Render the full left-hand tool panel."""
    # Background
    pygame.draw.rect(surface, COL_PANEL, (0, 0, PANEL_W, WINDOW_H))
    # Right border
    pygame.draw.line(surface, COL_BORDER, (PANEL_W - 1, 0), (PANEL_W - 1, WINDOW_H), 2)

    # ── App title ─────────────────────────────
    title = font.render("PAINT", True, (200, 210, 230))
    surface.blit(title, (PANEL_W // 2 - title.get_width() // 2, 12))
    pygame.draw.line(surface, COL_BORDER, (5, 60), (PANEL_W - 5, 60), 1)

    # ── Tool buttons ──────────────────────────
    tools_lbl = font.render("TOOLS", True, (140, 150, 170))
    surface.blit(tools_lbl, (10, 65))

    for i, tool in enumerate(TOOLS):
        r    = tool_rect(i)
        # Highlight the active tool
        col  = (70, 130, 180) if tool == current_tool else (50, 54, 68)
        pygame.draw.rect(surface, col, r, border_radius=6)
        pygame.draw.rect(surface, (90, 96, 120), r, 1, border_radius=6)

        lbl  = font.render(TOOL_LABELS_ASCII[tool], True, (220, 225, 235))
        surface.blit(lbl, (r.x + 6, r.y + 10))

    # ── Brush size ────────────────────────────
    pygame.draw.line(surface, COL_BORDER, (5, 290), (PANEL_W - 5, 290), 1)
    sz_lbl = font.render("SIZE", True, (140, 150, 170))
    surface.blit(sz_lbl, (10, 295))

    # Size indicator
    indicator_rect = pygame.Rect(10, 318, PANEL_W - 20, 8)
    pygame.draw.rect(surface, (60, 65, 80), indicator_rect, border_radius=4)
    fill_w = int((PANEL_W - 20) * (thickness / 30))
    pygame.draw.rect(surface, (100, 160, 220),
                     (10, 318, fill_w, 8), border_radius=4)

    sz_val = font.render(str(thickness), True, (200, 210, 230))
    surface.blit(sz_val, (PANEL_W // 2 - sz_val.get_width() // 2, 330))

    # +/- buttons for brush size
    btn_minus = pygame.Rect(10,            350, 50, 28)
    btn_plus  = pygame.Rect(PANEL_W - 60,  350, 50, 28)
    for btn, label in ((btn_minus, " – "), (btn_plus, " + ")):
        pygame.draw.rect(surface, (50, 54, 68), btn, border_radius=6)
        pygame.draw.rect(surface, (90, 96, 120), btn, 1, border_radius=6)
        bl = font.render(label, True, (220, 225, 235))
        surface.blit(bl, (btn.x + 4, btn.y + 6))

    # ── Colour palette ────────────────────────
    pygame.draw.line(surface, COL_BORDER, (5, 390), (PANEL_W - 5, 390), 1)
    col_lbl = font.render("COLOUR", True, (140, 150, 170))
    surface.blit(col_lbl, (10, 393))

    for i, color in enumerate(PALETTE):
        r = swatch_rect(i)
        # Offset palette section to be below the size controls
        r = r.move(0, 60)   # shift palette down to avoid overlap
        pygame.draw.rect(surface, color, r, border_radius=4)
        # Highlight swatch if it matches current colour
        if list(color) == list(current_color):
            pygame.draw.rect(surface, (255, 255, 255), r, 2, border_radius=4)
        else:
            pygame.draw.rect(surface, (70, 75, 90), r, 1, border_radius=4)

    # ── Current colour preview ─────────────────
    preview_y = 590
    prev_rect = pygame.Rect(10, preview_y, PANEL_W - 20, 30)
    pygame.draw.rect(surface, current_color, prev_rect, border_radius=6)
    pygame.draw.rect(surface, (90, 96, 120), prev_rect, 1, border_radius=6)


# ──────────────────────────────────────────────
# Utility: distance between two points
# ──────────────────────────────────────────────
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ──────────────────────────────────────────────
# Convert window coords → canvas coords
# ──────────────────────────────────────────────
def to_canvas(pos):
    return (pos[0] - CANVAS_X, pos[1])


def on_canvas(pos):
    return pos[0] >= CANVAS_X


def on_panel(pos):
    return pos[0] < CANVAS_X


# ──────────────────────────────────────────────
# Main application
# ──────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("🎨  Paint — Practice 10")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 16, bold=True)

    # ── Canvas surface ────────────────────────
    # We draw onto a separate surface so the panel is always on top.
    canvas = pygame.Surface((CANVAS_W, CANVAS_H))
    canvas.fill(COL_CANVAS)

    # ── Tool state ────────────────────────────
    current_tool  = TOOL_PENCIL
    current_color = list(DEFAULT_COLOR)
    thickness     = DEFAULT_THICKNESS

    # Mouse state
    drawing       = False    # True while left button is held
    prev_pos      = None     # last mouse position (used by pencil tool)
    drag_start    = None     # mouse position where drag began (rect / circle)

    # Preview layer — drawn on top of canvas each frame, cleared on mouse-up
    preview = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)

    # ── Main loop ─────────────────────────────
    while True:
        # Current mouse position in window coordinates
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard shortcuts ─────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:   current_tool = TOOL_PENCIL
                if event.key == pygame.K_r:   current_tool = TOOL_RECT
                if event.key == pygame.K_c:   current_tool = TOOL_CIRCLE
                if event.key == pygame.K_e:   current_tool = TOOL_ERASER
                # Clear canvas
                if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    canvas.fill(COL_CANVAS)
                # Save canvas as PNG
                if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    pygame.image.save(canvas, "drawing.png")

            # ── Mouse button DOWN ──────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # ── Panel click: tool selection ─
                if on_panel(mouse_pos):
                    # Check tool buttons
                    for i, tool in enumerate(TOOLS):
                        if tool_rect(i).collidepoint(mouse_pos):
                            current_tool = tool

                    # Check size buttons
                    btn_minus = pygame.Rect(10, 350, 50, 28)
                    btn_plus  = pygame.Rect(PANEL_W - 60, 350, 50, 28)
                    if btn_minus.collidepoint(mouse_pos):
                        thickness = max(1, thickness - 1)
                    if btn_plus.collidepoint(mouse_pos):
                        thickness = min(30, thickness + 1)

                    # Check palette swatches
                    for i, color in enumerate(PALETTE):
                        r = swatch_rect(i).move(0, 60)
                        if r.collidepoint(mouse_pos):
                            current_color = list(color)

                # ── Canvas click: start drawing ─
                elif on_canvas(mouse_pos):
                    drawing    = True
                    cx, cy     = to_canvas(mouse_pos)
                    drag_start = (cx, cy)
                    prev_pos   = (cx, cy)

                    # Pencil / eraser: paint immediately on press
                    if current_tool == TOOL_PENCIL:
                        pygame.draw.circle(canvas, current_color,
                                           (cx, cy), thickness)
                    elif current_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, COL_CANVAS,
                                           (cx, cy), ERASER_SIZE)

            # ── Mouse button UP ────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing and drag_start and on_canvas(mouse_pos):
                    cx, cy = to_canvas(mouse_pos)

                    # Commit the final shape to the canvas
                    if current_tool == TOOL_RECT:
                        # Draw rectangle from drag_start to release point
                        x0, y0 = drag_start
                        rx = min(x0, cx)
                        ry = min(y0, cy)
                        rw = abs(cx - x0)
                        rh = abs(cy - y0)
                        if rw > 1 and rh > 1:
                            pygame.draw.rect(canvas, current_color,
                                             (rx, ry, rw, rh), thickness)

                    elif current_tool == TOOL_CIRCLE:
                        # Draw circle: centre = drag_start, radius = distance to release
                        radius = int(dist(drag_start, (cx, cy)))
                        if radius > 1:
                            pygame.draw.circle(canvas, current_color,
                                               drag_start, radius, thickness)

                # Clear preview and reset state
                preview.fill((0, 0, 0, 0))
                drawing    = False
                prev_pos   = None
                drag_start = None

            # ── Mouse motion ───────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                if on_canvas(mouse_pos):
                    cx, cy = to_canvas(mouse_pos)

                    if current_tool == TOOL_PENCIL:
                        # Draw a line from the previous position to the current one
                        # to avoid gaps when the mouse moves fast
                        if prev_pos:
                            pygame.draw.line(canvas, current_color,
                                             prev_pos, (cx, cy), thickness * 2)
                        pygame.draw.circle(canvas, current_color,
                                           (cx, cy), thickness)
                        prev_pos = (cx, cy)

                    elif current_tool == TOOL_ERASER:
                        # Paint canvas background colour in a circle
                        if prev_pos:
                            pygame.draw.line(canvas, COL_CANVAS,
                                             prev_pos, (cx, cy), ERASER_SIZE * 2)
                        pygame.draw.circle(canvas, COL_CANVAS,
                                           (cx, cy), ERASER_SIZE)
                        prev_pos = (cx, cy)

                    elif current_tool == TOOL_RECT and drag_start:
                        # Live preview: draw ghost rect on the preview layer
                        preview.fill((0, 0, 0, 0))
                        x0, y0 = drag_start
                        rx = min(x0, cx)
                        ry = min(y0, cy)
                        rw = abs(cx - x0)
                        rh = abs(cy - y0)
                        if rw > 1 and rh > 1:
                            pygame.draw.rect(preview,
                                             (*current_color, 180),
                                             (rx, ry, rw, rh), thickness)

                    elif current_tool == TOOL_CIRCLE and drag_start:
                        # Live preview: ghost circle on the preview layer
                        preview.fill((0, 0, 0, 0))
                        radius = int(dist(drag_start, (cx, cy)))
                        if radius > 1:
                            pygame.draw.circle(preview,
                                               (*current_color, 180),
                                               drag_start, radius, thickness)

        # ── Render ────────────────────────────
        screen.fill((0, 0, 0))

        # Blit canvas
        screen.blit(canvas, (CANVAS_X, 0))
        # Blit transparent preview layer on top
        screen.blit(preview, (CANVAS_X, 0))

        # Eraser cursor indicator
        if current_tool == TOOL_ERASER and on_canvas(mouse_pos):
            cx, cy = to_canvas(mouse_pos)
            pygame.draw.circle(screen, (180, 50, 50),
                               (cx + CANVAS_X, cy), ERASER_SIZE, 2)

        # Draw panel (on top of everything)
        draw_panel(screen, font, current_tool, current_color, thickness)

        # Keyboard shortcut hints at the bottom of the canvas
        hint = font.render(
            "P=Pen  R=Rect  C=Circle  E=Erase  DEL=Clear  Ctrl+S=Save",
            True, (130, 135, 150))
        screen.blit(hint, (CANVAS_X + 8, WINDOW_H - 22))

        pygame.display.flip()
        clock.tick(60)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    main()
