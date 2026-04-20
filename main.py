import pygame
from neural_network import NeuralNetwork
from data import get_mnist_data
from assets import Board
from settings import *
from functions import to_percents

images, labels = get_mnist_data()


nn=NeuralNetwork.load("mnist_model.npz")


WIDTH, HEIGHT = 500, 500
screen=pygame.display.set_mode((WIDTH,HEIGHT))
board=Board(WIDTH,HEIGHT,grid_w,grid_h,radius=1.5)
i=0
board.set(images[i])
print("Actual:",labels[i])

fps=30
running=True
while running:
    keys=pygame.key.get_pressed()
    pygame.time.delay(1000//fps)
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
    board.update()
    board.draw()
    screen.blit(board.surface,(0,0))
    pygame.display.flip()

    if keys[pygame.K_RIGHT]:
        i=(i+1)%len(images)
        board.set(images[i])
        print("Actual:",labels[i])


    if keys[pygame.K_RETURN]:
        input_data=board.tiles
        prediction=nn.predict_probs(input_data)
        print("Predicted:",to_percents(prediction))
print("Model saved!")