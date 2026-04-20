from neural_network import NeuralNetwork
from nn_vis import NeuralNetworkVisualizer
from assets import Board,ProbabilityTable,Picker
from functions import image_to_list
import pygame
pygame.init()
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

    def draw_white(self,i,j):
        rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
        if self.tiles[i*self.rows+j]:
            color=[int(self.tiles[i*self.rows+j]*255)]*3
            pygame.draw.rect(self.surface,color,rect)
    def draw_color(self,i,j):
        rect=pygame.Rect((i*self.tile_w+self.padding,j*self.tile_h+self.padding,self.tile_w,self.tile_h))
        pygame.draw.rect(self.surface,self.tiles[i*self.rows+j],rect)
    def draw(self):
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
        return self.surface
    def update(self):

        mouse_pos=pygame.mouse.get_pos()
        mouse_pos=(mouse_pos[0]-self.offset[0]-self.padding,mouse_pos[1]-self.offset[1]-self.padding)
        mouse_pressed=pygame.mouse.get_pressed()
        keys=pygame.key.get_pressed()

    def set_white(self,tiles):
        self.color=False
        self.tiles=tiles

class Input_page:
    def __init__(self):
        # board_w=
        self.boards={
            "board1":InputBoard()
        }
class Mainpage:
    def __init__(self,cols:int,rows:int,network_file:str,labels:list):
        self.labels=labels
        self.nn=NeuralNetwork.load(network_file)

        self.font     = pygame.font.SysFont("dejavusans", 16)
        self.font_sm  = pygame.font.SysFont("dejavusans", 13)
        self.font_big = pygame.font.SysFont("dejavusans", 22, bold=True)

        board_w=400
        board_h=400
        self.board_pos=(50,120)
        pr=2
        self.board=Board(board_w,board_h,rows,cols,pr,self.board_pos)

        table_w=400
        table_h=150
        self.table_pos=(50,580)
        self.table=ProbabilityTable(table_w,table_h,6,self.font_big,self.font)

        vis_w=650
        vis_h=600
        self.vispos=(500,120)
        self.vis=NeuralNetworkVisualizer(self.nn,vis_w,vis_h,offset=self.vispos)

        self.forward_input()
    def forward_input(self):
        input_data=self.board.tiles
        prediction=self.nn.predict_probs(input_data)
        probs={self.labels[i]:prediction[i] for i in range(len(self.labels))}
        self.table.set_data(probs)
    def update(self):
        if self.board.update():
            self.forward_input()
    def handle_events(self,event):
        self.vis.handle_event(event)

    def draw(self,screen):
        screen.blit(self.board.draw(),self.board_pos)
        screen.blit(self.table.draw(),self.table_pos)
        self.vis.draw()
        screen.blit(self.vis.surface,self.vispos)
class App:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen=pygame.display.set_mode((self.WIDTH,self.HEIGHT))
        self.pages={
            "MNIST":Mainpage(28,28,"mnist_model.npz",[str(i) for i in range(10)])
        }
        self.current_page="MNIST"
    def update(self):
        self.pages[self.current_page].update()
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                return False
            self.pages[self.current_page].handle_events(ev)
        return True
    def draw(self):
        self.screen.fill(0)
        self.pages[self.current_page].draw(self.screen)
    def run(self):
        fps = 60
        running = True
        while running:
            pygame.time.delay(1000 // fps)
            running=self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
app=App()
app.run()





