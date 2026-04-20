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
from neural_network import NeuralNetwork
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
# Detail panel
# ──────────────────────────────────────────────────────────────────────────────

class _DetailPanel:
    W = 300
    PAD = 14

    def __init__(self):
        self.visible  = False
        self.layer_idx   = 0
        self.neuron_idx  = 0
        self.nn       = None
        self._scroll  = 0
        self._font_h  = None
        self._font_b  = None

    def show(self, nn, layer_idx, neuron_idx):
        self.nn         = nn
        self.layer_idx  = layer_idx
        self.neuron_idx = neuron_idx
        self.visible    = True
        self._scroll    = 0

    def hide(self):
        self.visible = False

    def scroll(self, dy):
        self._scroll = max(0, self._scroll - dy * 20)

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface, fonts):
        if not self.visible or self.nn is None:
            return

        fh, fb = fonts                   # heading, body
        sw, sh  = surface.get_size()
        x0      = sw - self.W - 10
        y0      = 10
        H       = sh - 20

        # Panel background
        panel_surf = pygame.Surface((self.W, H), pygame.SRCALPHA)
        panel_surf.fill((*_PANEL_BG, 230))
        pygame.draw.rect(panel_surf, _PANEL_BORDER, (0, 0, self.W, H), 2, border_radius=8)
        surface.blit(panel_surf, (x0, y0))

        layer  = self.nn.layers[self.layer_idx]
        ni     = self.neuron_idx
        P      = self.PAD
        cx     = x0 + P
        cy     = y0 + P - self._scroll

        def write(text, colour=_TEXT_MAIN, bold=False, indent=0):
            nonlocal cy
            font   = fb
            rendered = font.render(text, True, colour)
            surface.blit(rendered, (cx + indent, cy))
            cy += rendered.get_height() + 3

        def divider():
            nonlocal cy
            pygame.draw.line(surface, _PANEL_BORDER,
                             (x0 + P, cy + 2), (x0 + self.W - P, cy + 2))
            cy += 10

        # Clip drawing to panel
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(x0, y0, self.W, H))

        # ── Header ────────────────────────────────────────────────────────────
        title = fh.render(f"Layer {self.layer_idx + 1}  Neuron {ni}", True, _TEXT_ACCENT)
        surface.blit(title, (cx, cy))
        cy += title.get_height() + 6
        divider()

        act_fn = layer.activation.upper()
        write(f"Activation fn : {act_fn}", _TEXT_ACCENT)
        divider()

        # ── Input vector ──────────────────────────────────────────────────────
        write("Input (x)", _TEXT_DIM)
        if layer.input is not None:
            inp = np.asarray(layer.input).flatten()
            for j, v in enumerate(inp):
                write(f"  x[{j}] = {v:+.4f}", _TEXT_MAIN, indent=4)
        else:
            write("  (no forward pass yet)", _TEXT_DIM)
        divider()

        # ── Weights for this neuron ────────────────────────────────────────────
        write("Weights W[neuron, :]", _TEXT_DIM)
        w_row = layer.W[ni]
        for j, w in enumerate(w_row):
            col = _lerp_colour((200, 80, 80), (80, 200, 180), (w + 2) / 4)
            write(f"  W[{ni},{j}] = {w:+.4f}", col, indent=4)
        divider()

        # ── Bias ──────────────────────────────────────────────────────────────
        bias = layer.b[ni]
        write("Bias", _TEXT_DIM)
        write(f"  b[{ni}] = {bias:+.4f}", _TEXT_MAIN, indent=4)
        divider()

        # ── Pre-activation ────────────────────────────────────────────────────
        write("Pre-activation  z = W·x + b", _TEXT_DIM)
        if layer.input is not None:
            inp = np.asarray(layer.input).flatten()
            z = float(layer.W[ni] @ inp + layer.b[ni])
            write(f"  z = {z:+.4f}", _TEXT_MAIN, indent=4)
        else:
            write("  (no forward pass yet)", _TEXT_DIM)
        divider()

        # ── Output / activation value ──────────────────────────────────────────
        write("Output  a = f(z)", _TEXT_DIM)
        if layer.output is not None:
            out = np.asarray(layer.output).flatten()
            a = float(out[ni]) if ni < len(out) else float("nan")
            write(f"  a[{ni}] = {a:+.4f}", _TEXT_ACCENT, indent=4)
        else:
            write("  (no forward pass yet)", _TEXT_DIM)

        # Close button  ×
        close_r = pygame.Rect(x0 + self.W - 28, y0 + 6, 22, 22)
        pygame.draw.circle(surface, (180, 60, 60), close_r.center, 11)
        lbl = fb.render("×", True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=close_r.center))

        surface.set_clip(old_clip)
        self._close_rect = close_r

    def hit_close(self, pos):
        return hasattr(self, "_close_rect") and self._close_rect.collidepoint(pos)


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
        """Return list of lists of (wx, wy) world positions for every neuron."""
        nn = self.nn
        n_layers = len(nn.layers) + 1          # input layer + hidden/output layers

        # layer widths
        sizes = [nn.layer_sizes[0]] + [nn.layer_sizes[i + 1]
                                        for i in range(len(nn.layers))]

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
            self._font_heading = pygame.font.SysFont("consolas", 15, bold=True)
            self._font_body    = pygame.font.SysFont("consolas", 13)
            self._font_tiny    = pygame.font.SysFont("consolas", 10)
        except Exception:
            self._font_heading = pygame.font.Font(None, 18)
            self._font_body    = pygame.font.Font(None, 15)
            self._font_tiny    = pygame.font.Font(None, 12)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _ws(self, wx, wy):
        """World → screen."""
        return self._cam.world_to_screen(wx, wy, self.width, self.height)

    def _sw(self, sx, sy):
        """Screen → world."""
        return self._cam.screen_to_world(sx, sy, self.width, self.height)

    def _neuron_activation(self, layer_idx, neuron_idx):
        """Return the activation value (float) for a neuron, or 0 if no pass."""
        nn = self.nn
        if layer_idx == 0:
            # input layer – show raw input if available
            if nn.layers[0].input is not None:
                inp = np.asarray(nn.layers[0].input).flatten()
                if neuron_idx < len(inp):
                    return float(inp[neuron_idx])
            return 0.0
        else:
            layer = nn.layers[layer_idx - 1]
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

    def handle_event(self, event):
        cam = self._cam
        sw, sh = self.width, self.height
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self._local_pos(event.pos)
            if not pygame.Rect(0,0,self.width,self.height).collidepoint(pos):
                return
            if event.button == 1:
                # Check detail-panel close button first
                if self._panel.visible and self._panel.hit_close(pos):
                    self._panel.hide()
                    return
                hit = self._hit_neuron(*pos)
                if hit:
                    li, ni = hit
                    # zoom camera to neuron
                    wx, wy = self._positions[li][ni]
                    cam.focus_on(wx, wy, target_zoom=max(cam.tzoom, 2.0))
                    # show detail panel
                    if li == 0:
                        # input layer has no Layer object; use first real layer as proxy
                        self._panel.show(self.nn, 0, ni)
                    else:
                        self._panel.show(self.nn, li - 1, ni)
                else:
                    self._panning   = True
                    self._pan_start = pos
            elif event.button == 3:
                self._panel.hide()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._panning = False

        elif event.type == pygame.MOUSEMOTION:
            pos = self._local_pos(event.pos)
            if self._panning:
                dx = pos[0] - self._pan_start[0]
                dy = pos[1] - self._pan_start[1]
                cam.pan(dx, dy)
                self._pan_start = pos
            self._hovered = self._hit_neuron(*pos)

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = self._local_pos(pygame.mouse.get_pos())
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
        self._panel.draw(surf, (self._font_heading, self._font_body))

    # ── connections ───────────────────────────────────────────────────────────

    def _draw_connections(self, surf):
        cam   = self._cam
        nn    = self.nn
        zoom  = cam.zoom
        # Only draw connections when zoom is sufficient (performance)
        min_alpha = 15 if zoom > 0.4 else 0

        conn_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        for li, layer in enumerate(nn.layers):
            src_positions = self._positions[li]       # input side
            dst_positions = self._positions[li + 1]   # output side

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

                # Glow ring for hovered / selected
                is_hovered = self._hovered == (li, ni)
                is_selected = (self._panel.visible and
                               self._panel.layer_idx == (li - 1) and
                               self._panel.neuron_idx == ni)

                if is_hovered or is_selected:
                    pygame.draw.circle(surf, (255, 255, 180), (int(sx), int(sy)), r + 5)

                pygame.draw.circle(surf, col,          (int(sx), int(sy)), r)
                pygame.draw.circle(surf, (200, 200, 255), (int(sx), int(sy)), r, max(1, r // 6))

                # Value label (only when zoom > 0.7)
                if zoom > 0.7:
                    lbl = font.render(f"{act:+.2f}", True, _TEXT_DIM)
                    surf.blit(lbl, (int(sx) - lbl.get_width() // 2,
                                    int(sy) + r + 2))

    # ── layer labels ──────────────────────────────────────────────────────────

    def _draw_layer_labels(self, surf):
        font  = self._font_body
        sizes = [self.nn.layer_sizes[i] for i in range(len(self.nn.layer_sizes))]
        names = ["Input"] + [
            f"Layer {i}" + (" (out)" if i == len(self.nn.layers) else "")
            for i in range(1, len(self.nn.layer_sizes))
        ]
        n_layers = len(self._positions)
        for li, lpos in enumerate(self._positions):
            if not lpos:
                continue
            wx, _ = lpos[0]
            # put label above the topmost neuron
            _, top_wy = lpos[0]
            sx, sy = self._ws(wx, top_wy - self.NEURON_R - 22)
            n_shown = len(lpos)
            n_total = sizes[li]
            clipped = " …" if n_total > n_shown else ""
            lbl_txt = f"{names[li]}  [{n_total}{clipped}]"
            lbl = font.render(lbl_txt, True, _TEXT_ACCENT)
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


# ──────────────────────────────────────────────────────────────────────────────
# Standalone demo  (python nn_visualizer.py)
# ──────────────────────────────────────────────────────────────────────────────
#
# if __name__ == "__main__":
#
#
#     pygame.init()
#     W, H   = 1280, 720
#     screen = pygame.display.set_mode((W, H))
#     pygame.display.set_caption("Neural Network Visualizer")
#     clock  = pygame.time.Clock()
#
#     nn = NeuralNetwork([4, 6, 6, 3])
#     # Run a few random forward passes so neurons have activation values
#     rng = np.random.default_rng(0)
#     for _ in range(5):
#         nn.forward(rng.standard_normal(4).tolist())
#     w,h=700,500
#     x,y=100,100
#     vis = NeuralNetworkVisualizer(nn, width=w, height=h,offset=(x,y))
#
#     running = True
#     while running:
#         screen.fill(0)
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False
#             vis.handle_event(event)
#
#         vis.draw()
#         screen.blit(vis.surface, (x, y))
#         pygame.display.flip()
#         clock.tick(60)
#
#     pygame.quit()