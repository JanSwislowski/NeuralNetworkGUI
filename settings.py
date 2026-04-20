grid_w=28
grid_h=28
tiles=grid_w*grid_h
layers=[tiles,128, 64, 32, 10]

#training settings
batches=int(1e4)
batch_size=300
epochs=1
learning_rate=0.0001