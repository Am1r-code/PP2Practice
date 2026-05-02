"""
paint.py — Practice 11: Paint Application (Extended)
======================================================
Built on top of Practice 10. New shape tools added:

  NEW ► Square         — drag to set side length; constrained to equal W & H
  NEW ► Right triangle — drag defines the two legs (right-angle at drag origin)
  NEW ► Equilateral    — drag sets base width; height computed automatically
  NEW ► Rhombus        — drag sets full width and full height of bounding box

  Carried from Practice 10:
    • Pencil (freehand)
    • Rectangle
    • Circle
    • Eraser
    • Colour palette + brush size controls

All shapes show a semi-transparent live preview while the user drags.
Shapes are committed to the canvas on mouse-up.
"""

import pygame
import sys
import math

# ──────────────────────────────────────────────
# Window constants
# ──────────────────────────────────────────────
WINDOW_W = 980
WINDOW_H = 680
PANEL_W  = 150         # left panel width
CANVAS_X = PANEL_W
CANVAS_W = WINDOW_W - PANEL_W
CANVAS_H = WINDOW_H

# ──────────────────────────────────────────────
# Colours
# ──────────────────────────────────────────────
COL_PANEL  = (28,  30,  42)
COL_CANVAS = (248, 248, 244)
COL_BORDER = (55,  60,  78)

# Default drawing settings
DEFAULT_COLOR     = (40, 40, 200)
DEFAULT_THICKNESS = 3
ERASER_SIZE       = 24

# Colour palette swatches
PALETTE = [
    ( 20,  20,  20),   # near-black
    (200, 200, 200),   # grey
    (255, 255, 255),   # white
    (220,  40,  40),   # red
    (230, 130,  30),   # orange
    (240, 220,  40),   # yellow
    ( 60, 180,  60),   # green
    ( 40,  80, 200),   # blue
    (100,  40, 200),   # purple
    (200,  50, 150),   # pink
    ( 40, 180, 200),   # cyan
    (140,  80,  40),   # brown
]

# ──────────────────────────────────────────────
# Tool identifiers
# ──────────────────────────────────────────────
TOOL_PENCIL   = "pencil"
TOOL_RECT     = "rect"
TOOL_SQUARE   = "square"       # NEW
TOOL_CIRCLE   = "circle"
TOOL_RTRI     = "right_tri"    # NEW — right triangle
TOOL_EQTRI    = "equil_tri"    # NEW — equilateral triangle
TOOL_RHOMBUS  = "rhombus"      # NEW
TOOL_ERASER   = "eraser"

# Display order in the panel
TOOLS = [
    TOOL_PENCIL,
    TOOL_RECT,
    TOOL_SQUARE,
    TOOL_CIRCLE,
    TOOL_RTRI,
    TOOL_EQTRI,
    TOOL_RHOMBUS,
    TOOL_ERASER,
]

# Short labels shown on each button
TOOL_LABELS = {
    TOOL_PENCIL:  "PEN",
    TOOL_RECT:    "RECT",
    TOOL_SQUARE:  "SQUARE",
    TOOL_CIRCLE:  "CIRCLE",
    TOOL_RTRI:    "R-TRI",
    TOOL_EQTRI:   "EQ-TRI",
    TOOL_RHOMBUS: "RHOMB",
    TOOL_ERASER:  "ERASE",
}


# ──────────────────────────────────────────────
# Shape geometry helpers
# ──────────────────────────────────────────────
def right_triangle_pts(x0, y0, x1, y1):
    """
    Right triangle with the right angle at (x0, y0).
    The three vertices are:
      A = (x0, y0)  — right-angle corner
      B = (x1, y0)  — same row as A (horizontal leg)
      C = (x0, y1)  — same column as A (vertical leg)
    """
    return [(x0, y0), (x1, y0), (x0, y1)]


def equilateral_triangle_pts(x0, y0, x1, y1):
    """
    Equilateral triangle with base defined by x0→x1 along row y0.
    The apex is centred above (or below) the base.
    Height = (sqrt(3)/2) * base_width.
    The drag direction (y1 > y0 → apex up; y1 < y0 → apex down) controls orientation.
    """
    base_w  = abs(x1 - x0)
    height  = int(base_w * math.sqrt(3) / 2)

    # Base always from min_x to max_x at row y0
    bx0 = min(x0, x1)
    bx1 = max(x0, x1)
    mid_x = (bx0 + bx1) // 2

    # Apex direction: drag downward → apex below base; upward → apex above
    if y1 >= y0:
        apex_y = y0 + height
    else:
        apex_y = y0 - height

    return [(bx0, y0), (bx1, y0), (mid_x, apex_y)]


def rhombus_pts(x0, y0, x1, y1):
    """
    Rhombus (diamond) whose bounding box spans (x0,y0)→(x1,y1).
    The four vertices are the midpoints of the bounding-box sides.
    """
    cx = (x0 + x1) // 2   # horizontal centre
    cy = (y0 + y1) // 2   # vertical centre
    return [
        (cx, y0),    # top
        (x1, cy),    # right
        (cx, y1),    # bottom
        (x0, cy),    # left
    ]


def square_rect(x0, y0, x1, y1):
    """
    Constrain a drag rectangle to a square.
    The side length is the smaller of |dx| and |dy|,
    expanding in the correct quadrant from (x0, y0).
    """
    dx = x1 - x0
    dy = y1 - y0
    side = min(abs(dx), abs(dy))
    sx   = x0 + (side if dx >= 0 else -side)
    sy   = y0 + (side if dy >= 0 else -side)
    rx   = min(x0, sx)
    ry   = min(y0, sy)
    return rx, ry, side, side


# ──────────────────────────────────────────────
# Panel layout helpers
# ──────────────────────────────────────────────
TOOL_BTN_H  = 34    # height of each tool button
TOOL_BTN_GAP = 4    # vertical gap between buttons
TOOLS_Y0    = 74    # y-coordinate of the first tool button

def tool_rect(index: int) -> pygame.Rect:
    """Button rectangle for the tool at position `index`."""
    return pygame.Rect(8, TOOLS_Y0 + index * (TOOL_BTN_H + TOOL_BTN_GAP),
                       PANEL_W - 16, TOOL_BTN_H)

SWATCH_SIZE = 26
SWATCH_GAP  = 4
SWATCH_COLS = 3

def swatch_rect(index: int) -> pygame.Rect:
    """Palette swatch rectangle for colour `index`."""
    row = index // SWATCH_COLS
    col = index  % SWATCH_COLS
    # Start palette below the tool buttons + size controls
    palette_y0 = TOOLS_Y0 + len(TOOLS) * (TOOL_BTN_H + TOOL_BTN_GAP) + 68
    return pygame.Rect(
        8 + col * (SWATCH_SIZE + SWATCH_GAP),
        palette_y0 + row * (SWATCH_SIZE + SWATCH_GAP),
        SWATCH_SIZE, SWATCH_SIZE,
    )


# ──────────────────────────────────────────────
# Utility: convert window → canvas coordinates
# ──────────────────────────────────────────────
def to_canvas(pos):
    return (pos[0] - CANVAS_X, pos[1])

def on_canvas(pos):
    return pos[0] >= CANVAS_X

def on_panel(pos):
    return pos[0] < CANVAS_X

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ──────────────────────────────────────────────
# Shape drawing (canvas + preview)
# ──────────────────────────────────────────────
def draw_shape(surface, tool, color, thickness, x0, y0, x1, y1, alpha=255):
    """
    Draw the shape defined by `tool` onto `surface`.
    If alpha < 255 the colour is blended (used for preview).
    We use a helper surface for alpha support.
    """
    if alpha < 255:
        # Draw onto a temporary SRCALPHA surface, then blit
        tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        _draw_shape_on(tmp, tool, (*color, alpha), thickness, x0, y0, x1, y1)
        surface.blit(tmp, (0, 0))
    else:
        _draw_shape_on(surface, tool, color, thickness, x0, y0, x1, y1)


def _draw_shape_on(surface, tool, color, thickness, x0, y0, x1, y1):
    """Actual drawing logic, dispatched by tool name."""

    if tool == TOOL_RECT:
        # Rectangle from (x0,y0) to (x1,y1)
        rx = min(x0, x1); ry = min(y0, y1)
        rw = abs(x1 - x0); rh = abs(y1 - y0)
        if rw > 1 and rh > 1:
            pygame.draw.rect(surface, color, (rx, ry, rw, rh), thickness)

    elif tool == TOOL_SQUARE:
        # Square — constrained equal sides
        rx, ry, rw, rh = square_rect(x0, y0, x1, y1)
        if rw > 1:
            pygame.draw.rect(surface, color, (rx, ry, rw, rh), thickness)

    elif tool == TOOL_CIRCLE:
        # Circle: centre = drag start, radius = distance to release
        radius = int(dist((x0, y0), (x1, y1)))
        if radius > 1:
            pygame.draw.circle(surface, color, (x0, y0), radius, thickness)

    elif tool == TOOL_RTRI:
        # Right triangle
        pts = right_triangle_pts(x0, y0, x1, y1)
        if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:
            pygame.draw.polygon(surface, color, pts, thickness)

    elif tool == TOOL_EQTRI:
        # Equilateral triangle
        pts = equilateral_triangle_pts(x0, y0, x1, y1)
        if abs(x1 - x0) > 2:
            pygame.draw.polygon(surface, color, pts, thickness)

    elif tool == TOOL_RHOMBUS:
        # Rhombus (diamond)
        pts = rhombus_pts(x0, y0, x1, y1)
        if abs(x1 - x0) > 2 and abs(y1 - y0) > 2:
            pygame.draw.polygon(surface, color, pts, thickness)


# ──────────────────────────────────────────────
# Panel drawing
# ──────────────────────────────────────────────
def draw_panel(surface, font, current_tool, current_color, thickness):
    """Render the complete left-hand tool panel."""

    # Background + right border
    pygame.draw.rect(surface, COL_PANEL, (0, 0, PANEL_W, WINDOW_H))
    pygame.draw.line(surface, COL_BORDER, (PANEL_W - 1, 0), (PANEL_W - 1, WINDOW_H), 2)

    # Title
    t = font.render("PAINT", True, (190, 200, 220))
    surface.blit(t, (PANEL_W // 2 - t.get_width() // 2, 10))
    pygame.draw.line(surface, COL_BORDER, (5, 58), (PANEL_W - 5, 58), 1)

    tl = font.render("TOOLS", True, (130, 140, 165))
    surface.blit(tl, (8, 62))

    # Tool buttons
    for i, tool in enumerate(TOOLS):
        r   = tool_rect(i)
        col = (65, 120, 170) if tool == current_tool else (46, 50, 64)
        pygame.draw.rect(surface, col, r, border_radius=5)
        pygame.draw.rect(surface, (85, 92, 115), r, 1, border_radius=5)
        lbl = font.render(TOOL_LABELS[tool], True, (215, 222, 232))
        surface.blit(lbl, (r.x + 5, r.y + r.height // 2 - lbl.get_height() // 2))

    # Separator + SIZE label
    size_y0 = TOOLS_Y0 + len(TOOLS) * (TOOL_BTN_H + TOOL_BTN_GAP) + 4
    pygame.draw.line(surface, COL_BORDER, (5, size_y0), (PANEL_W - 5, size_y0), 1)
    sz_lbl = font.render("SIZE", True, (130, 140, 165))
    surface.blit(sz_lbl, (8, size_y0 + 4))

    # Thickness bar
    bar_y = size_y0 + 24
    pygame.draw.rect(surface, (58, 62, 78),
                     (8, bar_y, PANEL_W - 16, 8), border_radius=4)
    pygame.draw.rect(surface, (95, 155, 215),
                     (8, bar_y, int((PANEL_W - 16) * thickness / 30), 8),
                     border_radius=4)
    sv = font.render(str(thickness), True, (195, 205, 225))
    surface.blit(sv, (PANEL_W // 2 - sv.get_width() // 2, bar_y + 12))

    # +/- buttons
    btn_m = pygame.Rect(8,            bar_y + 32, 46, 26)
    btn_p = pygame.Rect(PANEL_W - 54, bar_y + 32, 46, 26)
    for btn, lbl in ((btn_m, " - "), (btn_p, " + ")):
        pygame.draw.rect(surface, (46, 50, 64), btn, border_radius=5)
        pygame.draw.rect(surface, (85, 92, 115), btn, 1, border_radius=5)
        bl = font.render(lbl, True, (215, 222, 232))
        surface.blit(bl, (btn.x + 4, btn.y + 5))

    # Separator + COLOUR label
    palette_y0 = TOOLS_Y0 + len(TOOLS) * (TOOL_BTN_H + TOOL_BTN_GAP) + 68
    sep_y = palette_y0 - 14
    pygame.draw.line(surface, COL_BORDER, (5, sep_y), (PANEL_W - 5, sep_y), 1)
    cl = font.render("COLOUR", True, (130, 140, 165))
    surface.blit(cl, (8, sep_y + 2))

    # Colour swatches
    for i, color in enumerate(PALETTE):
        r = swatch_rect(i)
        pygame.draw.rect(surface, color, r, border_radius=4)
        border_col = (255, 255, 255) if list(color) == list(current_color) \
                     else (68, 72, 88)
        pygame.draw.rect(surface, border_col, r, 2 if list(color) == list(current_color) else 1,
                         border_radius=4)

    # Active colour preview at very bottom
    prev = pygame.Rect(8, WINDOW_H - 36, PANEL_W - 16, 28)
    pygame.draw.rect(surface, current_color, prev, border_radius=6)
    pygame.draw.rect(surface, (85, 92, 115), prev, 1, border_radius=6)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Paint — Practice 11")
    clock  = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 14, bold=True)

    # The canvas is a separate surface so the panel always renders on top
    canvas  = pygame.Surface((CANVAS_W, CANVAS_H))
    canvas.fill(COL_CANVAS)

    # Preview layer (SRCALPHA) overlaid each frame; cleared on mouse-up
    preview = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)

    # Tool state
    current_tool  = TOOL_PENCIL
    current_color = list(DEFAULT_COLOR)
    thickness     = DEFAULT_THICKNESS

    # Mouse / drag state
    drawing    = False
    prev_pos   = None    # last position for pencil/eraser stroke
    drag_start = None    # canvas-coordinate origin of current drag

    # Identify whether the current tool draws a shape via polygon/rect/circle
    SHAPE_TOOLS = {TOOL_RECT, TOOL_SQUARE, TOOL_CIRCLE,
                   TOOL_RTRI, TOOL_EQTRI, TOOL_RHOMBUS}

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard shortcuts ─────────────
            if event.type == pygame.KEYDOWN:
                shortcuts = {
                    pygame.K_p: TOOL_PENCIL,
                    pygame.K_r: TOOL_RECT,
                    pygame.K_q: TOOL_SQUARE,
                    pygame.K_c: TOOL_CIRCLE,
                    pygame.K_t: TOOL_RTRI,
                    pygame.K_y: TOOL_EQTRI,
                    pygame.K_h: TOOL_RHOMBUS,
                    pygame.K_e: TOOL_ERASER,
                }
                if event.key in shortcuts:
                    current_tool = shortcuts[event.key]

                if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    canvas.fill(COL_CANVAS)   # clear canvas

                if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    pygame.image.save(canvas, "drawing.png")

            # ── Mouse button DOWN ──────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if on_panel(mouse_pos):
                    # Tool buttons
                    for i, tool in enumerate(TOOLS):
                        if tool_rect(i).collidepoint(mouse_pos):
                            current_tool = tool

                    # Size +/- buttons
                    size_y0 = TOOLS_Y0 + len(TOOLS) * (TOOL_BTN_H + TOOL_BTN_GAP) + 4
                    bar_y   = size_y0 + 24
                    btn_m   = pygame.Rect(8,            bar_y + 32, 46, 26)
                    btn_p   = pygame.Rect(PANEL_W - 54, bar_y + 32, 46, 26)
                    if btn_m.collidepoint(mouse_pos):
                        thickness = max(1, thickness - 1)
                    if btn_p.collidepoint(mouse_pos):
                        thickness = min(30, thickness + 1)

                    # Palette swatches
                    for i, color in enumerate(PALETTE):
                        if swatch_rect(i).collidepoint(mouse_pos):
                            current_color = list(color)

                elif on_canvas(mouse_pos):
                    drawing    = True
                    cx, cy     = to_canvas(mouse_pos)
                    drag_start = (cx, cy)
                    prev_pos   = (cx, cy)

                    # Pencil / eraser paint on click
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
                    x0, y0 = drag_start

                    # Commit all shape tools on release
                    if current_tool in SHAPE_TOOLS:
                        draw_shape(canvas, current_tool, current_color,
                                   thickness, x0, y0, cx, cy, alpha=255)

                # Reset drag state
                preview.fill((0, 0, 0, 0))
                drawing    = False
                prev_pos   = None
                drag_start = None

            # ── Mouse motion ───────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                if on_canvas(mouse_pos):
                    cx, cy = to_canvas(mouse_pos)

                    if current_tool == TOOL_PENCIL:
                        # Stroke: line segment from previous position → current
                        if prev_pos:
                            pygame.draw.line(canvas, current_color,
                                             prev_pos, (cx, cy), thickness * 2)
                        pygame.draw.circle(canvas, current_color,
                                           (cx, cy), thickness)
                        prev_pos = (cx, cy)

                    elif current_tool == TOOL_ERASER:
                        if prev_pos:
                            pygame.draw.line(canvas, COL_CANVAS,
                                             prev_pos, (cx, cy), ERASER_SIZE * 2)
                        pygame.draw.circle(canvas, COL_CANVAS,
                                           (cx, cy), ERASER_SIZE)
                        prev_pos = (cx, cy)

                    elif current_tool in SHAPE_TOOLS and drag_start:
                        # Live preview: draw semi-transparent shape on preview layer
                        preview.fill((0, 0, 0, 0))
                        x0, y0 = drag_start
                        draw_shape(preview, current_tool, current_color,
                                   thickness, x0, y0, cx, cy, alpha=160)

        # ── Render ────────────────────────────
        screen.fill((0, 0, 0))

        screen.blit(canvas,  (CANVAS_X, 0))
        screen.blit(preview, (CANVAS_X, 0))

        # Eraser cursor ring
        if current_tool == TOOL_ERASER and on_canvas(mouse_pos):
            ex, ey = to_canvas(mouse_pos)
            pygame.draw.circle(screen, (180, 50, 50),
                               (ex + CANVAS_X, ey), ERASER_SIZE, 2)

        draw_panel(screen, font, current_tool, current_color, thickness)

        # Shortcut hint bar at canvas bottom
        hints = ("P=Pen  R=Rect  Q=Square  C=Circle  "
                 "T=R-Tri  Y=Eq-Tri  H=Rhomb  E=Erase  DEL=Clear  Ctrl+S=Save")
        hint_surf = font.render(hints, True, (120, 128, 148))
        screen.blit(hint_surf, (CANVAS_X + 6, WINDOW_H - 20))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
