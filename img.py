#!/usr/bin/env python3.6

""" Image Tools """

from enum import IntEnum

from printing import pfcs
import util

try:
    from PIL import Image
except ImportError:
    pfcs(f'Pillow library is needed for w[{__file__}]')
    exit()


class ImageOrientation(IntEnum):
    Landscape = 0
    Portrait = 1
    Square = 2


def image_size(path_to_image: str)->tuple:
    if not util.is_file(path_to_image):
        pfcs(f'image file e[{path_to_image}] does not exist!')
        return None
    with Image.open(path_to_image) as image:
        return image.size
    return None


def image_heigh(path_to_image: str)->int:
    return image_size(path_to_image)[1]


def image_width(path_to_image: str)->int:
    return image_size(path_to_image)[0]


def image_orientation(path_to_image: str)-> ImageOrientation:
    width, height = image_size(path_to_image)
    if width > height:
        return ImageOrientation.Landscape
    if height > width:
        return ImageOrientation.Portrait
    return ImageOrientation.Square
