########################################
# convert.py
#
# (C) Leo Füreder
# licensed to you under the terms of the LGPL, see LICENSE
#
# This tool uses ffmpeg and AtomicParsely, make sure these tools are installed into your $PATH
# Written to accomodate the particularities of the Sony Walkman NW-E394 portable music player
# This is an real-life example of what the database will expect in an program
# The input file is always a .wav file independent of what the database contains
# meta.json and covers.json are always passed as well

import subprocess
import json
from datetime import datetime
import sys


def get_m4a_year(s):
    if s.isdecimal(): 
        return ["--year", s]
    try:
        datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
        return ["--year", s]
    except Exception:
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

input_path = sys.argv[1]
output_path = sys.argv[2]
meta_json = sys.argv[3]
covers_json = sys.argv[4]

for arg_pos, arg in enumerate([input_path, output_path, meta_json, covers_json]):
    if arg is None:
        print(f"Argument {arg_pos} are missing")
        sys.exit(1)

def check_meta(meta):
    if not isinstance(meta, dict): return False
    if "tags" not in meta: return False
    if "version" not in meta: return False
    if "policy" not in meta: return False
    if not isinstance(meta["tags"], dict): return False
    if any(not isinstance(k, str) or not isinstance(v, list) or any(not isinstance(i, str) for i in v) for k, v in meta["tags"].items()): return False
    return True

def check_cover(covers):
    if not isinstance(covers, dict): return False
    if "covers" not in covers: return False
    if "version" not in covers: return False
    if "policy" not in covers: return False
    if any(not isinstance(k, str) or not isinstance(v, str) for k, v in covers["covers"].items()): return False
    return True

class UnexpectedFormatException(Exception):
    pass

try:
    with open(meta_json, "r", encoding="utf-8") as f:
        meta = json.load(f)
        if not check_meta(meta): raise UnexpectedFormatException("the meta.json did not conform to the expected format")
except Exception as e:
    print(f"Parsing of meta.json (arg 3) file failed due to {e}")

try:
    with open(covers_json, "r", encoding="utf-8") as f:
        covers = json.load(f)
        if not check_cover(covers): raise UnexpectedFormatException("the covers.json did not conform to the expected format")
except Exception as e:
    print(f"Parsing of covers.json (arg 4) file failed due to {e}")

meta_policy = meta["policy"]
concat_policy = meta_policy.get("concat", (True, " & "))
concat_char = concat_policy[1] if concat_policy[0] else " & "

covers_policy = covers["policy"]
cover_size = covers_policy.get("size", (150, 150))
mandatory_cover = covers_policy.get("mandatory", [3])[0]
mandatory_cover_path = covers["covers"].get(mandatory_cover, None)

has_cover = mandatory_cover_path is not None

args_list = [
    "ffmpeg",
    "-i",
    input_path,
    "-c:a",
    "aac"
]

if has_cover:
    args_list.extend([
        "-i", 
        mandatory_cover_path,
        "-c:v",
        "mjpeg",
        "-vf",
        f"scale={cover_size[0]}:{cover_size[1]},format=yuv420p",
        "-disposition:v:0",
        "attached_pic",
    ])
else:
    args_list.append("-vn")

args_list.append(output_path)

try:
    subprocess.run(
        args_list,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
except Exception as e:
    print(f"FFmpeg failed due to {e}")
    sys.exit(1)

metadata_args = [
    "AtomicParsely",
    output_path
]

for key, tag_list in meta["tags"].items():
    tag = concat_char.join(tag_list)
    transform = vorbis_mapping.get(key, None)
    if transform:
        cli_params = transform(tag)
        if cli_params:
            metadata_args.extend(cli_params)

try:
    subprocess.run(
        metadata_args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
except Exception as e:
    print(f"AtomicParsely failed due to {e}")
    sys.exit(1)
