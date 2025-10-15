"""
PixelFlow color and brightness adjustments
"""

from PIL import Image, ImageEnhance
import numpy as np


def brightness(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image brightness (1.0 = original, >1.0 = brighter, <1.0 = darker)"""
    # TODO: Replace with actual PixelFlow implementation
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def contrast(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image contrast (1.0 = original, >1.0 = more contrast, <1.0 = less contrast)"""
    # TODO: Replace with actual PixelFlow implementation
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def saturation(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image saturation (1.0 = original, >1.0 = more saturated, <1.0 = less saturated)"""
    # TODO: Replace with actual PixelFlow implementation
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(factor)


def hue_shift(image: Image.Image, shift: int) -> Image.Image:
    """Shift hue by specified amount (-180 to 180)"""
    # TODO: Replace with actual PixelFlow implementation
    # This is a placeholder implementation
    hsv = image.convert('HSV')
    h, s, v = hsv.split()

    h_array = np.array(h)
    h_array = (h_array + shift) % 256

    new_h = Image.fromarray(h_array.astype('uint8'), 'L')
    new_hsv = Image.merge('HSV', (new_h, s, v))
    return new_hsv.convert('RGB')


def grayscale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale"""
    # TODO: Replace with actual PixelFlow implementation
    return image.convert('L').convert('RGB')


def invert(image: Image.Image) -> Image.Image:
    """Invert image colors"""
    # TODO: Replace with actual PixelFlow implementation
    return Image.eval(image, lambda x: 255 - x)