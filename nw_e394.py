########################################
# nw_e394.py
#
# (C) Leo Füreder
# licensed to you under the terms of the LGPL, see LICENSE
#
# This tool uses ffmpeg and AtomicParsely, make sure these tools are installed into your $PATH
# Written to accommodate the particularities of the Sony Walkman NW-E394 portable music player
# This is a real-life example of what the database will expect in a program
# The input file is always a .wav file independent of what the database contains
# meta.json and covers.json are always passed as well


import os
import subprocess
import tempfile
from datetime import datetime
import sys
from typing import Sequence
import argparse
import metaparser
def get_m4a_year(s):
    if s.isdecimal(): 
        return ["--year", s]
    try:
        datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
        return ["--year", s]
    except ValueError:
        return None

def get_tracknum(s):
    if s.isdecimal(): 
        return ["--tracknum", s] 
    else: 
        return None

vorbis_mapping = {
    "TITLE": lambda s: ["--title", s],
    "ALBUM": lambda s: ["--album", s],
    "TRACKNUMBER": get_tracknum,
    "ARTIST": lambda s: ["--artist", s],
    "COPYRIGHT": lambda s: ["--copyright", s],
    "DESCRIPTION": lambda s: ["--description", s],
    "GENRE": lambda s: ["--genre", s],
    "DATE": get_m4a_year,
}

def format_cover(cover_file_in: str, cover_file_out: str, dimension: Sequence[int]=(150, 150)):
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                cover_file_in,
                "-c:v",
                "mjpeg",
                "-vf",
                f"scale={dimension[0]}:{dimension[1]},format=yuv420p",
                "-map_metadata",
                "-1",
                "-map_chapters",
                "-1",
                cover_file_out
             ],
            text=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    except Exception as e:
        print(f"Conversion to JPEG failed due to {e}", file=sys.stderr)
        sys.exit(1)

def make_audio(input_file: str, output_file: str):
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                input_file,
                "-c:a",
                "aac",
                "-vn",
                "-map_metadata",
                "-1",
                "-map_chapters",
                "-1",
                output_file
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True)
    except Exception as e:
        print(f"Conversion to M4A file failed due to {e}", file=sys.stderr)
        sys.exit(1)

def attach_tags(output_file: str, tags: dict[str, list[str]], concat_str: str):
    atomic_parsely_command = [
        "AtomicParsley",
        output_file,
        "--overWrite",
        "--encodingTool",
        "",
        "--encodedBy",
        ""
    ]
    for key, tag_list in tags.items():
        tag = concat_str.join(tag_list)
        key = key.upper()
        transform = vorbis_mapping.get(key, None)
        if transform:
            cli_params = transform(tag)
            if cli_params:
                atomic_parsely_command.extend(cli_params)
    try:
        subprocess.run(
            atomic_parsely_command,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
    except Exception as e:
        print(f"Tagging with AtomicParsley failed due to {e}", file=sys.stderr)
        sys.exit(1)

def attach_cover(output_file: str, cover_file: str):
    atomic_parsely_command = [
        "AtomicParsley",
        output_file,
        "--overWrite",
        "--artwork",
        cover_file
    ]
    try:
        subprocess.run(
            atomic_parsely_command,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
    except Exception as e:
        print(f"Attaching cover art with AtomicParsley failed due to {e}", file=sys.stderr)
        sys.exit(1)


class UnexpectedFormatException(Exception):
    pass

arg_parser = argparse.ArgumentParser("Convert any media file into a Walkman NW-E394 compatible M4A file")

arg_parser.add_argument("input_file", help="Input file")
arg_parser.add_argument("output_file", help="Output file")
arg_parser.add_argument("meta_json", nargs="?", default=None, help="Meta JSON file")
arg_parser.add_argument("covers_json", nargs="?", default=None, help="Covers JSON file")

args = arg_parser.parse_args()

if args.meta_json:
    meta = metaparser.parse_meta_json(args.meta_json, {"concat": (True, " & ")})
    meta_policy = meta["policy"]
    concat_policy = meta_policy.get("concat", (True, " & "))
    concat_char = concat_policy[1] if concat_policy[0] else " & "
else:
    meta = None
    concat_char = None

if args.covers_json:
    covers = metaparser.parse_cover_json(args.covers_json, {"size": (150, 150)})
    covers_policy = covers["policy"]
    mandatory_cover_apic = covers_policy.get("mandatory", ["3"])[0]
    mandatory_cover = covers["covers"].get(mandatory_cover_apic, None)
    has_cover = mandatory_cover is not None
else:
    has_cover = False
    mandatory_cover = None

input_path = args.input_file
output_path = args.output_file
with tempfile.TemporaryDirectory() as tmp_dir:
    make_audio(input_path, output_path)
    if has_cover:
        tmp_jpeg = os.path.join(tmp_dir, "tmp.jpeg")
        format_cover(mandatory_cover["path"], tmp_jpeg, mandatory_cover["size"])
        attach_cover(output_path, tmp_jpeg)
    else:
        print("No covers attached")
    if meta is not None:
        attach_tags(output_path, meta, concat_char)
    else:
        print("No tags attached")