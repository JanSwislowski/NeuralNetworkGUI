import numpy as np
from settings import *
from neural_network import NeuralNetwork
from data import get_mnist_data
def get_batch(images, labels, batch_size):
    indices = np.random.choice(len(images), batch_size)
    # print("Batch indices:", indices)  # Debugging line to check the generated indices
    return images[indices], labels[indices]
def train_network(batches,batchsize,epochs,learning_rate,images,labels,nn):
    for batch in range(batches):
        batch_images, batch_labels = get_batch(images, labels, batchsize)
        print(batch, "total loss", nn.train(batch_images, batch_labels, epochs=epochs, learning_rate=learning_rate))
    print("Training complete!")

images, labels = get_mnist_data()
nn=NeuralNetwork(layers)
train_network(batches,batch_size,epochs,learning_rate,images,labels,nn)
nn.save("mnist_model.npz")