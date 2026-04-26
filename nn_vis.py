"""
nn_visualizer.py  –  Pygame visualizer for NeuralNetwork from neural_network.py

Usage
-----
    import numpy as np
    from neural_network import NeuralNetwork
    from nn_visualizer import NeuralNetworkVisualizer
    import pygame

    nn = NeuralNetwork([3, 4, 4, 2])
    # optionally run a forward pass first so activations are populated
    nn.forward([0.5, -0.3, 0.8])

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock  = pygame.time.Clock()
    vis    = NeuralNetworkVisualizer(nn, width=1280, height=720)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            vis.handle_event(event)

        vis.draw()                        # draws onto its internal surface
        screen.blit(vis.surface, (0, 0))  # blit onto your display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
"""

import math
import numpy as np
import pygame


# ──────────────────────────────────────────────────────────────────────────────
# Colour helpers
# ──────────────────────────────────────────────────────────────────────────────

_BG          = (15,  17,  26)
_PANEL_BG    = (24,  28,  44)
_PANEL_BORDER= (60,  80, 130)
_TEXT_MAIN   = (220, 225, 245)
_TEXT_DIM    = (120, 130, 160)
_TEXT_ACCENT = (100, 200, 255)
_SHADOW      = (0,   0,   0,  120)

def _lerp_colour(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _neuron_colour(activation: float) -> tuple:
    """Map activation value → RGB.  Negative → blue, zero → dark, positive → gold."""
    if activation >= 0:
        dark = (30, 30, 50)
        bright = (255, 210, 60)
        t = min(activation, 1.0)
        return _lerp_colour(dark, bright, t)
    else:
        dark = (30, 30, 50)
        bright = (60, 120, 255)
        t = min(-activation, 1.0)
        return _lerp_colour(dark, bright, t)

def _weight_colour(weight: float) -> tuple:
    """Negative weight → red, zero → dim grey, positive → cyan."""
    if weight >= 0:
        base = (30, 35, 50)
        hi   = (40, 200, 220)
        t = min(abs(weight), 1.0)
        return _lerp_colour(base, hi, t)
    else:
        base = (30, 35, 50)
        hi   = (220, 60, 60)
        t = min(abs(weight), 1.0)
        return _lerp_colour(base, hi, t)

def _weight_alpha(weight: float) -> int:
    return max(30, min(220, int(abs(weight) * 180 + 40)))


# ──────────────────────────────────────────────────────────────────────────────
# Smooth camera
# ──────────────────────────────────────────────────────────────────────────────

class _Camera:
    def __init__(self):
        self.x      = 0.0
        self.y      = 0.0
        self.zoom   = 1.0
        self.tx     = 0.0   # target x
        self.ty     = 0.0
        self.tzoom  = 1.0
        self._speed = 12.0  # lerp speed (per second)

    def update(self, dt: float):
        s = min(1.0, self._speed * dt)
        self.x    += (self.tx    - self.x)    * s
        self.y    += (self.ty    - self.y)    * s
        self.zoom += (self.tzoom - self.zoom) * s

    def world_to_screen(self, wx, wy, sw, sh):
        sx = (wx - self.x) * self.zoom + sw / 2
        sy = (wy - self.y) * self.zoom + sh / 2
        return sx, sy

    def screen_to_world(self, sx, sy, sw, sh):
        wx = (sx - sw / 2) / self.zoom + self.x
        wy = (sy - sh / 2) / self.zoom + self.y
        return wx, wy

    def pan(self, dx, dy):
        self.tx -= dx / self.zoom
        self.ty -= dy / self.zoom

    def zoom_at(self, sx, sy, sw, sh, factor):
        wx, wy = self.screen_to_world(sx, sy, sw, sh)
        self.tzoom = max(0.15, min(8.0, self.tzoom * factor))
        # keep the world point under the cursor fixed
        self.tx = wx - (sx - sw / 2) / self.tzoom
        self.ty = wy - (sy - sh / 2) / self.tzoom

    def focus_on(self, wx, wy, target_zoom=2.5):
        self.tx    = wx
        self.ty    = wy
        self.tzoom = target_zoom


# ──────────────────────────────────────────────────────────────────────────────
# Detail panel  (fullscreen overlay)
# ──────────────────────────────────────────────────────────────────────────────

class _DetailPanel:
    PAD        = 36       # outer margin
    MARGIN     = 20       # inner margin
    CHIP_W     = 160      # width of each input/weight chip
    CHIP_H     = 48       # height of each chip
    CHIP_GAP_X = 12
    CHIP_GAP_Y = 10
    MAX_ITEMS  = 5       # max inputs / weights to show

    def __init__(self):
        self.visible    = False
        self.layer_idx  = 0
        self.neuron_idx = 0
        self.nn         = None
        self._close_rect = pygame.Rect(0, 0, 0, 0)

    def show(self, nn, layer_idx, neuron_idx):
        self.nn         = nn
        self.layer_idx  = layer_idx
        self.neuron_idx = neuron_idx
        self.visible    = True

    def hide(self):
        self.visible = False

    def hit_close(self, pos):
        return self._close_rect.collidepoint(pos)

    # ── chip grid helper ──────────────────────────────────────────────────────

    def _draw_chip_grid(self, surface, items, x0, y0, available_w, fonts,
                        label_fn, value_fn, colour_fn, total_count):
        """
        Draw items as chips flowing left→right, wrapping down.
        items   : list of values to show (already truncated to MAX_ITEMS)
        label_fn(i, v) → str   small label text
        value_fn(i, v) → str   value text
        colour_fn(v)   → RGB   chip accent colour
        total_count    : real count (for "… N more" footer)
        Returns the y coordinate after the last row.
        """
        fh, fb, ft = fonts
        CW, CH = self.CHIP_W, self.CHIP_H
        GX, GY = self.CHIP_GAP_X, self.CHIP_GAP_Y
        cols = max(1, (available_w + GX) // (CW + GX))

        cy = y0
        for idx, v in enumerate(items):
            col_i = idx % cols
            row_i = idx // cols
            cx = x0 + col_i * (CW + GX)
            cy_chip = y0 + row_i * (CH + GY)

            accent = colour_fn(v)
            dark   = tuple(max(0, c - 120) for c in accent)

            # chip background
            chip_rect = pygame.Rect(cx, cy_chip, CW, CH)
            pygame.draw.rect(surface, (28, 32, 52), chip_rect, border_radius=6)
            # left accent bar
            pygame.draw.rect(surface, accent,
                             pygame.Rect(cx, cy_chip, 4, CH), border_radius=3)
            # label
            lbl = ft.render(label_fn(idx, v), True, _TEXT_DIM)
            surface.blit(lbl, (cx + 10, cy_chip + 4))
            # value
            val_txt = value_fn(idx, v)
            val_col = _lerp_colour(_TEXT_DIM, accent, min(1.0, abs(v)))
            val = fb.render(val_txt, True, val_col)
            surface.blit(val, (cx + 10, cy_chip + CH - val.get_height() - 5))

            cy = cy_chip + CH  # track last row bottom

        n_rows = math.ceil(len(items) / cols)
        bottom = y0 + n_rows * (CH + GY) - GY

        shown = len(items)
        if total_count > shown:
            more = ft.render(f"… {total_count - shown} more not shown", True, _TEXT_DIM)
            surface.blit(more, (x0, bottom + 6))
            bottom += more.get_height() + 6

        return bottom

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface, fonts):
        if not self.visible or self.nn is None:
            return

        fh, fb, ft = fonts
        sw, sh = surface.get_size()
        P  = self.PAD
        M  = self.MARGIN

        # ── dim backdrop ──────────────────────────────────────────────────────
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surface.blit(dim, (0, 0))

        # ── window rect ───────────────────────────────────────────────────────
        wx0 = P
        wy0 = P
        ww  = sw - 2 * P
        wh  = sh - 2 * P

        win = pygame.Surface((ww, wh), pygame.SRCALPHA)
        win.fill((*_PANEL_BG, 248))
        pygame.draw.rect(win, _PANEL_BORDER, (0, 0, ww, wh), 2, border_radius=12)
        surface.blit(win, (wx0, wy0))

        # inner content area
        ix = wx0 + M
        iy = wy0 + M
        iw = ww - 2 * M

        layer = self.nn.layers[self.layer_idx]
        ni    = self.neuron_idx

        # ── close button ──────────────────────────────────────────────────────
        cr = pygame.Rect(wx0 + ww - 36, wy0 + 8, 28, 28)
        pygame.draw.circle(surface, (160, 50, 50), cr.center, 14)
        pygame.draw.circle(surface, (220, 80, 80), cr.center, 14, 2)
        x_lbl = fh.render("×", True, (255, 255, 255))
        surface.blit(x_lbl, x_lbl.get_rect(center=cr.center))
        self._close_rect = cr

        cy = iy  # running y cursor

        # ── title bar ─────────────────────────────────────────────────────────
        act_fn = layer.activation.upper()
        title  = fh.render(
            f"Layer {self.layer_idx + 1}   ·   Neuron {ni}   ·   {act_fn}",
            True, _TEXT_ACCENT)
        surface.blit(title, (ix, cy))
        cy += title.get_height() + 8
        pygame.draw.line(surface, _PANEL_BORDER, (ix, cy), (ix + iw, cy))
        cy += 14

        # ── summary row (z, activation value) ────────────────────────────────
        has_data = layer.input is not None and layer.output is not None
        if has_data:
            inp = np.asarray(layer.input).flatten()
            out = np.asarray(layer.output).flatten()
            z   = float(layer.W[ni] @ inp + layer.b[ni])
            a   = float(out[ni]) if ni < len(out) else float("nan")
            bias = float(layer.b[ni])

            summary_items = [
                ("bias  b",       f"{bias:+.5f}", (160, 140, 220)),
                ("pre-act  z",    f"{z:+.5f}",   (200, 180, 80)),
                (f"{act_fn}(z)",  f"{a:+.5f}",   (80, 210, 140)),
            ]
            box_w = (iw - 2 * self.CHIP_GAP_X) // 3
            for bi, (lbl_txt, val_txt, col) in enumerate(summary_items):
                bx = ix + bi * (box_w + self.CHIP_GAP_X)
                by = cy
                pygame.draw.rect(surface, (22, 26, 44),
                                 pygame.Rect(bx, by, box_w, 54), border_radius=8)
                pygame.draw.rect(surface, col,
                                 pygame.Rect(bx, by, box_w, 4), border_radius=3)
                lbl_s = ft.render(lbl_txt, True, _TEXT_DIM)
                val_s = fb.render(val_txt, True, col)
                surface.blit(lbl_s, (bx + 10, by + 8))
                surface.blit(val_s, (bx + 10, by + 54 - val_s.get_height() - 8))
            cy += 54 + 18
        else:
            note = fb.render("No forward pass data yet.", True, _TEXT_DIM)
            surface.blit(note, (ix, cy))
            cy += note.get_height() + 18

        pygame.draw.line(surface, _PANEL_BORDER, (ix, cy), (ix + iw, cy))
        cy += 14

        # ── split: inputs left, weights right ─────────────────────────────────
        half_w   = (iw - 24) // 2
        left_x   = ix
        right_x  = ix + half_w + 24

        # section headers
        ih = fb.render("Inputs  x[i]", True, _TEXT_DIM)
        wh_lbl = fb.render(f"Weights  W[{ni}, i]", True, _TEXT_DIM)
        surface.blit(ih,     (left_x,  cy))
        surface.blit(wh_lbl, (right_x, cy))
        cy += ih.get_height() + 8

        # vertical divider between the two columns
        mid_x = ix + half_w + 12
        pygame.draw.line(surface, _PANEL_BORDER,
                         (mid_x, cy - 6), (mid_x, wy0 + wh - M))

        if has_data:
            inp   = np.asarray(layer.input).flatten()
            w_row = layer.W[ni]

            inp_show = inp[:self.MAX_ITEMS].tolist()
            w_show   = w_row[:self.MAX_ITEMS].tolist()

            def inp_colour(v):
                return _neuron_colour(v)

            def w_colour(v):
                return _weight_colour(v)

            bottom_inp = self._draw_chip_grid(
                surface, inp_show, left_x, cy, half_w, fonts,
                label_fn=lambda i, v: f"x[{i}]",
                value_fn=lambda i, v: f"{v:+.4f}",
                colour_fn=inp_colour,
                total_count=len(inp))

            bottom_w = self._draw_chip_grid(
                surface, w_show, right_x, cy, half_w, fonts,
                label_fn=lambda i, v: f"W[{ni},{i}]",
                value_fn=lambda i, v: f"{v:+.4f}",
                colour_fn=w_colour,
                total_count=len(w_row))
        else:
            note = fb.render("Run a forward pass to see values.", True, _TEXT_DIM)
            surface.blit(note, (left_x, cy))


# ──────────────────────────────────────────────────────────────────────────────
# Main visualiser
# ──────────────────────────────────────────────────────────────────────────────

class NeuralNetworkVisualizer:
    """
    Draws a NeuralNetwork onto an internal pygame.Surface.

    Parameters
    ----------
    nn          : NeuralNetwork instance
    width, height : size of the internal surface (and therefore the blit footprint)
    max_neurons : clip very large layers to this many displayed neurons
    """

    NEURON_R   = 22          # world-space radius
    LAYER_GAP  = 200         # horizontal gap between layers
    NEURON_GAP = 60          # vertical gap between neuron centres

    def __init__(self, nn, width=1280, height=720, max_neurons=20, offset=(0, 0)):
        self.nn          = nn
        self.width       = width
        self.height      = height
        self.max_neurons = max_neurons
        self.offset      = offset
        self.surface     = pygame.Surface((width, height))

        self._cam    = _Camera()
        self._panel  = _DetailPanel()
        self._panning = False
        self._pan_start = (0, 0)
        self._last_ms   = pygame.time.get_ticks()

        # pre-build layout positions (world space)
        self._positions = self._compute_positions()

        # fonts  (initialise lazily so caller can init pygame before us)
        self._font_body    = None
        self._font_heading = None
        self._font_tiny    = None

        # hover state
        self._hovered = None   # (layer_idx, neuron_idx) or None

    # ── layout ────────────────────────────────────────────────────────────────

    def _compute_positions(self):
        """Return list of lists of (wx, wy) world positions.
        Index li corresponds to nn.layers[li] (output neurons).
        Input layer is NOT shown."""
        nn = self.nn
        sizes = [nn.layer_sizes[i + 1] for i in range(len(nn.layers))]
        n_layers = len(sizes)

        total_w = (n_layers - 1) * self.LAYER_GAP
        start_x = -total_w / 2

        positions = []
        for li, size in enumerate(sizes):
            disp = min(size, self.max_neurons)
            total_h = (disp - 1) * self.NEURON_GAP
            start_y = -total_h / 2
            lpos = []
            for ni in range(disp):
                wx = start_x + li * self.LAYER_GAP
                wy = start_y + ni * self.NEURON_GAP
                lpos.append((wx, wy))
            positions.append(lpos)
        return positions

    # ── fonts (lazy) ──────────────────────────────────────────────────────────

    def _ensure_fonts(self):
        if self._font_body is not None:
            return
        try:
            self._font_heading = pygame.font.SysFont("consolas", 22, bold=True)
            self._font_body    = pygame.font.SysFont("consolas", 18)
            self._font_tiny    = pygame.font.SysFont("consolas", 14)
        except Exception:
            self._font_heading = pygame.font.Font(None, 26)
            self._font_body    = pygame.font.Font(None, 22)
            self._font_tiny    = pygame.font.Font(None, 17)
    # ── helpers ───────────────────────────────────────────────────────────────

    def _ws(self, wx, wy):
        """World → screen."""
        return self._cam.world_to_screen(wx, wy, self.width, self.height)

    def _sw(self, sx, sy):
        """Screen → world."""
        return self._cam.screen_to_world(sx, sy, self.width, self.height)

    def _neuron_activation(self, layer_idx, neuron_idx):
        """Return the output activation for nn.layers[layer_idx] neuron neuron_idx."""
        layer = self.nn.layers[layer_idx]
        if layer.output is not None:
            out = np.asarray(layer.output).flatten()
            if neuron_idx < len(out):
                return float(out[neuron_idx])
        return 0.0

    def _hit_neuron(self, sx, sy):
        """Return (layer_idx, neuron_idx) under screen pos, or None."""
        wx, wy = self._sw(sx, sy)
        r2 = (self.NEURON_R * 1.2) ** 2
        for li, lpos in enumerate(self._positions):
            for ni, (px, py) in enumerate(lpos):
                if (wx - px) ** 2 + (wy - py) ** 2 < r2:
                    return (li, ni)
        return None

    # ── event handling ────────────────────────────────────────────────────────

    def _local_pos(self, screen_pos):
        """Convert a window-space position to surface-local coordinates."""
        return (screen_pos[0] - self.offset[0], screen_pos[1] - self.offset[1])

    def handle_event(self, event,mp):
        cam = self._cam
        sw, sh = self.width, self.height

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self._local_pos(mp)
            if not pygame.Rect(0,0,self.width,self.height).collidepoint(pos):
                return
            pos = self._local_pos(mp)
            if event.button == 1:
                # Check detail-panel close button first
                if self._panel.visible and self._panel.hit_close(pos):
                    self._panel.hide()
                    return
                hit = self._hit_neuron(*pos)
                if hit:
                    li, ni = hit
                    wx, wy = self._positions[li][ni]
                    cam.focus_on(wx, wy, target_zoom=max(cam.tzoom, 2.0))
                    self._panel.show(self.nn, li, ni)
                else:
                    self._panning   = True
                    self._pan_start = pos
            elif event.button == 3:
                self._panel.hide()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._panning = False

        elif event.type == pygame.MOUSEMOTION:
            pos = self._local_pos(mp)
            if self._panning:
                dx = pos[0] - self._pan_start[0]
                dy = pos[1] - self._pan_start[1]
                cam.pan(dx, dy)
                self._pan_start = pos
            self._hovered = self._hit_neuron(*pos)

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = self._local_pos(mp)
            if self._panel.visible:
                pass  # panel has no scroll; wheel zooms as normal
            factor = 1.12 if event.y > 0 else 1 / 1.12
            cam.zoom_at(mx, my, sw, sh, factor)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._panel.hide()
            elif event.key == pygame.K_r:
                cam.tx, cam.ty, cam.tzoom = 0, 0, 1.0

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        self._ensure_fonts()

        now = pygame.time.get_ticks()
        dt  = (now - self._last_ms) / 1000.0
        self._last_ms = now
        self._cam.update(dt)

        surf = self.surface
        surf.fill(_BG)

        self._draw_connections(surf)
        self._draw_neurons(surf)
        self._draw_layer_labels(surf)
        self._draw_hud(surf)
        self._panel.draw(surf, (self._font_heading, self._font_body, self._font_tiny))

    # ── connections ───────────────────────────────────────────────────────────

    def _draw_connections(self, surf):
        cam   = self._cam
        nn    = self.nn
        zoom  = cam.zoom
        min_alpha = 15 if zoom > 0.4 else 0

        conn_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        for li, layer in enumerate(nn.layers):
            dst_positions = self._positions[li]
            # skip connections from the (removed) input layer
            if li == 0:
                continue
            src_positions = self._positions[li - 1]

            for ni, (sx, sy) in enumerate(src_positions):
                ssx, ssy = self._ws(sx, sy)
                for nj, (dx, dy) in enumerate(dst_positions):
                    if ni >= layer.W.shape[1] or nj >= layer.W.shape[0]:
                        continue
                    w = float(layer.W[nj, ni])
                    col   = _weight_colour(w)
                    alpha = _weight_alpha(w)
                    if alpha < min_alpha:
                        continue
                    sdx, sdy = self._ws(dx, dy)
                    lw = max(1, int(zoom * 1.5))
                    pygame.draw.line(conn_surf, (*col, alpha),
                                     (int(ssx), int(ssy)),
                                     (int(sdx), int(sdy)), lw)

        surf.blit(conn_surf, (0, 0))

    # ── neurons ───────────────────────────────────────────────────────────────

    def _draw_neurons(self, surf):
        cam  = self._cam
        zoom = cam.zoom
        r    = max(4, int(self.NEURON_R * zoom))
        font = self._font_tiny

        for li, lpos in enumerate(self._positions):
            for ni, (wx, wy) in enumerate(lpos):
                sx, sy = self._ws(wx, wy)
                act    = self._neuron_activation(li, ni)
                col    = _neuron_colour(act)

                is_hovered  = self._hovered == (li, ni)
                is_selected = (self._panel.visible and
                               self._panel.layer_idx == li and
                               self._panel.neuron_idx == ni)

                if is_hovered or is_selected:
                    pygame.draw.circle(surf, (255, 255, 180), (int(sx), int(sy)), r + 5)

                pygame.draw.circle(surf, col,            (int(sx), int(sy)), r)
                pygame.draw.circle(surf, (200, 200, 255), (int(sx), int(sy)), r, max(1, r // 6))

                if zoom > 0.7:
                    lbl = font.render(f"{act:+.2f}", True, _TEXT_DIM)
                    surf.blit(lbl, (int(sx) - lbl.get_width() // 2,
                                    int(sy) + r + 2))

    # ── layer labels ──────────────────────────────────────────────────────────

    def _draw_layer_labels(self, surf):
        font  = self._font_body
        nn    = self.nn
        for li, lpos in enumerate(self._positions):
            if not lpos:
                continue
            wx, top_wy = lpos[0]
            sx, sy = self._ws(wx, top_wy - self.NEURON_R - 22)
            n_shown = len(lpos)
            n_total = nn.layer_sizes[li + 1]
            is_out  = (li == len(self._positions) - 1)
            label   = f"{'Output' if is_out else f'Layer {li + 1}'}  [{n_total}{'…' if n_total > n_shown else ''}]"
            lbl = font.render(label, True, _TEXT_ACCENT)
            surf.blit(lbl, (int(sx) - lbl.get_width() // 2, int(sy)))

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, surf):
        font = self._font_tiny
        lines = [
            "Drag: pan   Scroll: zoom",
            "Click neuron: inspect   R: reset view   RMB / ESC: close panel",
        ]
        y = self.height - len(lines) * 14 - 6
        for line in lines:
            lbl = font.render(line, True, _TEXT_DIM)
            surf.blit(lbl, (8, y))
            y += 14

