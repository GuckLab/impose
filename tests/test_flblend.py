import pathlib

import numpy as np
import pytest

from impose import flblend


data_path = pathlib.Path(__file__).parent / "data"


def test_flb_shape():
    fb = flblend.FlBlend()
    image = np.linspace(0, 1, 1000).reshape(10, 100)
    fb.add_image(image, hue=150)
    assert fb.shape == (10, 100)


def test_flb_blend_no_image_data():
    fb = flblend.FlBlend()
    with pytest.warns(flblend.NoImageDataWarning, match="No image data"):
        image = fb.blend()
    assert image.shape == (2, 2)


def test_flb_blend_hsv():
    fb = flblend.FlBlend()
    im1 = np.linspace(0, 1, 100, endpoint=True).reshape(10, 10)
    im2 = np.linspace(0, 1, 100, endpoint=True)[::-1].reshape(10, 10)
    fb.add_image(im1, hue=0)
    fb.add_image(im2, hue=256/3)
    rgb = fb.blend(mode="hsv")
    assert np.allclose(rgb[0, 0, 0], 0.45)  # did not check/fully understand
    assert rgb[0, 0, 1] == 1 / len(fb)
    assert rgb[-1, -1, 0] == 1 / len(fb)
    assert np.allclose(rgb[-1, -1, 1], 0.45)  # did not check/fully understand
    # NaN values should have no influence on the color
    im3 = np.full((10, 10), np.nan)
    fb.add_image(im3, hue=0)
    rgb_nan = fb.blend(mode="hsv")
    assert (rgb_nan == rgb).all()


def test_flb_blend_rgb():
    fb = flblend.FlBlend()
    im1 = np.linspace(0, 1, 100, endpoint=True).reshape(10, 10)
    im2 = np.linspace(0, 1, 100, endpoint=True)[::-1].reshape(10, 10)
    fb.add_image(im1, hue=0)
    fb.add_image(im2, hue=256/3)
    rgb = fb.blend(mode="rgb")
    assert rgb[0, 0, 0] == 0
    assert rgb[0, 0, 1] == 1 / len(fb)
    assert rgb[-1, -1, 0] == 1 / len(fb)
    assert rgb[-1, -1, 1] == 0
    # NaN values should have no influence on the color
    im3 = np.full((10, 10), np.nan)
    fb.add_image(im3, hue=0)
    rgb_nan = fb.blend(mode="rgb")
    assert (rgb_nan == rgb).all()


def test_fli_get_hsv():
    image = np.linspace(.1, .9, 100).reshape(10, 10)
    fi = flblend.FlImage(image=image, hue=123)
    hsv = fi.get_hsv()
    assert np.all(hsv[:, :, 0] == 123/255)
    assert np.all(hsv[:, :, 1] == 1)
    assert np.all(hsv[:, :, 2] != 1), "b/c different value of the image"
    # Test behaviour for NaN values
    image = np.ndarray((1, 3), buffer=np.array([0, np.nan, 1]))
    fi = flblend.FlImage(image=image, hue=123)
    hsv = fi.get_hsv()
    assert np.allclose(hsv[:, 0, :], [0, 0, 0])
    assert np.all(np.isnan(hsv[:, 1, :]))
    assert np.allclose(hsv[:, 2, :], [123/255, 1, 1])


@pytest.mark.parametrize("hue", [0, "#FF0000", [255, 0, 0], (255, 0, 0)])
def test_fli_get_rgb_1(hue):
    image = np.linspace(.1, .9, 100).reshape(10, 10)
    fi = flblend.FlImage(image=image, hue=hue)
    rgb = fi.get_rgb()
    assert not np.all(rgb[:, :, 0] == 0)
    assert np.all(rgb[:, :, 1] == 0)
    assert np.all(rgb[:, :, 2] == 0)


@pytest.mark.parametrize("hue", [255/3, "#00FF00", [0, 255, 0], (0, 255, 0)])
def test_fli_get_rgb_2(hue):
    image = np.linspace(.1, .9, 100).reshape(10, 10)
    fi = flblend.FlImage(image=image, hue=hue)
    rgb = fi.get_rgb()
    assert np.all(rgb[:, :, 0] == 0)
    assert not np.all(rgb[:, :, 1] == 0)
    assert np.all(rgb[:, :, 2] == 0)


@pytest.mark.parametrize("hue", [255*2/3, "#0000FF", [0, 0, 255], (0, 0, 255)])
def test_fli_get_rgb_3(hue):
    image = np.linspace(.1, .9, 100).reshape(10, 10)
    fi = flblend.FlImage(image=image, hue=hue)
    rgb = fi.get_rgb()
    assert np.all(rgb[:, :, 0] == 0)
    assert np.all(rgb[:, :, 1] == 0)
    assert not np.all(rgb[:, :, 2] == 1)


def test_fli_uint8():
    image = np.linspace(0, 255, 100, dtype=np.uint8).reshape(10, 10)
    fi1 = flblend.FlImage(image=image, hue=0)
    fi2 = flblend.FlImage(image=np.array(image, dtype=float) / 255, hue=0)
    assert np.all(fi1.get_rgb() == fi2.get_rgb())


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
