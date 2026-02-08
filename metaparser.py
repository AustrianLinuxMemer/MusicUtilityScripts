########################################
# metaparser.py
#
# (C) Leo Füreder
# licensed to you under the terms of the LGPL, see LICENSE
#
# This is one implementation that is used to parse the JSON arguments
# Used by nw_e394.py and ogg_vorbis.py

import json
import sys

from collections.abc import Sequence


class UnexpectedFormatException(Exception):
    pass

def check_meta(meta, default_policy):
    if not isinstance(meta, dict): raise UnexpectedFormatException("the meta.json must be an object")
    if not isinstance(default_policy, dict): raise UnexpectedFormatException("the default policy for the meta.json must be an object")
    try:
        version = meta["version"]
        tags = meta["tags"]
        policy = meta.get("policy", default_policy)
        if not isinstance(policy, dict): raise UnexpectedFormatException("The policy object must be an object")
        if not isinstance(version, str): raise UnexpectedFormatException("The version string must be a string")
        if not isinstance(tags, dict): raise UnexpectedFormatException("The tags object must be a dictionary")
        for k, v in tags.items():
            if not isinstance(k, str): raise UnexpectedFormatException("the key must be a string")
            if not isinstance(v, list): raise UnexpectedFormatException("the value must be a list")
            if any(not isinstance(e, str) for e in v): raise UnexpectedFormatException("all values in the value list must be strings")
    except KeyError:
        raise UnexpectedFormatException("The meta.json must contain following keys: `version`, `tags`")

def correct_size(size: Sequence[int] | int | None, default_size: Sequence[int]) -> tuple[int, int]:
    if not isinstance(default_size, Sequence): raise UnexpectedFormatException("the default size must be a sequence")
    if any(not isinstance(v, int) for v in default_size): raise UnexpectedFormatException("all values in the default size must be integers")
    if len(default_size) != 2: raise UnexpectedFormatException("the default size must consist of two elements")
    if size is None: return default_size[0], default_size[1]
    if isinstance(size, int): return size, size
    if not isinstance(size, Sequence): raise UnexpectedFormatException("the size must be a sequence")
    if len(size) == 0:
        return default_size[0], default_size[1]
    elif len(size) == 1:
        if not isinstance(size[0], int):
            raise UnexpectedFormatException("the first element of must be an integer")
        else:
            return size[0], size[0]
    elif len(size) == 2:
        if not isinstance(size[0], int):
            raise UnexpectedFormatException("the first element must be an integer")
        if not isinstance(size[1], int):
            size = size[0], size[0]
        return size[0], size[1]
    else:
        raise UnexpectedFormatException("the size must consist of two elements")

def check_cover_entry(key: int, entry: dict, default_size: Sequence):
    if not isinstance(key, int): raise UnexpectedFormatException("the cover key must be an integer")
    if not isinstance(entry, dict): raise UnexpectedFormatException("the cover entry must be an object")
    try:
        path = entry["path"]
        if not isinstance(path, str): raise UnexpectedFormatException("the path must be a string")
        size = entry.get("size", None)
        entry["size"] = correct_size(size, default_size)
    except KeyError:
        raise UnexpectedFormatException("The cover entry must contain a `path` key")
def check_default_size(default_size):
    if not isinstance(default_size, Sequence): raise UnexpectedFormatException("the default size must be a sequence")
    if len(default_size) != 2: raise UnexpectedFormatException("the default size must contain two elements")
    if any(not isinstance(e, int) for e in default_size): raise UnexpectedFormatException("all values in the default size must be integers")

def check_cover(covers, default_policy: dict):
    if not isinstance(covers, dict): raise UnexpectedFormatException("the covers.json must be an object")
    if not isinstance(default_policy, dict): raise UnexpectedFormatException("the default policy must be an object and is required")
    try:
        version = covers["version"]
        if not isinstance(version, str): raise UnexpectedFormatException("the version must be a string")
        cover_dict = covers["covers"]
        policy = covers.get("policy", default_policy)
        default_size = policy.get("size", default_policy["size"])
        check_default_size(default_size)
        for k, v in cover_dict.items():
            try:
                if not k.isdigit():
                    raise UnexpectedFormatException(f"the key `{k}` must be an integer")
                else:
                    check_cover_entry(int(k), v, default_size)
            except ValueError:
                raise UnexpectedFormatException(f"the key `{k}` must be an integer")
    except KeyError:
        raise UnexpectedFormatException("the covers.json must contain the keys `version` and `covers`")


def parse_meta_json(meta_json, default_policy):
    try:
        with open(meta_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
            check_meta(meta, default_policy)
            return meta
    except Exception as e:
        print(f"Parsing of meta.json (arg 3) file failed due to {e}", file=sys.stderr)
        raise

def parse_cover_json(covers_json, default_policy):
    try:
        with open(covers_json, "r", encoding="utf-8") as f:
            covers = json.load(f)
            check_cover(covers, default_policy)
            return covers
    except Exception as e:
        print(f"Parsing of covers.json (arg 4) file failed due to {e}", file=sys.stderr)
        raise