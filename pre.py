#!/usr/bin/env python3

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import requests
from config import ConfigurationManager
from vid import VideoFileMetadata

from printing import cstr, print_line


def run_replace_list_on_query(query_string):
    replace_file_path = Path(ConfigurationManager().path("scripts")) / "pre_replace.json"
    with open(replace_file_path) as replace_fp:
        _list = json.load(replace_fp)
        if not _list:
            return query_string
        for string, replacement in _list.items():
            if "^" in string:
                query_string = re.sub(string, replacement, query_string)
            else:
                query_string = query_string.replace(string, replacement)
    return query_string


def pre_search(query: str) -> [list, False]:
    json_response = requests.get(
        f"https://predb.ovh/api/v1/?q={query}&count=50")
    try:
        data = json.loads(json_response.text)
        if data.get("status", "") == "error":
            print(f"got error: {data.get('message', 'N/A')}")
            return False
        rows = data["data"]["rows"]
    except json.decoder.JSONDecodeError:
        print(f"got json decoder error! on query: {query}")
        print(json_response)
        return False
    return [row["name"] for row in rows]


def pre_search_from_file(file_path: Path, use_replacement_list=True, use_metadata=False) -> str:
    file_name = run_replace_list_on_query(
        file_path.name) if use_replacement_list else file_path.name
    split_filename = file_name.split('.')
    query = f'{" ".join(split_filename)}'
    if use_metadata:
        metadata = VideoFileMetadata(file_path)
        if metadata.title:
            if " - " in metadata.title:
                query = metadata.title.split(" - ")[1]
    results = pre_search(query)
    if results:
        for result in results:
            if "1080p" in result:  # prefer 1080p results
                return result
        return results[0]
    return ""


def print_rename_info(src, dst, line=False):
    src_c = cstr(str(src), "orange")
    dst_c = cstr(str(dst), "lgreen")
    print("renamed:")
    print(" " * 5, src_c,)
    print(cstr("--->", "grey"))
    print(" " * 5, dst_c)
    if line:
        print_line()


def get_args():
    parser = argparse.ArgumentParser(description="Pre Search")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--suffix", type=str, help="add suffix", default="")
    parser.add_argument("-f", "--file", help="use file search mode", action="store_true")
    parser.add_argument("-r", "--rename", help="rename file", action="store_true")
    parser.add_argument("-p", "--use-parent", action="store_true", dest="use_parent")
    parser.add_argument("--use-metadata", "-m", action="store_true", dest="use_metadata")
    return parser.parse_args()


def main():
    args = get_args()
    if args.file:
        if "*" in args.query:
            items = glob.glob(args.query)
        elif "," in args.query:
            items = args.query.split(",")
        else:
            items = [args.query]
        count = len(items)
        for item in items:
            file_name = Path(item).resolve()
            if args.use_parent:
                sys.exit()
            ret = pre_search_from_file(
                file_name, use_metadata=args.use_metadata)
            if not ret:
                if args.rename:
                    print(f"could not find release, not renaming file {item}")
                    sys.exit(1)
                else:
                    print("could not find release")
                    sys.exit(1)
            print(ret + args.suffix)
            if args.rename:
                if not file_name.exists():
                    print(f"found release but {file_name} does not exist, will not rename...")
                    sys.exit(1)
                new_file_name = ret
                if not ret.endswith(file_name.suffix):
                    new_file_name = ret + file_name.suffix
                file_name.rename(new_file_name)
                print_rename_info(file_name, new_file_name, line=count > 1)
    else:
        ret = pre_search(args.query)
        if not ret:
            print("could not find release")
        else:
            for name in ret:
                print(name + args.suffix)


if __name__ == "__main__":
    main()
