import pygame
class Mouse:
    def __init__(self,screen_w,screen_h,display_w,display_h):
        self.sw=screen_w
        self.sh=screen_h
        self.dw=display_w
        self.dh=display_h
    def get_pos(self):
        mp=pygame.mouse.get_pos()
        ratio_w=mp[0]/self.dw
        ratio_h=mp[1]/self.dh
        return (int(ratio_w*self.sw),int(ratio_h*self.sh))
