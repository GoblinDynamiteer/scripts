#!/usr/bin/env python3

import argparse
import glob
import json
import re
from pathlib import Path
import abc

import requests
from config import ConfigurationManager
from vid import VideoFileMetadata

from printing import cstr, print_line, Color


class PreSearch(abc.ABC):
    def __init__(self, query: str = ""):
        self._query: str = query
        self._results = []

    @abc.abstractmethod
    def search(self) -> bool:
        return False

    def get_results(self, match=None) -> list:
        if match is not None:
            if not isinstance(match, str):
                return []
            return [r for r in self._results if match in r]
        return self._results

    def set_query(self, query: str):
        self._query = query


class PreDbLiveSearch(PreSearch):
    URL = "https://api.predb.live/api/search"

    def search(self) -> bool:
        if not self._query:
            return False
        resp = requests.post(self.URL, json={"input": self._query, "page": 1})
        if resp.status_code != 200 or not resp.json().get("success", False):
            return False
        _data = resp.json().get("data", {})
        if not _data:
            return False
        return self._parse_response(_data)

    def _parse_response(self, result_data: dict) -> bool:
        _values = result_data.get("values", [])
        if not _values:
            return False
        for result in _values:
            _name = result.get("name", "")
            if _name:
                self._results.append(_name)
        return True if self._results else False


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


def query_from_path(file_path: Path, use_replacement_list=True, use_metadata=False) -> str:
    file_name = run_replace_list_on_query(
        file_path.name) if use_replacement_list else file_path.name
    split_filename = file_name.split(".")
    query = f'{" ".join(split_filename)}'
    if use_metadata:
        metadata = VideoFileMetadata(file_path)
        if metadata.title:
            if " - " in metadata.title:
                query = metadata.title.split(" - ")[1]
    return query


def print_rename_info(src, dst, line=False):
    print("renamed:")
    print(" " * 5, cstr(str(src), Color.Orange))
    print(cstr("--->", "grey"))
    print(" " * 5, cstr(str(dst), Color.LightGreen))
    if line:
        print_line()


def get_args():
    parser = argparse.ArgumentParser(description="Pre Search")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--suffix", type=str, help="add suffix", default="")
    parser.add_argument("-f", "--file", help="use file search mode", action="store_true")
    parser.add_argument("-r", "--rename", help="rename file", action="store_true")
    parser.add_argument("--use-metadata", "-m", action="store_true", dest="use_metadata")
    return parser.parse_args()


def handle_file(cli_args):
    if "*" in cli_args.query:
        items = glob.glob(cli_args.query)
    elif "," in cli_args.query:
        items = cli_args.query.split(",")
    else:
        items = [cli_args.query]
    count = len(items)
    for item in items:
        _path = Path(item).resolve()
        query = query_from_path(_path, use_metadata=cli_args.use_metadata)
        if not query:
            print(f"could not generate query for filename: {_path.name}")
        _search = PreDbLiveSearch(query)
        if not _search.search():
            if cli_args.rename:
                print(f"could not find release, not renaming file {item}")
                continue
            else:
                print(f"could not find release using query: {query}")
                continue
        if cli_args.rename:
            if not _path.exists():
                print(f"found release but {_path} does not exist, will not rename...")
                continue
            _results = _search.get_results(match="1080p")
            if not _results:
                print(f"could not find any 1080p releases for {_path.name}")
            new_file_name = _results[0]
            if not new_file_name.endswith(_path.suffix):
                new_file_name = new_file_name + _path.suffix
            _path.rename(new_file_name)
            print_rename_info(_path, new_file_name, line=count > 1)
        else:
            print("results:")
            for _result in _search.get_results():
                print(_result)


def main():
    args = get_args()
    if args.file:
        handle_file(cli_args=args)
    else:
        _search = PreDbLiveSearch(args.query)
        if _search.search():
            for name in _search.get_results():
                print(name + args.suffix)
        else:
            print("could not find release")


if __name__ == "__main__":
    main()
