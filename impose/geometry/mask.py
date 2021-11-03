import numpy as np
from skimage.draw import polygon2mask


def ellipse(x, y, a, b, phi, shape, scale_x=1, scale_y=1):
    xv = np.arange(shape[1]).reshape(1, -1) * scale_x
    yv = np.arange(shape[0]).reshape(-1, 1) * scale_y

    cos_angle = np.cos(np.pi - phi)
    sin_angle = np.sin(np.pi - phi)
    xc = (xv - x + .5)
    yc = (yv - y + .5)

    xct = xc * cos_angle - yc * sin_angle
    yct = xc * sin_angle + yc * cos_angle
    rad_cc = (xct ** 2 / a ** 2) + (yct ** 2 / b ** 2)
    mask = rad_cc <= 1
    return mask


def polygon(points, shape, scale_x=1, scale_y=1):
    points = np.array(points, dtype=float, copy=True)
    points[:, 0] = points[:, 0] / scale_x - .5
    points[:, 1] = points[:, 1] / scale_y - .5
    return polygon2mask(shape, points[:, ::-1])


def rectangle(x, y, a, b, phi, shape, scale_x=1, scale_y=1):
    dx = a / 2
    dy = b / 2
    xv = np.array([dx, dx, -dx, -dx])
    yv = np.array([dy, -dy, -dy, dy])
    xr = xv * np.cos(phi) - yv * np.sin(phi)
    yr = xv * np.sin(phi) + yv * np.cos(phi)
    points = np.zeros((4, 2), dtype=float)
    points[:, 0] = (x + xr) / scale_x - .5
    points[:, 1] = (y + yr) / scale_y - .5
    return polygon2mask(shape, points[:, ::-1])
