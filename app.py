import pygame
from neural_network import NeuralNetwork
from nn_vis import NeuralNetworkVisualizer
from assets import Board,ProbabilityTable,Picker,Label,InputBoard
pygame.init()

font = pygame.font.SysFont("dejavusans", 16)
font_sm = pygame.font.SysFont("dejavusans", 13)
font_big = pygame.font.SysFont("dejavusans", 22, bold=True)
font_verybig = pygame.font.SysFont("dejavusans", 50, bold=True)
class Input_page:
    def __init__(self,prev_page_lambda):
        board_w=400
        board_h=400
        self.exit=Label((70,10),"<-",font_verybig,(155,155,155),5,border_color=(200,0,0),function=prev_page_lambda,padding=10)
        self.boards_pos=(600-board_w//2,50)
        self.boards={
            "board1":InputBoard(board_w,board_h,3,3,self.boards_pos,4)
        }
        self.current_board="board1"
    def reset(self):
        self.current_board="board1"
    def draw(self,screen):
        self.exit.draw(screen)
        screen.blit(self.boards[self.current_board].draw(screen,self.boards_pos),self.boards_pos)
    def set_board(self,board:Board):
        self.boards["board1"].set_white(board.tiles,board.rows,board.cols)
    def update(self):
        self.boards[self.current_board].update()
        self.exit.update()
    def handle_events(self,ev):
        return
class Mainpage:
    def __init__(self,cols:int,rows:int,network_file:str,labels:list,input_page_lambda,output_page_lambda):
        self.labels=labels
        self.nn=NeuralNetwork.load(network_file)

        self.font     = font
        self.font_sm  = font_sm
        self.font_big = font_big

        board_w=400
        board_h=400
        self.board_pos=(50,80)
        pr=2
        self.board=Board(board_w,board_h,rows,cols,pr,self.board_pos)

        table_w=400
        table_h=150
        self.table_pos=(50,580)
        self.table=ProbabilityTable(table_w,table_h,6,self.font_big,self.font)

        vis_w=650
        vis_h=600
        self.vispos=(500,110)
        self.vis=NeuralNetworkVisualizer(self.nn,vis_w,vis_h,offset=self.vispos)

        self.input_label=Label((self.table_pos[0]+table_w//2,10),"Wejście:",font_verybig,(255,255,255),function=input_page_lambda)
        self.output_label=Label((self.table_pos[0]+table_w//2,510),"Wyjście:",font_verybig,(255,255,255),function=output_page_lambda)

        self.forward_input()
    def forward_input(self):
        input_data=self.board.tiles
        prediction=self.nn.predict_probs(input_data)
        probs={self.labels[i]:prediction[i] for i in range(len(self.labels))}
        self.table.set_data(probs)
    def update(self):
        if self.board.update():
            self.forward_input()
        self.input_label.update()
        self.output_label.update()
    def handle_events(self,event):
        self.vis.handle_event(event)
    def reset(self):
        return

    def draw(self,screen):
        screen.blit(self.board.draw(),self.board_pos)
        screen.blit(self.table.draw(),self.table_pos)
        self.vis.draw()
        screen.blit(self.vis.surface,self.vispos)
        self.input_label.draw(screen)
        self.output_label.draw(screen)
class App:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen=pygame.display.set_mode((self.WIDTH,self.HEIGHT))
        self.pages={
            "MNIST":Mainpage(28,28,"mnist_model.npz",[str(i) for i in range(10)],lambda: self.switch_pages("Input"),lambda: self.switch_pages("Output")),
            "Input":Input_page(lambda: self.switch_pages("previous"))
        }
        self.current_page="MNIST"
        self.previous_page=None
    def switch_pages(self,page):
        if page=="previous":
            if not self.previous_page: return
            self.current_page=self.previous_page
            return
        if page=="Input":
            self.pages[page].reset()
            self.pages[page].set_board(self.pages[self.current_page].board)

        self.previous_page=self.current_page
        self.current_page=page
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





