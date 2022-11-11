#!/usr/bin/env python3

import argparse
import glob
import json
import re
from pathlib import Path
import abc
from typing import List

import requests
from config import ConfigurationManager
from vid import VideoFileMetadata
from base_log import BaseLog
from printout import cstr, print_line, Color, fcs
from bs4 import BeautifulSoup


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


class PreDbOrgSearch(PreSearch, BaseLog):
    URL = "https://predb.org/search"

    def __init__(self, query: str = "", verbose=False):
        PreSearch.__init__(self, query)
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("PREDB_ORG")

    def search(self) -> bool:
        if not self._query:
            self.error("search: query missing")
            return False
        self.log(fcs(f"search: using query i[{self._query}]"))
        _url = self.URL
        resp = requests.get(_url, params={"searchstr": self._query, "searchcat": "all"})
        if resp.status_code != 200:
            self.error("search: get request failed")
            return False
        if not resp.text:
            return False
        return self._parse_response(resp.text)

    def _parse_response(self, result_html: str) -> bool:
        soup = BeautifulSoup(result_html, "html.parser")
        main_table = soup.find("table", attrs={"class": "table table-condensed"})
        main_table_body = main_table.find("tbody")
        for row in main_table_body.findAll("tr"):
            rel = row.find("th")
            self._results.append(rel.text)
        if self._results:
            self.log(f"search: got {len(self._results)} result(s)")
            return True
        self.warn("search: no results")
        return False


class PreDbMeSearch(PreSearch, BaseLog):
    URL = "https://predb.me/?search="

    def __init__(self, query: str = "", verbose=False):
        PreSearch.__init__(self, query)
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("PREDB_ME")

    def search(self) -> bool:
        if not self._query:
            self.error("search: query missing")
            return False
        self.log(fcs(f"search: using query i[{self._query}]"))
        resp = requests.get(self.URL, params={})
        if resp.status_code != 200 or not resp.json().get("success", False):
            self.error("search: get request failed")
            return False
        _data = resp.json().get("data", {})
        if not _data:
            self.error("search: no data in result")
            return False
        return self._parse_response(_data)

    def _parse_response(self, result_data: dict) -> bool:
        _values = result_data.get("values", [])
        if not _values:
            self.error("search: no data in result")
            return False
        for result in _values:
            _name = result.get("name", "")
            if _name:
                self._results.append(_name)
        if self._results:
            self.log(f"search: got {len(self._results)} result(s)")
            return True
        self.warn("search: no results")
        return False


class PreDbLiveSearch(PreSearch, BaseLog):
    URL = "https://api.predb.live/api/search"

    def __init__(self, query: str = "", verbose=False):
        PreSearch.__init__(self, query)
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("PREDB_LIVE")

    def search(self) -> bool:
        if not self._query:
            self.error("search: query missing")
            return False
        self.log(fcs(f"search: using query i[{self._query}]"))
        resp = requests.post(self.URL, json={"input": self._query, "page": 1})
        if resp.status_code != 200 or not resp.json().get("success", False):
            self.error("search: post request failed")
            return False
        _data = resp.json().get("data", {})
        if not _data:
            self.error("search: no data in result")
            return False
        return self._parse_response(_data)

    def _parse_response(self, result_data: dict) -> bool:
        _values = result_data.get("values", [])
        if not _values:
            self.error("search: no data in result")
            return False
        for result in _values:
            _name = result.get("name", "")
            if _name:
                self._results.append(_name)
        if self._results:
            self.log(f"search: got {len(self._results)} result(s)")
            return True
        self.warn("search: no results")
        return False


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
    return query.replace("-", " ")


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
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose logging")
    return parser.parse_args()


def args_to_file_paths(file_arg: str, assert_exists: bool = True) -> List[Path]:
    if "*" in file_arg:
        items = glob.glob(file_arg)
    elif "," in file_arg:
        items = file_arg.split(",")
    else:
        items = [file_arg]
    _ret = []
    for item in items:
        _p = Path(item)
        if assert_exists and not _p.is_file():
            raise FileNotFoundError(f"File does not exist: {_p.resolve()}")
        _ret.append(_p)
    return _ret


def handle_files(files: List[Path], cli_args: argparse.Namespace):
    log = BaseLog(verbose=True)
    log.set_log_prefix("FILE")
    count = len(files)
    for file_path in files:
        query = query_from_path(file_path, use_metadata=cli_args.use_metadata)
        if not query:
            log.error(f"could not generate query for filename: {file_path.name}")
        _search = PreDbOrgSearch(query, verbose=cli_args.verbose)
        if not _search.search():
            if cli_args.rename:
                log.warn(f"could not find release, not renaming file {file_path.name}")
                continue
            else:
                log.warn(f"could not find release using query: {query}")
                continue
        if cli_args.rename:
            if not file_path.exists():
                log.warn(f"found release but {file_path} does not exist, will not rename...")
                continue
            if ".4k." in file_path.name:
                _results = _search.get_results(match="2160p")
            else:
                _results = _search.get_results(match="1080p")
            if not _results:
                log.warn(f"could not find any releases with correct resolution for {file_path.name}")
            new_file_name = _results[0]
            if not new_file_name.endswith(file_path.suffix):
                new_file_name = new_file_name + file_path.suffix
            file_path.rename(new_file_name)
            print_rename_info(file_path, new_file_name, line=count > 1)
        else:
            log.log("results:")
            for _result in _search.get_results():
                print(" " * 5, _result)


def main():
    args = get_args()
    if args.file:
        handle_files(args_to_file_paths(args.query), cli_args=args)
    else:
        _search = PreDbOrgSearch(args.query, args.verbose)
        if _search.search():
            for name in _search.get_results():
                print(name + args.suffix)
        else:
            print("could not find release")


if __name__ == "__main__":
    main()
