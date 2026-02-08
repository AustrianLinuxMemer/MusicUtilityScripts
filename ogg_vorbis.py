########################################
# ogg_vorbis.py
#
# (C) Leo Füreder
# licensed to you under the terms of the LGPL, see LICENSE
#
# This is a sample script to convert any media file into an OGG Vorbis file with embedded cover images
# Modify this script to better suit your needs, it is just an example
# This tool depends on ffmpeg, make sure you have installed this tool into your $PATH

import sys
from io import BytesIO
from typing import Literal

import metaparser
import argparse
import struct
from PIL import Image

def encode_image(input_file, id3_apic: int, resize: tuple[int,int] | None=None, image_format: Literal["JPEG", "PNG"]= "JPEG", description: str | None=None) -> bytes:

    format_to_mime = {
        "JPEG": "image/jpeg".encode("ascii"),
        "PNG": "image/png".encode("ascii")
    }
    if image_format not in format_to_mime:
        raise ValueError("image_format must be JPEG or PNG")
    mode_to_bpp = {
        "1": 1,
        "L": 8,
        "P": 8,
        "RGB": 24,
        "RGBA": 32,
        "CMYK": 32,
        "I": 32,
        "F": 32,
    }
    mime = format_to_mime[image_format]
    description = (description if description is not None else "").encode("utf-8")
    image = Image.open(input_file)
    if resize:
        image = image.resize(resize)
    color_count = len(image.getcolors(maxcolors=image.width*image.height) or []) if image.mode == "P" else 0
    image_bpp = mode_to_bpp.get(image.mode, 0)
    buf = BytesIO()
    image.save(buf, format=image_format)
    buf_value = buf.getvalue()

    buf_2 = BytesIO()
    buf_2.write(struct.pack("<I", id3_apic))
    buf_2.write(struct.pack("<I", len(mime)))
    buf_2.write(mime)
    buf_2.write(struct.pack("<I", len(description)))
    buf_2.write(description)
    buf_2.write(struct.pack("<IIII", image.width, image.height, image_bpp, color_count))
    buf_2.write(struct.pack("<I", len(buf_value)))
    buf_2.write(buf_value)

    return buf_2.getvalue()
