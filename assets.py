import pygame
import time
import math
from functions import image_to_list,scale_rect

pygame.init()
font = pygame.font.SysFont("dejavusans", 16)
font_sm = pygame.font.SysFont("dejavusans", 13)
font_big = pygame.font.SysFont("dejavusans", 22, bold=True)
font_verybig = pygame.font.SysFont("dejavusans", 50, bold=True)
class Label:
    def __init__(self,pos,text,font:pygame.font.Font,color,border=-1,function=None,border_color=None,padding=5,pos_type=0):
        self.padding=padding
        self.txt=font.render(text,False,color)
        self.rect=self.txt.get_rect()
        if pos_type==0:
            self.rect.topleft=(pos[0]-self.txt.get_width()//2-padding,pos[1])
        else:
            self.rect.topleft=(pos[0]-padding,pos[1])

        self.rect.w+=padding*2
        self.border=border
        self.bc=border_color
        self.function=function
    def draw(self,screen):
        if self.border!=-1:
            pygame.draw.rect(screen,self.bc,self.rect,self.border,border_radius=5)
        screen.blit(self.txt,(self.rect.x+self.padding,self.rect.y))
    def get_width(self):
        return self.rect.w
    def get_height(self):
        return self.rect.h
    def update(self):
        if not self.function:
            return
        if pygame.mouse.get_pressed()[0]:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.function()

class Label_list:
    def __init__(self,x,y,max_width,font:pygame.font.Font,texts,color,label=None,label_font=None):
        self.x=x
        self.y=y
        self.w=max_width
        self.font=font
        self.generate_labels(texts,color)
    def generate_labels(self,texts,color):
        self.labels=[]
        self.helpers=[]
        x=self.x
        y=self.y
        self.helpers.append(Label((x,y),"[",self.font,color,pos_type=1,padding=0))
        x+=self.helpers[-1].get_width()
        for i in texts[:-1]:
            self.labels.append(Label((x,y),str(i),self.font,color,pos_type=1,padding=0))
            x+=self.labels[-1].get_width()
            self.helpers.append(Label((x,y),", ",self.font,color,pos_type=1,padding=0))
            x+=self.helpers[-1].get_width()
            if x-self.x>=self.w:
                x=self.x
                y+=self.labels[-1].get_height()
        x-=self.helpers[-1].get_width()
        self.helpers.pop()
        self.helpers.append(Label((x,y),"]",self.font,color,pos_type=1))
    def draw(self,screen):
        for i ,j in zip(self.helpers,self.labels):
            i.draw(screen),j.draw(screen)
    def update(self):
        for i ,j in zip(self.helpers,self.labels):
            i.update(),j.update()


class InputBoard:
    def __init__(self,width,heigt,rows,cols,offset=(0,0),padding=7,image=None):
        self.width=width
        self.height=heigt
        self.rows=rows
        self.cols=cols
        self.tile_w=self.width//self.cols
        self.tile_h=self.height//self.rows

        self.color=False
        if image:
            self.color=True
            self.tiles=image_to_list(rows,cols,image)
        else: self.tiles=[0 for i in range(self.rows*self.cols)]

        print(self.tiles)
        self.surface=pygame.Surface((self.width+padding*2,self.height+padding*2))

        self.padding=padding
        self.offset=offset

        self.list=Label_list(300,600,600,font_verybig,self.tiles,(255,255,255))
    def draw_white(self,i,j):
        rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
        if self.tiles[i*self.rows+j]:
            color=[int(self.tiles[i*self.rows+j]*255)]*3
            pygame.draw.rect(self.surface,color,rect)
    def draw_color(self,i,j):
        rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
        pygame.draw.rect(self.surface,self.tiles[i*self.rows+j],rect)
    def draw(self,screen,pos):
        self.surface.fill((0,0,0))
        color2=(50,50,50)
        for i in range(self.cols):
            for j in range(self.rows):
                if self.color: self.draw_color(i,j)
                else: self.draw_white(i,j)
                rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
                pygame.draw.rect(self.surface,color2,rect,width=1)


        color=(200,130,120)
        pygame.draw.rect(self.surface,color,pygame.Rect(0,0,self.width+self.padding,self.height+self.padding),width=self.padding,border_radius=10)
        self.list.draw(screen)


        for i in range(self.cols):
            for j in range(self.rows):
                rect=pygame.Rect((i*self.tile_w+self.padding+pos[0],j*self.tile_h+self.padding+pos[1],self.tile_w,self.tile_h))
                if rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen,(20,200,30),scale_rect(self.list.labels[i*self.rows+j ].rect,5,3),width=3,border_radius=2)

        return self.surface
    def update(self):

        mouse_pos=pygame.mouse.get_pos()
        mouse_pos=(mouse_pos[0]-self.offset[0]-self.padding,mouse_pos[1]-self.offset[1]-self.padding)
        mouse_pressed=pygame.mouse.get_pressed()
        keys=pygame.key.get_pressed()

    def set_white(self,tiles,rows,cols):
        self.color=False
        self.tiles=tiles
        self.rows=rows
        self.cols=cols
        self.tile_w=self.width//self.cols
        self.tile_h=self.height//self.rows

        self.list=Label_list(200,500,800,font,self.tiles,(255,255,255))



class Board:
    def __init__(self,width,heigt,rows,cols,radius=5,offset=(0,0),padding=7):
        self.width=width
        self.height=heigt
        self.rows=rows
        self.cols=cols
        self.tile_w=self.width//self.cols
        self.tile_h=self.height//self.rows

        self.tiles=[0 for i in range(self.rows*self.cols)]
        self.surface=pygame.Surface((self.width+padding*2,self.height+padding*2))
        self.r=radius

        self.padding=padding
        self.offset=offset
    def draw(self):
        self.surface.fill((0,0,0))
        color2=(50,50,50)
        for i in range(self.cols):
            for j in range(self.rows):
                rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
                if self.tiles[i*self.rows+j]:
                    color=[int(self.tiles[i*self.rows+j]*255)]*3
                    pygame.draw.rect(self.surface,color,rect)
                pygame.draw.rect(self.surface,color2,rect,width=1)

        color=(200,130,120)
        pygame.draw.rect(self.surface,color,pygame.Rect(0,0,self.width+self.padding,self.height+self.padding),width=self.padding,border_radius=10)
        return self.surface
    def update(self):
        ret=False

        mouse_pos=pygame.mouse.get_pos()
        mouse_pos=(mouse_pos[0]-self.offset[0]-self.padding,mouse_pos[1]-self.offset[1]-self.padding)
        mouse_pressed=pygame.mouse.get_pressed()
        keys=pygame.key.get_pressed()
        if mouse_pressed[0]:
            i=mouse_pos[0]//self.tile_w
            j=mouse_pos[1]//self.tile_h
            for x in range(max(0,math.floor(i-self.r)),min(self.cols,math.ceil(i+self.r+1))):
                for y in range(max(0,math.floor(j-self.r)),min(self.rows,math.ceil(j+self.r+1))):
                    if (i-x)**2+(j-y)**2>=self.r**2:
                        continue
                    self.tiles[x*self.rows+y]+=0.345
                    self.tiles[x*self.rows+y]=min(1,self.tiles[x*self.rows+y])
                    ret=True
        if keys[pygame.K_c]:
            self.reset()
            ret=True
        return ret
    def reset(self):
        self.tiles=[0 for i in range(self.rows*self.cols)]
    def set(self,tiles):
        self.tiles=tiles
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
#  Colour palette
# ─────────────────────────────────────────────
BG_COLOR        = (15,  17,  26)
SURFACE_BG      = (22,  25,  40)
BAR_COLOR       = (64, 190, 255)
BAR_HIGH_COLOR  = (255, 210,  60)
BAR_LOW_COLOR   = ( 80, 120, 200)
LABEL_COLOR     = (200, 210, 240)
VALUE_COLOR     = (255, 255, 255)
GRID_COLOR      = ( 35,  40,  60)
BORDER_COLOR    = ( 50,  60,  90)
ACCENT_COLOR    = (64, 190, 255)
SHADOW_COLOR    = (  0,   0,   0, 80)

# ─────────────────────────────────────────────
#  Easing
# ─────────────────────────────────────────────
def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3

def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2

def lerp(a, b, t):
    return a + (b - a) * t


# ─────────────────────────────────────────────
#  Single bar state
# ─────────────────────────────────────────────
class Bar:
    ANIM_DURATION = 0.45   # seconds for height animation
    MOVE_DURATION = 0.35   # seconds for x-position animation

    def __init__(self, label: str, value: float, slot: int,
                 bar_w: int, bar_max_h: int, padding: int):
        self.label   = label
        self.value   = value          # current target value (0-1)
        self.slot    = slot           # current column slot

        self.bar_w     = bar_w
        self.bar_max_h = bar_max_h
        self.padding   = padding

        # animation state – value (height)
        self._disp_value  = value
        self._from_value  = value
        self._to_value    = value
        self._val_t       = 1.0

        # animation state – position (x)
        self._disp_slot   = float(slot)
        self._from_slot   = float(slot)
        self._to_slot     = float(slot)
        self._pos_t       = 1.0

    # ── public API ──────────────────────────────
    def set_value(self, new_value: float):
        self._from_value = self._disp_value
        self._to_value   = new_value
        self._val_t      = 0.0
        self.value       = new_value

    def set_slot(self, new_slot: int):
        if new_slot == self.slot:
            return
        self._from_slot = self._disp_slot
        self._to_slot   = float(new_slot)
        self._pos_t     = 0.0
        self.slot       = new_slot

    def update(self, dt: float):
        if self._val_t < 1.0:
            self._val_t = min(1.0, self._val_t + dt / self.ANIM_DURATION)
            self._disp_value = lerp(self._from_value, self._to_value,
                                     ease_out_cubic(self._val_t))

        if self._pos_t < 1.0:
            self._pos_t = min(1.0, self._pos_t + dt / self.MOVE_DURATION)
            self._disp_slot = lerp(self._from_slot, self._to_slot,
                                    ease_in_out_cubic(self._pos_t))

    # ── visual helpers ───────────────────────────
    def is_animating(self):
        return self._val_t < 1.0 or self._pos_t < 1.0

    def display_x(self, left_margin: int) -> float:
        return left_margin + self._disp_slot * (self.bar_w + self.padding)

    def display_h(self) -> float:
        return self._disp_value * self.bar_max_h


# ─────────────────────────────────────────────
#  ProbabilityTable
# ─────────────────────────────────────────────
class ProbabilityTable:
    """
    Renders a sorted probability bar-chart onto its own Surface.

    Parameters
    ----------
    width, height : dimensions of the returned surface
    top_n         : how many bars to show (highest values)
    font          : pygame.font.Font for labels / values
    font_small    : smaller font (optional, falls back to `font`)
    """

    PADDING_FRAC = 0.18   # fraction of bar_w used as gap between bars

    def __init__(self,
                 width: int,
                 height: int,
                 top_n: int,
                 font: pygame.font.Font,
                 font_small: pygame.font.Font | None = None):

        self.width    = width
        self.height   = height
        self.top_n    = top_n
        self.font     = font
        self.font_sm  = font_small or font

        # layout constants
        self.margin_top    = 20
        self.margin_bottom = 56   # room for label + value text
        self.margin_left   = 18
        self.margin_right  = 18

        chart_w = width - self.margin_left - self.margin_right
        self.bar_max_h = height - self.margin_top - self.margin_bottom

        # bar geometry
        # bar_w + padding_w repeated top_n times fills chart_w
        # bar_w / padding_w = 1 / PADDING_FRAC  →  bar_w*(1+PADDING_FRAC)*top_n = chart_w
        self.bar_w = int(chart_w / (top_n * (1 + self.PADDING_FRAC)))
        self.padding = int(self.bar_w * self.PADDING_FRAC)

        self._bars: dict[str, Bar] = {}   # label → Bar
        self._surface = pygame.Surface((width, height), pygame.SRCALPHA)

        self._last_time = time.time()

    # ── public API ───────────────────────────────────────────────────────────

    def set_data(self, data: dict[str, float]):
        """
        Replace / update values.  `data` is {label: probability_0_to_1}.
        Only the top_n are displayed; others are kept in memory but invisible.
        """
        # update or create bars
        for label, value in data.items():
            value = max(0.0, min(1.0, value))
            if label in self._bars:
                self._bars[label].set_value(value)
            else:
                bar = Bar(label, value, slot=0,
                          bar_w=self.bar_w,
                          bar_max_h=self.bar_max_h,
                          padding=self.padding)
                self._bars[label] = bar

        # remove bars that no longer exist
        for label in list(self._bars.keys()):
            if label not in data:
                del self._bars[label]

        self._reassign_slots()

    def _reassign_slots(self):
        """Sort top_n bars descending and assign slot indices."""
        ranked = sorted(self._bars.values(),
                        key=lambda b: b.value, reverse=True)
        visible = ranked[:self.top_n]
        visible_set = set(id(b) for b in visible)

        for i, bar in enumerate(visible):
            bar.set_slot(i)

        # bars leaving the visible area: animate them off to the right
        for bar in self._bars.values():
            if id(bar) not in visible_set:
                bar.set_slot(self.top_n + 1)  # off-screen slot

    # ── update / draw ─────────────────────────────────────────────────────────

    def update(self):
        now = time.time()
        dt  = min(now - self._last_time, 0.1)
        self._last_time = now
        for bar in self._bars.values():
            bar.update(dt)

    def draw(self) -> pygame.Surface:
        """Return the up-to-date Surface (call every frame)."""
        self.update()
        surf = self._surface
        surf.fill((0, 0, 0, 0))

        # background panel
        pygame.draw.rect(surf, SURFACE_BG,
                         (0, 0, self.width, self.height), border_radius=14)
        pygame.draw.rect(surf, BORDER_COLOR,
                         (0, 0, self.width, self.height),
                         width=1, border_radius=14)

        # horizontal grid lines
        for frac in (0.25, 0.5, 0.75, 1.0):
            y = self.margin_top + self.bar_max_h - int(frac * self.bar_max_h)
            pygame.draw.line(surf, GRID_COLOR,
                             (self.margin_left, y),
                             (self.width - self.margin_right, y))
            lbl = self.font_sm.render(f"{int(frac*100)}%", True, GRID_COLOR)
            surf.blit(lbl, (2, y - lbl.get_height() // 2))

        # draw bars – include any bar whose DISPLAY x overlaps the chart area.
        # This covers bars animating in OR out of the visible region.
        all_bars = sorted(self._bars.values(), key=lambda b: b._disp_slot)
        visible = [b for b in all_bars if b._disp_slot < self.top_n + 0.5]

        for bar in visible:
            x  = bar.display_x(self.margin_left)
            h  = bar.display_h()
            y  = self.margin_top + self.bar_max_h - h
            bw = self.bar_w

            # colour interpolation: low=blue, high=yellow
            t = bar._disp_value
            r = int(lerp(BAR_LOW_COLOR[0], BAR_HIGH_COLOR[0], t))
            g = int(lerp(BAR_LOW_COLOR[1], BAR_HIGH_COLOR[1], t))
            b = int(lerp(BAR_LOW_COLOR[2], BAR_HIGH_COLOR[2], t))
            color = (r, g, b)

            # shadow
            shadow_rect = pygame.Rect(int(x)+3, int(y)+3, bw, int(h))
            shadow_surf = pygame.Surface((bw, int(h)+4), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(shadow_surf, (0, 0, 0, 60),
                             (0, 0, bw, int(h)+4), border_radius=6)
            surf.blit(shadow_surf, (int(x)+3, int(y)))

            # bar body
            bar_rect = pygame.Rect(int(x), int(y), bw, max(2, int(h)))
            pygame.draw.rect(surf, color, bar_rect, border_radius=6)

            # glossy highlight
            hi_w = max(2, bw // 3)
            hi_h = max(2, int(h) // 3)
            hi_surf = pygame.Surface((hi_w, hi_h), pygame.SRCALPHA)
            hi_surf.fill((255, 255, 255, 30))
            surf.blit(hi_surf, (int(x) + 4, int(y) + 4))

            # top accent line
            pygame.draw.rect(surf, (255, 255, 255, 180),
                             pygame.Rect(int(x), int(y), bw, 3),
                             border_radius=3)

            # label (below bar)
            text_y = self.margin_top + self.bar_max_h + 6
            lbl_surf = self.font_sm.render(bar.label, True, LABEL_COLOR)
            lx = int(x) + (bw - lbl_surf.get_width()) // 2
            surf.blit(lbl_surf, (lx, text_y))

            # value percentage
            pct_str = f"{bar._disp_value*100:.1f}%"
            val_surf = self.font_sm.render(pct_str, True, VALUE_COLOR)
            vx = int(x) + (bw - val_surf.get_width()) // 2
            surf.blit(val_surf, (vx, text_y + lbl_surf.get_height() + 2))
        return surf
