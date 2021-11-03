"""Illustration of blending methods implemented in impose"""
from impose import flblend
from matplotlib import pylab as plt
import numpy as np
from skimage.draw import disk

fb = flblend.FlBlend()

ax1 = plt.subplot(121, title="RGB blend")
ax2 = plt.subplot(122, title="HSV blend")

for cx, cy, co in [
    [200, 200, "#FF0F00"],
    [200, 300, "#FFD800"],
    [300, 300, "#12FF00"],
    [300, 200, "#000AFF"]
]:

    img = np.zeros((500, 500), dtype=np.uint8)
    rr, cc = disk((cy, cx), 100, shape=img.shape)
    img[rr, cc] = 255

    fb.add_image(img, hue=co)
    ax1.plot(cx, cy, "o", ms=10, color=co)
    ax2.plot(cx, cy, "o", ms=10, color=co)

ax1.imshow(fb.blend("rgb"))
ax2.imshow(fb.blend("hsv"))
plt.tight_layout()
plt.show()
