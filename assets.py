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
    def update(self,mp):
        if not self.function:
            return
        if pygame.mouse.get_pressed()[0]:
            if self.rect.collidepoint(mp):
                self.function()

class Label_list:
    def __init__(self,x,y,max_width,font:pygame.font.Font,texts,color,max_items=False,pos_type=0):
        self.x=x
        self.y=y
        self.w=max_width
        self.font=font
        self.generate_labels(texts,color,max_items)
        self.generate_rect()
        self.pos_type=pos_type
        if self.pos_type==1:
            self.center()

    def center(self):
        diff=self.x-self.rect.centerx
        self.rect.x+=diff
        for i in self.labels:
            i.rect.x+=diff
        for i in self.helpers:
            i.rect.x+=diff

    def generate_rect(self):
        padding=10
        self.rect=scale_rect(pygame.Rect(self.x,self.y,self.mw,self.h),padding,padding)
    def generate_labels(self,texts,color,mi):
        self.labels=[]
        self.helpers=[]
        self.mw=0
        x=self.x
        y=self.y
        self.helpers.append(Label((x,y),"[",self.font,color,pos_type=1,padding=0))
        x+=self.helpers[-1].get_width()
        for i in texts:
            self.labels.append(Label((x,y),str(i),self.font,color,pos_type=1,padding=0))
            x+=self.labels[-1].get_width()
            self.helpers.append(Label((x,y),", ",self.font,color,pos_type=1,padding=0))
            x+=self.helpers[-1].get_width()
            if x-self.x>=self.w:
                self.mw=max(self.mw,x-self.x)
                x=self.x
                y+=self.labels[-1].get_height()
        if mi:
            self.helpers.append(Label((x,y),"...]",self.font,color,pos_type=1))
            print(1)
        else:
            self.helpers.append(Label((x,y),"]",self.font,color,pos_type=1))
        x+=self.helpers[-1].get_width()


        self.h=self.helpers[-1].rect.bottom-self.y
        self.mw=max(self.mw,x-self.x)
    def draw(self,screen):
        bg=(50,50,50)
        border=(20,20,20)
        r=10
        pygame.draw.rect(screen,bg,self.rect,border_radius=r)
        pygame.draw.rect(screen,border,self.rect,width=5,border_radius=r)
        for i in self.helpers:
            i.draw(screen)
        for i in self.labels:
            i.draw(screen)
    def update(self):
        for i ,j in zip(self.helpers,self.labels):
            i.update(),j.update()
class input_str:
    def __init__(self,x,y,max_width,font:pygame.font.Font,texts,color,res):
        self.x=x
        self.y=y
        self.w=max_width
        self.font=font
        self.generate_labels(texts,color)

        self.list=Label_list(600,420,600,font,res,(255,255,255),pos_type=1)
    def generate_labels(self,texts,color):
        self.labels=[]
        x=self.x
        y=self.y
        for i in texts:
            self.labels.append(Label((x,y),str(i),self.font,color,pos_type=1,padding=0))
            x+=self.labels[-1].get_width()
            if x-self.x>=self.w:
                x=self.x
                y+=self.labels[-1].get_height()
    def draw(self,screen,mp):
        for i in self.labels:
            i.draw(screen)
        self.list.draw(screen)

        for i in range(len(self.labels)):
            if self.labels[i].rect.collidepoint(mp):
                w=6
                pygame.draw.rect(screen,(20,200,30),scale_rect(self.list.labels[i].rect,7,3),width=w,border_radius=2)
                pygame.draw.rect(screen,(20,30,200),scale_rect(self.labels[i].rect,7,3),width=w,border_radius=2)

    def update(self):
        pass

class InputBoard:
    def __init__(self,width,heigt,rows,cols,offset=(0,0),padding=7,image=None,max_items=None,font=font):
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

        self.surface=pygame.Surface((self.width+padding*2,self.height+padding*2))

        self.padding=padding
        self.offset=offset

        self.font=font
        if max_items==None: self.max_items=-1
        else: self.max_items=max_items
        # print(max_items)
        self.generate_list()
    def generate_list(self):
        t=self.tiles[:self.max_items] if self.max_items!=-1 else self.tiles
        self.list=Label_list(600,580,600,self.font,t,(200,200,200),max_items=True if self.max_items!=-1 else False,pos_type=1)
    def draw_white(self,i,j):
        rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
        if self.tiles[i*self.rows+j]:
            color=[int(self.tiles[i*self.rows+j]*255)]*3
            pygame.draw.rect(self.surface,color,rect)
    def draw_color(self,i,j):
        rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
        pygame.draw.rect(self.surface,self.tiles[i*self.rows+j],rect)
    def draw(self,screen,pos,mp):
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
                if rect.collidepoint(mp) and (self.max_items==-1 or i*self.rows+j<self.max_items):
                    w=6
                    pygame.draw.rect(screen,(20,200,30),scale_rect(self.list.labels[i*self.rows+j ].rect,7,3),width=w,border_radius=3)

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
        dec=100.0
        for i in range(len(self.tiles)):
            self.tiles[i]=int(self.tiles[i]*dec)/dec

        self.generate_list()



class Board:
    def __init__(self,width,heigt,rows,cols,radius=5,offset=(0,0),padding=7,alfa=0.4):
        self.alfa=alfa

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
    def update(self,mp):
        ret=False

        mouse_pos=mp
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
                    self.tiles[x*self.rows+y]+=self.alfa#34
                    self.tiles[x*self.rows+y]=min(1,self.tiles[x*self.rows+y])
                    ret=True
        if keys[pygame.K_c]:
            self.reset()
            ret=True
        if keys[pygame.K_x]:
            self.save("x")
            time.sleep(2)
        if keys[pygame.K_o]:
            self.save("o")
            time.sleep(2)

        return ret
    def reset(self):
        self.tiles=[0 for i in range(self.rows*self.cols)]
    def set(self,tiles):
        self.tiles=tiles
    def save(self,label):
        with open("XOmodel_traindata.txt", "a") as f:
            f.write(label+"/n")
            f.write(" ".join([str(i) for i in self.tiles])+"/n")

class Picker_with_func:
    def __init__(self,
                 x: int, y: int,
                 width: int,
                 height:int,
                 options: list[str],
                 font: pygame.font.Font,
                 func:list,
                 ):
        self.picker=Picker(x,y,width,height,options,font)
        self.func=func
        self.cur=0
        self.options=options
        # self.pos=(x,y)
    def draw(self,screen):
        self.picker.draw(screen)
    def handle_event(self,ev,mp):
        self.picker.handle_event(ev,mp)
    def update(self,mp):
        self.picker.update(mp)
        if self.picker.selected_index!=self.cur:
            self.cur=self.picker.selected_index
            self.func[self.cur]()


class Picker:
    def __init__(self, x, y, width, height, options, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = 0
        self.font = font

        self.is_open = False
        self.animation_progress = 0  # 0 = closed, 1 = open
        self.animation_speed = 0.2

        self.option_height = height
        self.bg_color = (100, 100, 100)  # not transparent
        self.text_color = (0, 0, 0)
        self.hover_index = -1

    def handle_event(self, event,mp):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mp):
                self.is_open = not self.is_open
            elif self.is_open:
                for i, option_rect in enumerate(self.get_option_rects()):
                    if option_rect.collidepoint(mp):
                        self.selected_index = i
                        self.is_open = False

    def update(self,mp):
        # animation
        target = 1 if self.is_open else 0
        if self.animation_progress < target:
            self.animation_progress = min(target, self.animation_progress + self.animation_speed)
        elif self.animation_progress > target:
            self.animation_progress = max(target, self.animation_progress - self.animation_speed)

        # hover
        if self.is_open:
            mouse_pos = mp
            self.hover_index = -1
            for i, rect in enumerate(self.get_option_rects()):
                if rect.collidepoint(mouse_pos):
                    self.hover_index = i
        else:
            self.hover_index = -1

    def draw(self, surface):
        # draw selected
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=8)
        text = self.font.render(self.options[self.selected_index], True, self.text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))

        # draw dropdown with animation
        if self.animation_progress > 0:
            total_height = int(len(self.options) * self.option_height * self.animation_progress)
            dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height,
                self.rect.width,
                total_height
            )

            pygame.draw.rect(surface, self.bg_color, dropdown_rect, border_radius=8)

            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.height + i * self.option_height,
                    self.rect.width,
                    self.option_height
                )

                if option_rect.bottom > dropdown_rect.bottom:
                    break

                if i == self.hover_index:
                    pygame.draw.rect(surface, (220, 220, 220), option_rect,border_radius=8)

                text = self.font.render(option, True, self.text_color)
                surface.blit(text, text.get_rect(center=option_rect.center))

    def get_option_rects(self):
        rects = []
        for i in range(len(self.options)):
            rects.append(pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height + i * self.option_height,
                self.rect.width,
                self.option_height
            ))
        return rects

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
