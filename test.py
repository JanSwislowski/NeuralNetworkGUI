import pygame
import time
import math

# ─────────────────────────────────────────────
#  Palette
# ─────────────────────────────────────────────
C_BG          = (15,  17,  26)
C_PANEL       = (28,  32,  48)
C_PANEL_HOVER = (36,  41,  62)
C_BORDER      = (55,  65, 100)
C_BORDER_OPEN = (64, 190, 255)
C_ACCENT      = (64, 190, 255)
C_TEXT        = (220, 228, 255)
C_TEXT_DIM    = (110, 125, 165)
C_ITEM_HOVER  = (38,  68, 110)
C_ITEM_SEL    = (30,  80, 130)
C_ARROW       = (120, 145, 200)
C_SHADOW      = (  0,   0,   0)

# ─────────────────────────────────────────────
#  Easing helpers
# ─────────────────────────────────────────────
def ease_out_expo(t: float) -> float:
    return 1.0 if t >= 1.0 else 1 - 2 ** (-10 * t)

def ease_in_expo(t: float) -> float:
    return 0.0 if t <= 0.0 else 2 ** (10 * t - 10)

def ease_out_back(t: float, s: float = 1.4) -> float:
    c1 = s
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# ─────────────────────────────────────────────
#  Picker
# ─────────────────────────────────────────────
class Picker:
    """
    A drop-down picker widget for Pygame.

    Usage
    -----
    picker = Picker(x=50, y=50, width=260, options=["Cat","Dog","Fish"],
                    font=font, placeholder="Select…")

    # in event loop:
    picker.handle_event(event)

    # in draw loop:
    screen.blit(picker.draw(), picker.surface_offset())

    # read selected value:
    value = picker.selected   # None or string
    """

    HEADER_H   = 44          # height of the closed header
    ITEM_H     = 38          # height of each dropdown item
    ANIM_OPEN  = 0.28        # seconds to open
    ANIM_CLOSE = 0.18        # seconds to close
    RADIUS     = 10          # corner radius
    MAX_ITEMS_VISIBLE = 6    # scroll after this many

    def __init__(self,
                 x: int, y: int,
                 width: int,
                 options: list[str],
                 font: pygame.font.Font,
                 font_small: pygame.font.Font | None = None,
                 placeholder: str = "Select an option…",
                 selected: str | None = None):

        self.x = x
        self.y = y
        self.width    = width
        self.options  = options
        self.font     = font
        self.font_sm  = font_small or font
        self.placeholder = placeholder
        self.selected    = selected

        # animation state
        self._open       = False
        self._anim_t     = 0.0        # 0=closed, 1=open
        self._anim_dir   = 0          # +1 opening, -1 closing
        self._last_time  = time.time()

        # hover / interaction
        self._hover_header = False
        self._hover_item   = -1       # index of hovered item
        self._scroll       = 0        # first visible item index

        # ripple on selection
        self._ripple_alpha = 0.0
        self._ripple_item  = -1

        # arrow bob phase
        self._arrow_phase  = 0.0

        # surface – tall enough for header + all items
        visible_items = min(len(options), self.MAX_ITEMS_VISIBLE)
        self._surf_h  = self.HEADER_H + visible_items * self.ITEM_H + 8
        self._surface = pygame.Surface((width, self._surf_h), pygame.SRCALPHA)

    # ── public helpers ────────────────────────────────────────────────────────

    def surface_offset(self):
        """Return (x, y) where to blit the surface on the parent surface."""
        return (self.x, self.y)

    def total_height(self):
        """Current rendered height (useful for layout)."""
        return self.HEADER_H + self._dropdown_h()

    def set_options(self, options: list[str], keep_selected: bool = True):
        old = self.selected
        self.options = options
        if not keep_selected or old not in options:
            self.selected = None
        visible_items = min(len(options), self.MAX_ITEMS_VISIBLE)
        self._surf_h  = self.HEADER_H + visible_items * self.ITEM_H + 8
        self._surface = pygame.Surface((self.width, self._surf_h), pygame.SRCALPHA)
        self._scroll  = 0

    # ── event handling ────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Returns True if the event was consumed by this widget.
        Pass absolute mouse coordinates; widget adjusts internally.
        """
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos[0] - self.x, event.pos[1] - self.y
            self._hover_header = (0 <= mx < self.width and
                                   0 <= my < self.HEADER_H)
            if self._open or self._anim_t > 0:
                self._hover_item = self._item_at(mx, my)
            else:
                self._hover_item = -1
            return self._hover_header or self._hover_item >= 0

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos[0] - self.x, event.pos[1] - self.y
            if 0 <= mx < self.width and 0 <= my < self.HEADER_H:
                self._toggle()
                return True
            idx = self._item_at(mx, my)
            if idx >= 0:
                self._select(idx)
                return True
            # click outside – close
            if self._open:
                self._close()
                return True

        elif event.type == pygame.MOUSEWHEEL:
            if self._open:
                mx, my = pygame.mouse.get_pos()
                mx -= self.x; my -= self.y
                if (0 <= mx < self.width and
                        self.HEADER_H <= my < self._surf_h):
                    max_scroll = max(0, len(self.options) - self.MAX_ITEMS_VISIBLE)
                    self._scroll = max(0, min(max_scroll,
                                              self._scroll - event.y))
                    return True

        elif event.type == pygame.KEYDOWN and self._open:
            if event.key == pygame.K_ESCAPE:
                self._close(); return True
            elif event.key == pygame.K_UP:
                self._hover_item = max(0, self._hover_item - 1)
                self._ensure_visible(self._hover_item); return True
            elif event.key == pygame.K_DOWN:
                self._hover_item = min(len(self.options)-1,
                                       self._hover_item + 1)
                self._ensure_visible(self._hover_item); return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if 0 <= self._hover_item < len(self.options):
                    self._select(self._hover_item); return True

        return False

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self) -> pygame.Surface:
        now = time.time()
        dt  = min(now - self._last_time, 0.1)
        self._last_time = now
        self._update_anim(dt)

        surf = self._surface
        surf.fill((0, 0, 0, 0))

        t   = self._anim_t              # 0=closed … 1=open
        dh  = self._dropdown_h()        # current pixel height of dropdown

        # ── shadow when open ──────────────────────────────────────────
        if t > 0.01:
            shadow_alpha = int(120 * t)
            for i in range(8):
                s = pygame.Surface((self.width + i*4, self.HEADER_H + dh + i*4),
                                    pygame.SRCALPHA)
                a = max(0, shadow_alpha - i * 18)
                s.fill((0, 0, 0, a))
                surf.blit(s, (-i*2, i*2))

        # ── dropdown panel (drawn first so header sits on top) ────────
        if t > 0.01 and dh > 2:
            dp_rect = pygame.Rect(0, self.HEADER_H - self.RADIUS,
                                  self.width, dh + self.RADIUS)
            self._draw_dropdown(surf, dp_rect, t)

        # ── header ────────────────────────────────────────────────────
        self._draw_header(surf, t)

        return surf

    # ── private drawing helpers ───────────────────────────────────────────────

    def _draw_header(self, surf, t):
        w, h = self.width, self.HEADER_H
        is_open = t > 0.01

        # border color pulse
        border_col = lerp_color(C_BORDER, C_BORDER_OPEN, t)

        # header bg
        bg_col = lerp_color(C_PANEL,
                             C_PANEL_HOVER if self._hover_header else C_PANEL,
                             0.5 if self._hover_header else 0)
        if is_open:
            # flat bottom when open
            pygame.draw.rect(surf, bg_col,
                             (0, 0, w, h + self.RADIUS))
            pygame.draw.rect(surf, bg_col,
                             (0, 0, w, h), border_radius=self.RADIUS)
            # redraw bottom square
            pygame.draw.rect(surf, bg_col,
                             (0, h - self.RADIUS, w, self.RADIUS))
        else:
            pygame.draw.rect(surf, bg_col,
                             (0, 0, w, h), border_radius=self.RADIUS)

        # border
        border_thick = 2 if is_open else 1
        if is_open:
            pygame.draw.rect(surf, border_col,
                             (0, 0, w, h), width=border_thick,
                             border_top_left_radius=self.RADIUS,
                             border_top_right_radius=self.RADIUS,
                             border_bottom_left_radius=0,
                             border_bottom_right_radius=0)
            # side borders continue down
            pygame.draw.line(surf, border_col, (0, 0), (0, h))
            pygame.draw.line(surf, border_col, (w-1, 0), (w-1, h))
        else:
            pygame.draw.rect(surf, border_col,
                             (0, 0, w, h), width=border_thick,
                             border_radius=self.RADIUS)

        # accent line at top when open
        if t > 0.01:
            line_w = int(w * t)
            lx = (w - line_w) // 2
            pygame.draw.rect(surf, C_ACCENT, (lx, 0, line_w, 2),
                             border_radius=1)

        # label text
        label  = self.selected or self.placeholder
        color  = C_TEXT if self.selected else C_TEXT_DIM
        txt    = self.font.render(label, True, color)
        ty     = (h - txt.get_height()) // 2
        # clip text to avoid overlapping arrow
        clip   = pygame.Rect(14, 0, w - 48, h)
        surf.set_clip(clip)
        surf.blit(txt, (14, ty))
        surf.set_clip(None)

        # arrow
        self._draw_arrow(surf, w - 30, h // 2, t)

    def _draw_arrow(self, surf, cx, cy, t):
        # rotate from 0° (point down) to 180° (point up) as t goes 0→1
        # add subtle bob animation
        bob    = math.sin(self._arrow_phase) * 1.5
        angle  = math.pi * t          # 0 → π
        size   = 7
        # three points of a chevron
        pts = []
        for dx, dy in [(-size, -size*0.5), (0, size*0.5), (size, -size*0.5)]:
            rx = dx * math.cos(angle) - dy * math.sin(angle)
            ry = dx * math.sin(angle) + dy * math.cos(angle)
            pts.append((cx + rx, cy + ry + bob))
        col = lerp_color(C_ARROW, C_ACCENT, t)
        pygame.draw.lines(surf, col, False, pts, 2)

    def _draw_dropdown(self, surf, rect, t):
        w = self.width
        clip_h = int(self._max_dropdown_h() * ease_out_back(t, s=1.2))
        clip_h = min(clip_h, self._max_dropdown_h())

        # clip so items appear to slide in
        clip_rect = pygame.Rect(0, self.HEADER_H, w, clip_h)
        surf.set_clip(clip_rect)

        # background
        dp_rect = pygame.Rect(0, self.HEADER_H, w,
                              self._max_dropdown_h())
        pygame.draw.rect(surf, C_PANEL, dp_rect,
                         border_bottom_left_radius=self.RADIUS,
                         border_bottom_right_radius=self.RADIUS)

        # items
        visible = min(len(self.options), self.MAX_ITEMS_VISIBLE)
        for i in range(visible):
            idx  = i + self._scroll
            if idx >= len(self.options): break
            iy   = self.HEADER_H + i * self.ITEM_H + 4
            item_rect = pygame.Rect(4, iy, w - 8, self.ITEM_H - 2)

            # staggered fade-in
            item_delay = i * 0.035
            item_t     = max(0.0, min(1.0, (t - item_delay) / 0.25))
            item_alpha = int(255 * ease_out_expo(item_t))

            # bg highlight
            is_sel   = self.options[idx] == self.selected
            is_hover = self._hover_item == idx

            if is_sel:
                bg = lerp_color(C_ITEM_SEL, C_ITEM_HOVER, 0.3 if is_hover else 0)
                pygame.draw.rect(surf, bg, item_rect, border_radius=6)
            elif is_hover:
                pygame.draw.rect(surf, C_ITEM_HOVER, item_rect, border_radius=6)

            # ripple
            if self._ripple_item == idx and self._ripple_alpha > 0:
                rip_surf = pygame.Surface((item_rect.width, item_rect.height),
                                           pygame.SRCALPHA)
                rip_surf.fill((*C_ACCENT, int(self._ripple_alpha * 80)))
                surf.blit(rip_surf, item_rect.topleft)

            # text
            label   = self.options[idx]
            txt_col = lerp_color(C_TEXT_DIM, C_TEXT, item_t)
            if is_sel:
                txt_col = C_ACCENT
            txt     = self.font.render(label, True, txt_col)
            # slide in from left
            slide   = int((1 - ease_out_expo(item_t)) * 18)
            tx      = item_rect.x + 12 + slide
            ty      = item_rect.y + (item_rect.height - txt.get_height()) // 2

            txt_s = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            txt_s.blit(txt, (0, 0))
            txt_s.set_alpha(item_alpha)
            surf.blit(txt_s, (tx, ty))

            # checkmark for selected
            if is_sel:
                self._draw_check(surf,
                                  item_rect.right - 22,
                                  item_rect.centery,
                                  item_alpha)

        # scrollbar
        if len(self.options) > self.MAX_ITEMS_VISIBLE:
            self._draw_scrollbar(surf, clip_h)

        # border
        pygame.draw.rect(surf, lerp_color(C_BORDER, C_BORDER_OPEN, t),
                         pygame.Rect(0, self.HEADER_H - 1, w,
                                     self._max_dropdown_h() + 1),
                         width=1,
                         border_bottom_left_radius=self.RADIUS,
                         border_bottom_right_radius=self.RADIUS)
        # hide top border (header draws its own)
        pygame.draw.line(surf, C_PANEL,
                         (1, self.HEADER_H), (w - 2, self.HEADER_H))

        surf.set_clip(None)

    def _draw_check(self, surf, cx, cy, alpha):
        pts = [(cx - 6, cy), (cx - 2, cy + 4), (cx + 6, cy - 5)]
        s = pygame.Surface((20, 16), pygame.SRCALPHA)
        pygame.draw.lines(s, (*C_ACCENT, alpha), False,
                          [(p[0]-cx+10, p[1]-cy+8) for p in pts], 2)
        surf.blit(s, (cx - 10, cy - 8))

    def _draw_scrollbar(self, surf, visible_h):
        total   = len(self.options)
        vis     = self.MAX_ITEMS_VISIBLE
        ratio   = vis / total
        bar_h   = max(20, int(visible_h * ratio))
        track_h = visible_h
        pos_t   = self._scroll / max(1, total - vis)
        bar_y   = self.HEADER_H + int((track_h - bar_h) * pos_t)
        sb_rect = pygame.Rect(self.width - 5, bar_y, 3, bar_h)
        pygame.draw.rect(surf, C_BORDER_OPEN, sb_rect, border_radius=2)

    # ── private logic helpers ─────────────────────────────────────────────────

    def _toggle(self):
        if self._open:
            self._close()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        self._open    = True
        self._anim_dir = 1
        self._hover_item = -1

    def _close(self):
        self._open    = False
        self._anim_dir = -1
        self._hover_item = -1

    def _select(self, idx: int):
        self.selected       = self.options[idx]
        self._ripple_item   = idx
        self._ripple_alpha  = 1.0
        self._close()

    def _item_at(self, mx, my) -> int:
        """Return option index at local coords (mx,my), or -1."""
        if not (0 <= mx < self.width): return -1
        rel = my - self.HEADER_H - 4
        if rel < 0: return -1
        i = int(rel // self.ITEM_H)
        if 0 <= i < self.MAX_ITEMS_VISIBLE:
            idx = i + self._scroll
            if 0 <= idx < len(self.options):
                return idx
        return -1

    def _ensure_visible(self, idx: int):
        if idx < self._scroll:
            self._scroll = idx
        elif idx >= self._scroll + self.MAX_ITEMS_VISIBLE:
            self._scroll = idx - self.MAX_ITEMS_VISIBLE + 1

    def _update_anim(self, dt: float):
        speed = 1.0 / (self.ANIM_OPEN if self._anim_dir >= 0 else self.ANIM_CLOSE)
        self._anim_t = max(0.0, min(1.0,
                           self._anim_t + self._anim_dir * speed * dt))
        # bob
        self._arrow_phase += dt * 2.5

        # ripple decay
        if self._ripple_alpha > 0:
            self._ripple_alpha = max(0.0, self._ripple_alpha - dt * 3.0)

    def _max_dropdown_h(self) -> int:
        return min(len(self.options), self.MAX_ITEMS_VISIBLE) * self.ITEM_H + 8

    def _dropdown_h(self) -> int:
        t = self._anim_t
        if t <= 0: return 0
        return int(self._max_dropdown_h() * ease_out_back(t, s=1.2))


# ─────────────────────────────────────────────
#  Demo
# ─────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((620, 500))
    pygame.display.set_caption("Picker – demo")
    clock  = pygame.time.Clock()

    try:
        font    = pygame.font.SysFont("dejavusans", 16)
        font_sm = pygame.font.SysFont("dejavusans", 13)
    except Exception:
        font = font_sm = pygame.font.Font(None, 20)

    animals = ["🐱 Cat", "🐶 Dog", "🐟 Fish", "🐦 Bird",
               "🐢 Turtle", "🐹 Hamster", "🦎 Lizard",
               "🐠 Clownfish", "🐇 Rabbit", "🦜 Parrot"]

    colors  = ["Red", "Green", "Blue", "Yellow",
               "Orange", "Purple", "Pink", "Cyan"]

    picker1 = Picker(x=60,  y=80,  width=240, options=animals,
                     font=font, placeholder="Choose animal…")
    picker2 = Picker(x=330, y=80,  width=240, options=colors,
                     font=font, placeholder="Choose colour…",
                     selected="Blue")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            # handle pickers in reverse order so top one gets priority
            if not picker1.handle_event(event):
                picker2.handle_event(event)

        # ── render ────────────────────────────────
        screen.fill(C_BG)

        # title
        title = font.render("Picker widget demo  –  click to open", True,
                             (100, 120, 170))
        screen.blit(title, (60, 40))

        # status
        v1 = picker1.selected or "—"
        v2 = picker2.selected or "—"
        status = font.render(f"Selected:  animal={v1}   colour={v2}",
                              True, (80, 200, 140))
        screen.blit(status, (60, 420))

        # draw pickers – order matters for overlap!
        # draw the inactive one first so the active dropdown overlaps it
        if picker1._open or picker1._anim_t > 0:
            screen.blit(picker2.draw(), picker2.surface_offset())
            screen.blit(picker1.draw(), picker1.surface_offset())
        else:
            screen.blit(picker1.draw(), picker1.surface_offset())
            screen.blit(picker2.draw(), picker2.surface_offset())

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()