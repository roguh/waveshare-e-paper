#!/usr/bin/env python3
import os
import sys
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter,ImageChops

GENERATED_DIRECTORY = "./roguh_pics/generated/"

# 104px is the width of my 2.13 inch e-paper
DEFAULT_NEW_WIDTH = 104

BLACK = 25
WHITE = 255 - BLACK


def enhance(input_img: Image.Image) -> Image.Image:
    preprocessed_img = ImageEnhance.Color(
        ImageEnhance.Sharpness(input_img).enhance(100.0)
    ).enhance(10)
    preprocessed_img = preprocessed_img.filter(ImageFilter.MinFilter(3))
    return preprocessed_img


def save_to_2color(
    input_img: Image.Image,
    out_fname: str,
    white_threshold: int = 128,
    black_threshold: Optional[int] = None,
) -> None:
    def pixel_filter(pixel256: int) -> bool:
        if pixel256 > white_threshold:
            return False
        if black_threshold is not None:
            if pixel256 < black_threshold:
                return False
        return True

    out_img = input_img.convert("L").point(pixel_filter, mode="1")
    out_img.save(out_fname)

    with open(out_fname.replace(".png", ".raw"), "wb") as rawout:
        rawout.write(out_img.tobytes())


def convert_to_3color(in_fname: str, new_width: int = DEFAULT_NEW_WIDTH) -> None:
    os.makedirs(GENERATED_DIRECTORY, exist_ok=True)
    base_fname = os.path.basename(in_fname)
    black_fname = os.path.join(GENERATED_DIRECTORY, base_fname.replace(".png", ".black.png"))
    red_fname = os.path.join(GENERATED_DIRECTORY, base_fname.replace(".png", ".red.png"))
    resized_fname = os.path.join(GENERATED_DIRECTORY, base_fname.replace(".png", f".resized{new_width}.png"))

    img = Image.open(in_fname)

    shrunken_img = img.resize(
        (new_width, int(img.size[1] * new_width / img.size[0])),
        Image.Resampling.NEAREST,
    )
    shrunken_img.save(resized_fname)

    save_to_2color(shrunken_img, black_fname, WHITE)
    save_to_2color(shrunken_img, red_fname, WHITE, black_threshold=BLACK)


if __name__ == "__main__":
    convert_to_3color(sys.argv[1])
