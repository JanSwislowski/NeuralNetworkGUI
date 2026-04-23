import numpy as np

def relu(x):
    return np.maximum(0, x)

def relu_derivative(x):
    return (x > 0).astype(float)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_derivative(x):
    return x * (1 - x)

def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()

def one_hot_encode(label, num_classes):
    encoding = np.zeros(num_classes)
    encoding[label] = 1.0
    return encoding

def mean_squared_error(predicted, actual):
    return np.mean((predicted - actual) ** 2)

def cross_entropy_loss(predicted, actual):
    return -np.sum(actual * np.log(predicted + 1e-9))
def to_percents(probs):
    return [f"{p*100:.2f}%" for p in probs]

import pygame
import numpy as np

def get_color_at(arr, x, y, tile_w, tile_h):
    # Extract block
    block = arr[x:x+tile_w, y:y+tile_h]

    # Mean color (best default)
    color = block.mean(axis=(0, 1))

    return tuple(color.astype(int))


def image_to_list(rows, cols, file):
    img = pygame.image.load(file).convert()
    w, h = img.get_size()

    # Convert to numpy array (shape: width, height, 3)
    arr = pygame.surfarray.array3d(img)

    l = []
    tile_w = w // cols
    tile_h = h // rows

    for i in range(cols):
        for j in range(rows):
            color = get_color_at(
                arr,
                i * tile_w,
                j * tile_h,
                tile_w,
                tile_h
            )
            l.append(color)
    return l
def scale_rect(rect:pygame.Rect,dw,dh):
    return pygame.Rect(rect.x-dw,rect.y-dh,rect.w+dw*2,rect.h+dh*2)