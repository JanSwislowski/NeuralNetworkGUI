import struct
import numpy as np
def rotate_images(images):
    arr=np.empty_like(images)
    for i in range(len(images)):
        arr[i]=np.rot90(images[i],k=-1)
    #reflect vertically
    for i in range(len(arr)):
        arr[i]=np.flip(arr[i],axis=1)
    return arr
def get_mnist_data():
    with open('train-labels.idx1-ubyte', 'rb') as f:
        magic, num_labels = struct.unpack('>II', f.read(8))  # read header
        labels = list(f.read(num_labels))  # rest is just raw bytes, one per label
        labels = np.array(labels, dtype=np.uint8)  # convert to numpy array

    with open('train-images.idx3-ubyte', 'rb') as f:
        magic, num_images, rows, cols = struct.unpack('>IIII', f.read(16))  # 16 byte header
        images = np.frombuffer(f.read(), dtype=np.uint8)
        images = images.reshape(num_images, rows,cols)  # shape: (60000, 28, 28)
        images=rotate_images(images)
        images = images.reshape(num_images, -1)
        images= images.astype(np.float32) / 255.0

    return images, labels