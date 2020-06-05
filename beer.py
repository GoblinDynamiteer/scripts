#!/usr/bin/env python3

import json
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime
from hashlib import sha1
from enum import Enum

from printing import pfcs, fcs

UNTAPPD_DATETIME_FMT = r"%Y-%m-%d %H:%M:%S"


class Beer():
    def __init__(self, name, brewery="Unknown", alc=0.0, beer_type="Unknown"):
        self.name = name
        self.brewery = brewery
        self.alc = alc
        self.type = beer_type
        self.hash = sha1(f"{brewery} {name}".encode("utf-8")).hexdigest()

    def __str__(self):
        return fcs(f"dg[{self.brewery}] - i[{self.name}] ({self.type}, {self.alc} %)")


class CheckIn():
    def __init__(self, date):
        self.date = date


class BeerList():
    class Sorting(Enum):
        Checkins = "checkins"
        BreweryName = "brewery"
        BeerName = "beername"
        ABV = "abv"

    def __init__(self):
        self.list = {}

    def add_beer(self, beer: Beer):
        if beer.hash in self.list:
            return
        self.list[beer.hash] = {"beer": beer, "checkins": []}

    def add_checkin(self, beer: Beer, checkin: CheckIn):
        if beer.hash not in self.list:
            self.add_beer(beer)
        self.list[beer.hash]["checkins"].append(checkin)

    def print_all(self, sort_by=None, reversed_order=False, limit=None):
        count = 0
        if sort_by:
            for item in self.get_sorted_list(sort_by, reverse=reversed_order):
                self.print_beer(item)
                count += 1
                if isinstance(limit, int) and count >= limit:
                    return
        else:
            for _hash in self.list:
                self.print_beer(self.list[_hash])
                count += 1
                if isinstance(limit, int) and count >= limit:
                    return

    def print_beer(self, data):
        print(data["beer"])
        print(f"  check ins: {len(data['checkins'])}")

    def get_sorted_list(self, sort_by, reverse=False):
        hashes = {}
        if sort_by == self.Sorting.Checkins:
            hashes = {_hash: len(data["checkins"])
                      for (_hash, data) in self.list.items()}
        elif sort_by == self.Sorting.ABV:
            hashes = {_hash: data["beer"].alc
                      for (_hash, data) in self.list.items()}
        elif sort_by == self.Sorting.BeerName:
            hashes = {_hash: data["beer"].name
                      for (_hash, data) in self.list.items()}
        elif sort_by == self.Sorting.BreweryName:
            hashes = {_hash: data["beer"].brewery
                      for (_hash, data) in self.list.items()}
        for _hash, _ in sorted(
                hashes.items(),
                reverse=reverse,
                key=lambda item: item[1]):
            yield self.list[_hash]


def init_list(untappd_data):
    beer_list = BeerList()
    for check_in in untappd_data:
        beer_name = check_in.get("beer_name", "")
        brewery = check_in.get("brewery_name", "")
        alc = float(check_in.get(("beer_abv"), 0.0))
        beer_type = check_in.get("beer_type")
        beer = Beer(beer_name, brewery, alc, beer_type)
        date = datetime.strptime(check_in.get(
            "created_at", ""), UNTAPPD_DATETIME_FMT)
        beer_list.add_checkin(beer, CheckIn(date))
    return beer_list


def load_untappd_export(file_path: Path):
    if file_path.is_file():
        with open(file_path) as export_file:
            try:
                return json.load(export_file)
            except Exception as error:
                pfcs(f"e[ERROR]: could not parse file: e[{file_path}]")
                return None
    pfcs(f"e[ERROR]: file does not exist: e[{file_path}]")
    return None


def generate_cli_args():
    parser = ArgumentParser()
    parser.add_argument("--file",
                        "-f",
                        help="Path to Untappd checkin list JSON export file.",
                        default="untappd.json",
                        dest="json_export_file")
    parser.add_argument("--sortby",
                        default=None,
                        choices=[s.value for s in BeerList.Sorting],
                        dest="sort_by")
    parser.add_argument("--limit",
                        default=None,
                        type=int,
                        dest="limit")
    parser.add_argument("--reverse",
                        action="store_true",
                        dest="reverse")
    return parser.parse_args()


def main():
    args = generate_cli_args()
    data = load_untappd_export(Path(args.json_export_file))
    if data is None:
        return
    beer_list = init_list(data)
    # Top 10 most checked in
    beer_list.print_all(sort_by=BeerList.Sorting(args.sort_by),
                        reversed_order=args.reverse,
                        limit=args.limit)


if __name__ == "__main__":
    main()
