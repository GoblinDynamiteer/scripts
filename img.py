#!/usr/bin/env python3

""" Image Tools """

from enum import IntEnum

from printout import pfcs
from pathlib import Path
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


def image_size(path_to_image: str) -> tuple:
    if not util.is_file(path_to_image):
        pfcs(f'image file e[{path_to_image}] does not exist!')
        return None
    with Image.open(path_to_image) as image:
        return image.size
    return None


def image_heigh(path_to_image: str) -> int:
    return image_size(path_to_image)[1]


def image_width(path_to_image: str) -> int:
    return image_size(path_to_image)[0]


def image_resize(path_to_image: str, width: int, heigh: int, new_file_name: None) -> bool:
    if not util.is_file(path_to_image):
        pfcs(f'image file e[{path_to_image}] does not exist!')
        return False
    old_img_path = Path(path_to_image)
    if not new_file_name:
        new_file_name = old_img_path.name.replace(
            old_img_path.suffix, "") + "_resized" + old_img_path.suffix
    elif isinstance(new_file_name, str):
        resized_img_path = Path(old_img_path.parent) / new_file_name
    elif isinstance(new_file_name, Path):
        resized_img_path = new_file_name
    else:
        pfcs(f'cannot determine output filename of'
             f'resized version of e[{path_to_image}]!')
        return False
    if util.is_file(resized_img_path):
        pfcs(f'output filename e[{resized_img_path}] already exist!')
        return False
    with Image.open(old_img_path) as image:
        resized_image = image.copy()
        resized_image.thumbnail((width, heigh))
        resized_image.save(resized_img_path)
        return True


def image_orientation(path_to_image: str) -> ImageOrientation:
    width, height = image_size(path_to_image)
    if width > height:
        return ImageOrientation.Landscape
    if height > width:
        return ImageOrientation.Portrait
    return ImageOrientation.Square
