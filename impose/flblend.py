"""Blend fluorescence image channels for visualization"""
import numbers
import warnings

import numpy as np
from skimage.color import gray2rgb, hsv2rgb, rgb2hsv
from skimage.exposure import rescale_intensity


class NoImageDataWarning(UserWarning):
    pass


class FlBlend:
    def __init__(self):
        self.images = []

    def __len__(self):
        return len(self.images)

    @property
    def shape(self):
        if self.images:
            return self.images[0].shape
        else:
            return None

    def add_image(self, image, hue, brightness=127, contrast=127,
                  autocontrast=True):
        """Add a new image

        Parameters
        ----------
        image: 2d ndarray
            Image data, dtype should be uint8 (values between 0 and 255)
            or float (values between 0 and 1)
        hue: float or str or RGB tuple/list/ndarray
            The color hue; If a number, must be between 0 and
            255; If a string, must be a hex color value; Otherwise
            must be an RGB color tuple/list/array.
        brightness: float
            Brightness; value between 0 and 255
        contrast: float
            Contrast; value between 0 and 255
        autocontrast: bool
            Automatically sets the contrast (histogram based
            between 1% and 99% of image data)
        """
        assert len(image.shape) == 2
        if autocontrast:
            values_to_bin = image[~np.isnan(image)]
            # only perform histogram analysis if whe have data
            if values_to_bin.size:
                hist, edges = np.histogram(values_to_bin,
                                           bins=int(np.sqrt(image.size)),
                                           density=True)
                shist = np.cumsum(hist) / np.nansum(hist)
                amin = np.argmin(np.abs(shist - .01))
                amax = np.argmin(np.abs(shist - .99))
                vmin = edges[amin]
                vmax = edges[amax]
                # scale to interval [0, 1]
                image = rescale_intensity(image, in_range=(vmin, vmax),
                                          out_range=(0, 1))
        flim = FlImage(image=image,
                       hue=hue,
                       contrast=contrast,
                       brightness=brightness)
        self.images.append(flim)

    def blend(self, mode="hsv"):
        if len(self) == 0:
            warnings.warn("No image data available for blending!",
                          NoImageDataWarning)
            image = np.zeros((2, 2))
        elif len(self) == 1:
            # single images do not need blending
            image = self.images[0].get_rgb()
        else:
            if mode == "hsv":
                image = self.blend_hsv()
            else:
                image = self.blend_rgb()

        return image

    def blend_rgb(self):
        """Return image from RGB blending

        Returns
        -------
        blend_rgb: 3d ndarray
            RGB image with values between 0 and 1 if brightness or
            contrast were not modified (only normalization by number
            of individual images; The last axis iterates over RGB
        """
        shape = self.shape
        stack_r = np.zeros((shape[0], shape[1], len(self)), dtype=float)
        stack_g = np.zeros((shape[0], shape[1], len(self)), dtype=float)
        stack_b = np.zeros((shape[0], shape[1], len(self)), dtype=float)
        # We use this array to track the number of valid images pixel-wise
        # (we have to use float here, since np.nan only exists for floats)
        # This is necessary so we can correctly account for NaN values
        # that might occur e.g. for Brillouin data.
        # See https://github.com/GuckLab/impose/issues/25 for more background.
        stack_v = np.zeros((shape[0], shape[1], len(self)), dtype=float)

        for ii, flim in enumerate(self.images):
            rgb = flim.get_rgb()
            stack_r[:, :, ii] = rgb[:, :, 0]
            stack_g[:, :, ii] = rgb[:, :, 1]
            stack_b[:, :, ii] = rgb[:, :, 2]
            stack_v[:, :, ii] = np.invert(np.isnan(rgb[:, :, 0]))

        # Get the number of valid images per pixel for later normalization
        norm_v = np.nansum(stack_v, axis=2)
        # Zero-valued pixels means all images were NaN at that pixel
        norm_v[norm_v == 0] = np.nan

        merged = np.zeros((shape[0], shape[1], 3), dtype=float)
        merged[:, :, 0] = np.nansum(stack_r, axis=2) / norm_v
        merged[:, :, 1] = np.nansum(stack_g, axis=2) / norm_v
        merged[:, :, 2] = np.nansum(stack_b, axis=2) / norm_v

        return merged

    def blend_hsv(self):
        """Return image from RGB blending

        Returns
        -------
        blend_hsv: 3d ndarray
            RGB image with HSV-blending via hue angles; The last axis
            iterates over RGB
        """
        shape = self.shape

        stack_s = np.zeros((shape[0], shape[1], len(self)), dtype=float)
        stack_v = np.zeros((shape[0], shape[1], len(self)), dtype=float)
        stack_xh = np.zeros((shape[0], shape[1], len(self)), dtype=float)
        stack_yh = np.zeros((shape[0], shape[1], len(self)), dtype=float)

        for ii, flim in enumerate(self.images):
            hsv = flim.get_hsv()
            stack_s[:, :, ii] = hsv[:, :, 1] * hsv[:, :, 2]
            stack_v[:, :, ii] = hsv[:, :, 2]
            stack_xh[:, :, ii] = np.cos(
                (hsv[:, :, 0]) * 2 * np.pi) * np.abs(hsv[:, :, 2])
            stack_yh[:, :, ii] = np.sin(
                (hsv[:, :, 0]) * 2 * np.pi) * np.abs(hsv[:, :, 2])

        merged_hsv = np.zeros((shape[0], shape[1], 3), dtype=float)

        stack_havg = np.arctan2(
            np.nanmean(stack_yh, axis=2),
            np.nanmean(stack_xh, axis=2)) / 2 / np.pi % 1

        valid = np.nansum(stack_v, axis=2) != 0
        sat = np.nansum(stack_s, axis=2)
        sat[valid] = np.nansum(stack_v, axis=2)[valid]
        sat /= np.nanmax(sat)

        merged_hsv[:, :, 0] = stack_havg
        merged_hsv[:, :, 1] = 1-sat
        merged_hsv[:, :, 2] = np.nanmean(stack_v, axis=2)

        return hsv2rgb(merged_hsv)


class FlImage:
    def __init__(self, image, hue, contrast=127.0, brightness=127.0):
        """Image instance used for blending

        Parameters
        ----------
        image: 2d ndarray
            Image data, dtype should be uint8 (values between 0 and 255)
            or float (values between 0 and 1)
        hue: float or str or RGB tuple/list/ndarray
            The color hue; If a number, must be between 0 and
            255; If a string, must be a hex color value; Otherwise
            must be an RGB color tuple/list/array.
        brightness: float
            Brightness; value between 0 and 255
        contrast: float
            Contrast; value between 0 and 255
        """
        if image.dtype == np.dtype(np.uint8):
            # convert image to float in range [0, 1]
            image = image / 255
        self.image = image
        #: Hue (RGB triple with values from 0 to 255)
        self.hue_rgb = self.colorhue2rgb(hue)
        #: Contrast (0 - 255)
        self.contrast = contrast
        #: Brightness (0 - 255)
        self.brightness = brightness

    @staticmethod
    def colorhue2rgb(hue):
        """Convert color hue to RGB"""
        if isinstance(hue, str):
            rgb = FlImage.hex2rgb(hue)
        elif isinstance(hue, numbers.Number):
            rgb = hsv2rgb([hue/255, 1., 1.])
        elif isinstance(hue, (np.ndarray, list, tuple)):
            rgb = np.array(hue, dtype=float) / 255
        else:
            raise ValueError(f"Unrecognized hue value or type: '{hue}'!")
        hsv = rgb2hsv(np.array(rgb))
        hsv[1] = 1
        hsv[2] = 1
        return hsv2rgb(hsv).tolist()

    @staticmethod
    def hex2rgb(hex_string):
        color = hex_string.strip("#")
        r = int(color[:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return [r, g, b]

    @property
    def shape(self):
        return self.image.shape[0], self.image.shape[1]

    def get_rgb(self):
        """Return RGB image as a 3d ndarray

        Returns
        -------
        image_rgb: 3d ndarray
            Unnormalized RGB image (if contrast and brightness were
            not modified, then the image values are always between
            0 and 1); Last axis iterates over RGB
        """
        # contrast: do not allow zero brightness (offset 1 from zero)
        # runs from 2/256 to 2
        con = 2 * (self.contrast + 1) / 256
        # brightness
        # runs from -127/256 to 1/2
        bri = (self.brightness - 127) / 256
        bim = con * self.image + bri
        image_rgb = gray2rgb(bim)
        # apply hue
        image_rgb[:, :, 0] *= self.hue_rgb[0]
        image_rgb[:, :, 1] *= self.hue_rgb[1]
        image_rgb[:, :, 2] *= self.hue_rgb[2]
        return image_rgb

    def get_hsv(self):
        rgb = self.get_rgb()
        image_hsv = rgb2hsv(rgb)
        # rgb2hsv sets NaN values to zero
        # which we revert here
        image_hsv[np.isnan(rgb)] = np.nan
        return image_hsv
