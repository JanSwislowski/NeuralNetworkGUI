import numpy as np
from functions import *


class Layer:
    def __init__(self, n, m, activation='relu'):
        self.activation = activation
        self.W = np.random.randn(m, n) * np.sqrt(2 / n)  # He init
        self.b = np.zeros(m)
        self.input = None
        self.output = None

    def forward(self, x):
        self.input = x
        z = self.W @ x + self.b
        self.output = relu(z) if self.activation == 'relu' else z
        return self.output

    def backward(self, delta, learning_rate):
        grad = delta * (relu_derivative(self.output) if self.activation == 'relu' else 1.0)
        self.W -= learning_rate * np.outer(grad, self.input)
        self.b -= learning_rate * grad
        return self.W.T @ grad


class NeuralNetwork:
    def __init__(self, layer_sizes):
        self.layer_sizes = layer_sizes
        self.layers = [
            Layer(layer_sizes[i], layer_sizes[i + 1],
                  activation='relu' if i < len(layer_sizes) - 2 else 'linear')
            for i in range(len(layer_sizes) - 1)
        ]

    def forward(self, x):
        x = np.asarray(x, dtype=float)
        for layer in self.layers:
            x = layer.forward(x)
        return softmax(x)

    def backward(self, predicted, actual, learning_rate):
        delta = predicted - actual
        for layer in reversed(self.layers):
            delta = layer.backward(delta, learning_rate)

    def train(self, X, y, epochs=1, learning_rate=0.01):
        num_classes = self.layer_sizes[-1]
        X = np.asarray(X, dtype=float)
        for epoch in range(epochs):
            total_loss = 0.0
            for xi, yi in zip(X, y):
                label = one_hot_encode(int(yi), num_classes)
                predicted = self.forward(xi)
                total_loss += cross_entropy_loss(predicted, label)
                self.backward(predicted, label, learning_rate)
        return total_loss / len(X)

    def predict_probs(self, x):
        return self.forward(x)

    def predict_class(self, x):
        return int(np.argmax(self.predict_probs(x)))

    def save(self, path):
        data = {
            "layer_sizes": self.layer_sizes,
            **{f"W_{i}": layer.W for i, layer in enumerate(self.layers)},
            **{f"b_{i}": layer.b for i, layer in enumerate(self.layers)},
        }
        np.savez(path, **data)

    @classmethod
    def load(cls, path):
        data = np.load(path if path.endswith(".npz") else path + ".npz", allow_pickle=False)
        layer_sizes = data["layer_sizes"].tolist()
        nn = cls(layer_sizes)
        for i, layer in enumerate(nn.layers):
            layer.W = data[f"W_{i}"]
            layer.b = data[f"b_{i}"]
        return nn