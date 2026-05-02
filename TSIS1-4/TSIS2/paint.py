"""
paint.py  –  Extended Paint Application  (TSIS 2)
=================================================
New tools over Practice 10/11:
  • Pencil   – freehand drawing
  • Line     – straight line with live preview
  • Fill     – flood-fill (BFS, exact colour match)
  • Text     – click to place, type, Enter to commit, Escape to cancel
  • Brush sizes: 1=small(2px)  2=medium(5px)  3=large(10px)
  • Ctrl+S   – save canvas as timestamped PNG

All Practice 10/11 shapes (rectangle, circle, square, right triangle,
equilateral triangle, rhombus, eraser) are retained and respect brush size.

Run:  python paint.py
"""

import sys
import datetime

import pygame

from tools import (
    PencilTool, LineTool,
    RectangleTool, FilledRectangleTool, CircleTool,
    SquareTool, RightTriangleTool, EquilateralTriangleTool, RhombusTool,
    EraserTool, FillTool, TextTool,
)

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────

WINDOW_W   = 1100
WINDOW_H   = 720
TOOLBAR_W  = 180           # left-side toolbar width
CANVAS_W   = WINDOW_W - TOOLBAR_W
CANVAS_H   = WINDOW_H

FPS = 60

# ── Colour palette ─────────────────────────────────────────────────────────
BG_TOOLBAR   = (30,  32,  40)
BG_CANVAS    = (255, 255, 255)
ACCENT       = (90, 180, 255)
ACCENT_DIM   = (50, 110, 170)
TEXT_LIGHT   = (210, 215, 225)
TEXT_MUTED   = (120, 125, 140)
HOVER_COLOR  = (50,  55,  70)
ACTIVE_COLOR = (60, 130, 220)
DIVIDER      = (50,  53,  65)

# 20-colour palette shown in the toolbar
PALETTE = [
    (  0,   0,   0), (255, 255, 255), (128, 128, 128), (192, 192, 192),
    (255,   0,   0), (128,   0,   0), (255, 165,   0), (255, 200,   0),
    (  0, 200,   0), (  0, 100,   0), (  0, 200, 200), (  0,   0, 255),
    (  0,   0, 128), (128,   0, 128), (255,   0, 255), (255, 182, 193),
    (210, 180, 140), (139,  69,  19), ( 30, 144, 255), (255, 215,   0),
]

BRUSH_SIZES = {1: 2, 2: 5, 3: 10}    # key = shortcut digit, value = px


# ─────────────────────────────────────────────────────────────────────────────
# Toolbar button descriptor
# ─────────────────────────────────────────────────────────────────────────────

class ToolButton:
    def __init__(self, label: str, tool_name: str, shortcut: str = ""):
        self.label      = label
        self.tool_name  = tool_name
        self.shortcut   = shortcut
        self.rect       = pygame.Rect(0, 0, 0, 0)   # set in layout

    def draw(self, surface, font, is_active: bool, hover: bool):
        color = ACTIVE_COLOR if is_active else (HOVER_COLOR if hover else BG_TOOLBAR)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        if is_active:
            pygame.draw.rect(surface, ACCENT, self.rect, 2, border_radius=6)

        lbl = font.render(self.label, True, TEXT_LIGHT)
        surface.blit(lbl, lbl.get_rect(midleft=(self.rect.x + 10, self.rect.centery)))

        if self.shortcut:
            sc = font.render(self.shortcut, True, TEXT_MUTED)
            surface.blit(sc, sc.get_rect(midright=(self.rect.right - 6, self.rect.centery)))


# ─────────────────────────────────────────────────────────────────────────────
# Main application class
# ─────────────────────────────────────────────────────────────────────────────

class PaintApp:

    TOOL_BUTTONS = [
        ToolButton("✏  Pencil",           "pencil",      "P"),
        ToolButton("╱  Line",             "line",        "L"),
        ToolButton("□  Rectangle",        "rectangle",   "R"),
        ToolButton("▪  Filled Rect",      "filled_rect", "F"),
        ToolButton("○  Circle",           "circle",      "C"),
        ToolButton("■  Square",           "square",      "Q"),
        ToolButton("△  Right Tri",        "right_tri",   "T"),
        ToolButton("△  Equil Tri",        "equil_tri",   "E"),
        ToolButton("◇  Rhombus",          "rhombus",     "H"),
        ToolButton("🪣  Fill",             "fill",        "G"),
        ToolButton("A  Text",             "text",        "X"),
        ToolButton("◻  Eraser",           "eraser",      "D"),
    ]

    TOOLS = {
        "pencil":      PencilTool(),
        "line":        LineTool(),
        "rectangle":   RectangleTool(),
        "filled_rect": FilledRectangleTool(),
        "circle":      CircleTool(),
        "square":      SquareTool(),
        "right_tri":   RightTriangleTool(),
        "equil_tri":   EquilateralTriangleTool(),
        "rhombus":     RhombusTool(),
        "fill":        FillTool(),
        "text":        TextTool(),
        "eraser":      EraserTool(),
    }

    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Paint – Extended (TSIS 2)")
        self.clock   = pygame.time.Clock()

        # Canvas lives on its own surface so toolbar never bleeds into saves
        self.canvas  = pygame.Surface((CANVAS_W, CANVAS_H))
        self.canvas.fill(BG_CANVAS)

        # Per-frame overlay for live previews (SRCALPHA)
        self.overlay = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)

        # State
        self.active_tool_name  = "pencil"
        self.drawing           = False
        self.color             = (0, 0, 0)
        self.brush_size_key    = 1          # 1 / 2 / 3
        self.mouse_on_canvas   = False

        # Fonts
        self.font_sm  = pygame.font.SysFont("dejavusans", 13)
        self.font_med = pygame.font.SysFont("dejavusans", 14, bold=True)
        self.font_hdr = pygame.font.SysFont("dejavusans", 15, bold=True)

        # Pre-compute toolbar button rects
        self._layout_toolbar()

        # Colour-swatch rects (computed in draw_toolbar)
        self._swatch_rects: list[pygame.Rect] = []

        # Size button rects
        self._size_rects: dict[int, pygame.Rect] = {}

        # Status message (bottom of toolbar)
        self._status = "Ready"

    # ── Layout ───────────────────────────────────────────────────────────────

    def _layout_toolbar(self):
        btn_h  = 30
        btn_w  = TOOLBAR_W - 16
        x      = 8
        y      = 50          # below the title

        for btn in self.TOOL_BUTTONS:
            btn.rect = pygame.Rect(x, y, btn_w, btn_h)
            y += btn_h + 4

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def active_tool(self):
        return self.TOOLS[self.active_tool_name]

    @property
    def brush_size(self) -> int:
        return BRUSH_SIZES[self.brush_size_key]

    # ── Canvas helpers ────────────────────────────────────────────────────────

    def canvas_pos(self, screen_pos: tuple) -> tuple:
        """Convert screen coordinates to canvas-local coordinates."""
        return (screen_pos[0] - TOOLBAR_W, screen_pos[1])

    def on_canvas(self, screen_pos: tuple) -> bool:
        """Return True if a screen position is inside the canvas area."""
        x, y = screen_pos
        return TOOLBAR_W <= x < WINDOW_W and 0 <= y < WINDOW_H

    # ── Save ─────────────────────────────────────────────────────────────────

    def save_canvas(self):
        """Save the canvas surface as a timestamped PNG file. (Ctrl+S)"""
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"canvas_{ts}.png"
        pygame.image.save(self.canvas, filename)
        self._status = f"Saved: {filename}"
        print(f"[Save] {filename}")

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():

            # ── Quit ─────────────────────────────────────────────────────────
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Key down ──────────────────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                # Ctrl+S → save
                if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    self.save_canvas()
                    continue

                # Text tool intercepts all other keys while active
                if isinstance(self.active_tool, TextTool) and self.active_tool.active:
                    self.active_tool.handle_keydown(event, self.canvas, self.color)
                    continue

                # Brush size shortcuts 1 / 2 / 3
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.brush_size_key = int(event.unicode)
                    self._status = f"Brush size: {self.brush_size}px"
                    continue

                # Tool shortcuts
                key_to_tool = {
                    pygame.K_p: "pencil",
                    pygame.K_l: "line",
                    pygame.K_r: "rectangle",
                    pygame.K_f: "filled_rect",
                    pygame.K_c: "circle",
                    pygame.K_q: "square",
                    pygame.K_t: "right_tri",
                    pygame.K_e: "equil_tri",
                    pygame.K_h: "rhombus",
                    pygame.K_g: "fill",
                    pygame.K_x: "text",
                    pygame.K_d: "eraser",
                }
                if event.key in key_to_tool:
                    self.active_tool_name = key_to_tool[event.key]
                    self._status = f"Tool: {self.active_tool_name}"

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # ── Mouse down ────────────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Toolbar click?
                if not self.on_canvas(pos):
                    self._handle_toolbar_click(pos)
                else:
                    self.drawing = True
                    cpos = self.canvas_pos(pos)
                    self.active_tool.on_mouse_down(
                        self.canvas, cpos, self.color, self.brush_size)

            # ── Mouse move ────────────────────────────────────────────────────
            elif event.type == pygame.MOUSEMOTION:
                if self.drawing and self.on_canvas(event.pos):
                    cpos = self.canvas_pos(event.pos)
                    self.active_tool.on_mouse_move(
                        self.canvas, cpos, self.color, self.brush_size)

            # ── Mouse up ──────────────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.drawing:
                    self.drawing = False
                    if self.on_canvas(event.pos):
                        cpos = self.canvas_pos(event.pos)
                        self.active_tool.on_mouse_up(
                            self.canvas, cpos, self.color, self.brush_size)

    def _handle_toolbar_click(self, pos: tuple):
        # Tool buttons
        for btn in self.TOOL_BUTTONS:
            if btn.rect.collidepoint(pos):
                self.active_tool_name = btn.tool_name
                self._status = f"Tool: {btn.tool_name}"
                return

        # Colour swatches
        for i, rect in enumerate(self._swatch_rects):
            if rect.collidepoint(pos):
                self.color = PALETTE[i]
                self._status = f"Color: RGB{self.color}"
                return

        # Size buttons
        for key, rect in self._size_rects.items():
            if rect.collidepoint(pos):
                self.brush_size_key = key
                self._status = f"Brush size: {BRUSH_SIZES[key]}px"
                return

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_toolbar(self):
        toolbar_rect = pygame.Rect(0, 0, TOOLBAR_W, WINDOW_H)
        pygame.draw.rect(self.screen, BG_TOOLBAR, toolbar_rect)

        # Right border
        pygame.draw.line(self.screen, DIVIDER, (TOOLBAR_W - 1, 0), (TOOLBAR_W - 1, WINDOW_H))

        # Title
        title = self.font_hdr.render("🎨 Paint", True, ACCENT)
        self.screen.blit(title, (12, 14))

        # Tool buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.TOOL_BUTTONS:
            is_active = (btn.tool_name == self.active_tool_name)
            hover     = btn.rect.collidepoint(mouse_pos) and not is_active
            btn.draw(self.screen, self.font_sm, is_active, hover)

        # Section: Brush size
        section_y = self.TOOL_BUTTONS[-1].rect.bottom + 14
        _draw_section_label(self.screen, self.font_sm, "BRUSH SIZE  [1/2/3]",
                            8, section_y, TEXT_MUTED)
        section_y += 18

        self._size_rects = {}
        labels = {1: "S 2px", 2: "M 5px", 3: "L 10px"}
        btn_w  = (TOOLBAR_W - 20) // 3
        for i, (key, lbl) in enumerate(labels.items()):
            rect = pygame.Rect(8 + i * (btn_w + 2), section_y, btn_w, 26)
            self._size_rects[key] = rect
            active = (key == self.brush_size_key)
            bg = ACTIVE_COLOR if active else HOVER_COLOR
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if active:
                pygame.draw.rect(self.screen, ACCENT, rect, 1, border_radius=4)
            txt = self.font_sm.render(lbl, True, TEXT_LIGHT)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        # Section: Colour palette
        section_y += 38
        _draw_section_label(self.screen, self.font_sm, "COLORS",
                            8, section_y, TEXT_MUTED)
        section_y += 18

        self._swatch_rects = []
        sw = 20   # swatch width / height
        gap = 3
        cols = (TOOLBAR_W - 16) // (sw + gap)
        for i, col in enumerate(PALETTE):
            row = i // cols
            c   = i %  cols
            rect = pygame.Rect(8 + c * (sw + gap), section_y + row * (sw + gap), sw, sw)
            self._swatch_rects.append(rect)
            pygame.draw.rect(self.screen, col, rect, border_radius=3)
            if col == self.color:
                pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=3)

        # Active colour swatch (large preview)
        preview_y = section_y + ((len(PALETTE) // cols) + 1) * (sw + gap) + 8
        pygame.draw.rect(self.screen, self.color,
                         pygame.Rect(8, preview_y, TOOLBAR_W - 16, 28), border_radius=5)
        pygame.draw.rect(self.screen, ACCENT,
                         pygame.Rect(8, preview_y, TOOLBAR_W - 16, 28), 1, border_radius=5)

        # Status bar
        status_surf = self.font_sm.render(self._status, True, TEXT_MUTED)
        self.screen.blit(status_surf, (8, WINDOW_H - 22))

    def draw_frame(self):
        """Compose one full frame."""
        # Draw canvas onto screen
        self.screen.blit(self.canvas, (TOOLBAR_W, 0))

        # Draw live preview overlay
        self.overlay.fill((0, 0, 0, 0))
        mouse_pos = pygame.mouse.get_pos()
        if self.on_canvas(mouse_pos):
            cpos = self.canvas_pos(mouse_pos)
            self.active_tool.draw_preview(
                self.overlay, cpos, self.color, self.brush_size)
        self.screen.blit(self.overlay, (TOOLBAR_W, 0))

        # Draw toolbar on top
        self.draw_toolbar()

        pygame.display.flip()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.handle_events()
            self.draw_frame()
            self.clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def _draw_section_label(surface, font, text, x, y, color):
    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = PaintApp()
    app.run()
