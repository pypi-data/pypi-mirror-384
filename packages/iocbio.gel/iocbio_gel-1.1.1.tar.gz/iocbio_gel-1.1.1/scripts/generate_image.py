import numpy as np
import skimage

d = np.zeros((1024, 1024))

boxes = [[200, 100, 20], [500, 500, 50]]

for b in boxes:
    d[b[0] : b[0] + b[2], b[1] : b[1] + b[2]] = 100

ox = np.arange(0, 100, 100 / d.shape[0])
print(ox, ox.shape)
offset = np.meshgrid(np.zeros(d.shape[1]), ox)[1]
d += offset
d = d.astype(np.uint8)
print(d.min(), d.max())
skimage.io.imsave("test.tif", d)
