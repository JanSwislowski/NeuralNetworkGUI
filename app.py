import random

import pygame
import numpy as np
from neural_network import NeuralNetwork
from nn_vis import NeuralNetworkVisualizer
from assets import Board,ProbabilityTable,Label,InputBoard,input_str,Picker_with_func
from mouse import Mouse
pygame.init()

font = pygame.font.SysFont("dejavusans", 16)
font_sm = pygame.font.SysFont("dejavusans", 13)
font_big = pygame.font.SysFont("dejavusans", 22, bold=True)
font_verybig = pygame.font.SysFont("dejavusans", 50, bold=True)
class Input_page:
    def __init__(self,prev_page_lambda):
        self.exit=Label((70,10),"<-",font_verybig,(155,155,155),5,border_color=(200,0,0),function=prev_page_lambda,padding=10)

        self.label=Label((440,25),"Model:",font_verybig,(255,255,255),padding=0,pos_type=1)
        func=[lambda: self.change_board("board1"),lambda: self.change_board("board2"),lambda: self.change_board("board3"),]
        self.picker=Picker_with_func(600,25,200,50,["current","image","text"],font,func,)


        board_w=400
        board_h=400
        self.boards_pos=(600-board_w//2,100)

        text_w=800
        text_x=600-text_w//2
        text="Jeffrey Epstein falso accusatus est de concubitu cum pueris. Similis sors soli nigro viro cum reverentia accidit — Diddy. Liberate Diddy et Epstein!!!"
        texts=[text[i:i+3] for i in range(0,len(text),3)]
        res=random.sample(range(1, 100), len(texts))
        self.boards={
            "board1":InputBoard(board_w,board_h,3,3,self.boards_pos,4,max_items=None,font=font_verybig),
            "board2":InputBoard(board_w,board_h,25,25,self.boards_pos,4,image="img.png",max_items=40,font=font_big),
            "board3":input_str(text_x,self.boards_pos[1]+20,text_w,font_verybig,texts,(255,255,255),res,)
        }
        self.current_board="board1"
    def change_board(self,board):
        self.current_board=board
    def reset(self):
        self.current_board="board1"
    def draw(self,screen,mp):
        self.exit.draw(screen)

        if self.current_board not in ("board3"):
            screen.blit(self.boards[self.current_board].draw(screen,self.boards_pos,mp),self.boards_pos)
        else:
            self.boards[self.current_board].draw(screen,mp)
        self.picker.draw(screen)
        self.label.draw(screen)
    def set_board(self,board:Board):
        self.boards["board1"].set_white(board.tiles,board.rows,board.cols)
    def update(self,mp):
        self.boards[self.current_board].update()
        self.exit.update(mp)
        self.picker.update(mp)
    def handle_events(self,ev,mp):
        self.picker.handle_event(ev,mp)
class Output_page:
    def __init__(self,prev_page_lambda):
        self.exit=Label((70,10),"<-",font_verybig,(155,155,155),5,border_color=(200,0,0),function=prev_page_lambda,padding=10)
        #1 is X or O
        # 2 is MNIST
        # 3 is LLMS
        func=[lambda: self.change_prob(1),lambda: self.change_prob(2),lambda: self.change_prob(3),]
        self.picker=Picker_with_func(600,65,200,50,["XO","MNIST","text"],font,func,)

        self.label=Label((440,60),"Model:",font_verybig,(255,255,255),padding=0,pos_type=1)

        self.current_prob=1
        self.prob_pos=(200,200)
        self.prob=ProbabilityTable(800,500,5,font_verybig,font_big)

        self.last_change=pygame.time.get_ticks()
        self.change_interval=3e3

    def prob_func(self,n):
        alpha = 0.1  # smaller than 1 → more extreme
        x = np.random.dirichlet(np.ones(n) * alpha)

        return x
    def generate_prob1(self):
        #X or O
        arr=["X","O"]
        x=self.prob_func(len(arr))
        return {i:j for i,j in zip(arr,x)}
    def generate_prob2(self):
        #X or O
        arr=[str(i) for i in range(10)]
        x=self.prob_func(len(arr))
        return {i:j for i,j in zip(arr,x)}
    def generate_prob3(self):
        #X or O
        arr=["nig","gga","ret","ard"," res","pek","t. ","city","boy","!*@","nir!"]

        x=self.prob_func(len(arr))
        return {i:j for i,j in zip(arr,x)}

    def change_prob(self,prob):
        if prob==1:
            t=self.generate_prob1()
            self.prob.set_data(t)
            self.current_prob=1
        elif prob==2:
            t=self.generate_prob2()
            self.prob.set_data(t)
            self.current_prob=2
        elif prob==3:
            t=self.generate_prob3()
            self.prob.set_data(t)
            self.current_prob=3


    def reset(self):
        self.current_prob=1
    def draw(self,screen,x):
        self.exit.draw(screen)

        screen.blit(self.prob.draw(),self.prob_pos)
        self.picker.draw(screen)
        self.label.draw(screen)
    def update(self,mp):
        # print(self.last_change-t)
        self.exit.update(mp)
        self.picker.update(mp)
        self.prob.update()
        t=pygame.time.get_ticks()
        if t-self.last_change>self.change_interval:
            self.change_prob(self.current_prob)
            self.last_change=t
    def handle_events(self,ev,mp):
        self.picker.handle_event(ev,mp)
class Mainpage:
    def __init__(self,cols:int,rows:int,network_file:str,labels:list,input_page_lambda,output_page_lambda,radius,alfa):
        self.labels=labels
        self.nn=NeuralNetwork.load(network_file)

        self.font     = font
        self.font_sm  = font_sm
        self.font_big = font_big

        board_w=400
        board_h=400
        self.board_pos=(50,80)

        self.board=Board(board_w,board_h,rows,cols,radius,self.board_pos,alfa=alfa)

        table_w=400
        table_h=150
        self.table_pos=(50,580)
        self.table=ProbabilityTable(table_w,table_h,6,self.font_big,self.font)

        vis_w=650
        vis_h=600
        self.vispos=(500,110)
        self.vis=NeuralNetworkVisualizer(self.nn,vis_w,vis_h,offset=self.vispos,max_neurons=20)

        self.input_label=Label((self.table_pos[0]+table_w//2,10),"Wejście:",font_verybig,(255,255,255),function=input_page_lambda)
        self.output_label=Label((self.table_pos[0]+table_w//2,510),"Wyjście:",font_verybig,(255,255,255),function=output_page_lambda)

        self.forward_input()
    def forward_input(self):
        input_data=self.board.tiles
        prediction=self.nn.predict_probs(input_data)
        probs={self.labels[i]:prediction[i] for i in range(len(self.labels))}
        self.table.set_data(probs)
    def update(self,mp):
        if self.board.update(mp):
            self.forward_input()
        self.input_label.update(mp)
        self.output_label.update(mp)
    def handle_events(self,event,mp):
        self.vis.handle_event(event,mp)
    def reset(self):
        return

    def draw(self,screen,x):
        screen.blit(self.board.draw(),self.board_pos)
        screen.blit(self.table.draw(),self.table_pos)
        self.vis.draw()
        screen.blit(self.vis.surface,self.vispos)
        self.input_label.draw(screen)
        self.output_label.draw(screen)
class App:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 1200, 800
        self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.w, self.h = self.display.get_size()
        self.mouse=Mouse(self.WIDTH,self.HEIGHT,self.w,self.h)
        self.mp=None

        self.screen=pygame.Surface((self.WIDTH,self.HEIGHT))

        self.label=Label((700,25),"Model:",font_verybig,(255,255,255),padding=0,pos_type=1)
        func=[lambda: self.switch_pages("MNIST"),lambda: self.switch_pages("XO")]
        self.picker=Picker_with_func(850, 30, 200, 50, ["MNIST", "XO"], font_big, func,)
        self.pages={
            "MNIST":Mainpage(28,28,"mnist_model.npz",[str(i) for i in range(10)],lambda: self.switch_pages("Input"),lambda: self.switch_pages("Output"),radius=2,alfa=0.4),
            "XO": Mainpage(3,3,"xo_model.npz",["x","o"],lambda: self.switch_pages("Input"),lambda: self.switch_pages("Output"),radius=1,alfa=0.2),
            "Input":Input_page(lambda: self.switch_pages("previous")),
            "Output":Output_page(lambda: self.switch_pages("previous")),
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
        self.mp=self.mouse.get_pos()
        self.pages[self.current_page].update(self.mp)
        if self.current_page in ("MNIST","XO"):
            self.picker.update(self.mp)
    def handle_events(self,mp):
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                return False
            self.pages[self.current_page].handle_events(ev,mp)
            if self.current_page in ("MNIST","XO"):
                self.picker.handle_event(ev,mp)
        return True
    def draw(self):
        self.screen.fill(0)
        self.pages[self.current_page].draw(self.screen,self.mp)
        if self.current_page in ("MNIST","XO"):
            self.picker.draw(self.screen)
            self.label.draw(self.screen)
        self.display.blit(pygame.transform.smoothscale(self.screen,(self.w,self.h)),(0,0))
    def run(self):
        fps = 60
        running = True
        while running:
            pygame.time.delay(1000 // fps)
            self.update()
            running=self.handle_events(self.mp)
            self.draw()
            pygame.display.flip()
app=App()
app.run()





