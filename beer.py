#!/usr/bin/env python3

import json
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime
from hashlib import sha1
from enum import Enum

from printing import pfcs, fcs

UNTAPPD_DATETIME_FMT = r"%Y-%m-%d %H:%M:%S"
ARG_DATE_FMT = r"%Y-%m-%d"


def filenameify(string):
    string = string.lower()
    rep_list = [
        (".", ""),
        ("&", "and"),
        ("å", "a"),
        ("ä", "a"),
        ("ö", "o"),
        ("/", "-"),
        ("--", "-"),
        ("(", " "),
        (" - ", "-"),
        (")", " "),
        ("é", "e"),
        ("  ", " ")  # must be last
    ]
    for search, rep in rep_list:
        string = string.replace(search, rep)
    string = string.strip()
    return string.replace(" ", "_")


def parse_arg_date(arg_date):
    if arg_date:
        try:
            return datetime.strptime(arg_date, ARG_DATE_FMT)
        except TypeError:
            pfcs(f"could not parse --date filter: e[{arg_date}]")
            return None
        except ValueError:
            pfcs(f"wrong format for --date filter: e[{arg_date}]")
            return None
    return None


def parse_arg_sorting(arg_sort):
    try:
        return BeerList.Sorting(arg_sort) if arg_sort else None
    except Exception:
        return None


class Beer:
    def __init__(self, name, brewery="Unknown", alc=0.0, beer_type="Unknown"):
        self.name = name
        self.brewery = brewery
        self.alc = alc
        self.type = beer_type
        self.hash = sha1(f"{brewery} {name}".encode("utf-8")).hexdigest()

    def __str__(self):
        return fcs(f"dg[{self.brewery}] - i[{self.name}]"
                   f" ({self.type}, o[{self.alc} %])")

    def filename(self, extension=".jpg"):
        return f"{filenameify(self.brewery)}-{filenameify(self.name)}{extension}"


class CheckIn:
    class Location:
        def __init__(self, venue=None, city=None):
            self.venue = venue
            self.city = city

        def __str__(self):
            ret_str = ""
            if self.venue is not None:
                ret_str = self.venue
            if self.city is not None:
                ret_str += f" / {self.city}"
            return ret_str

        def valid(self):
            if self.venue is None and self.city is None:
                return False
            return True

    def __init__(self, date, venue=None, city=None):
        self.date = date
        self.location = self.Location(venue, city)

    def __str__(self):
        if self.location.valid():
            return fcs(f"dg[{self.date}] @ {self.location}")
        return fcs(f"dg[{self.date}]")


class BeerList:
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

    def print_list(self, cli_args, sort_by):
        count = 0
        for item in self.get_sorted_list(sort_by, reverse=cli_args.reverse):
            if self.print_beer(item, cli_args):
                count += 1
            if isinstance(cli_args.limit, int) and count >= cli_args.limit:
                return

    def print_beer(self, data, cli_args):
        beer_obj = data["beer"]
        filter_name = cli_args.filter
        matched = False
        if filter_name and filter_name.lower() in beer_obj.name.lower():
            matched = True
        if filter_name and filter_name.lower() in beer_obj.brewery.lower():
            matched = True
        if filter_name and not matched:
            return False
        date_filter = parse_arg_date(cli_args.date)
        if date_filter:
            found_match = False
            for checkin_obj in data["checkins"]:
                if checkin_obj.date.date() == date_filter.date():
                    found_match = True
            if not found_match:
                return False
        print(beer_obj)
        num_checkins = len(data["checkins"])
        if not cli_args.show_all_checkins:
            pfcs(f"  Number of CheckIns: p[{num_checkins}]", end="")
        else:
            pfcs(f"  CheckIns:")
        if cli_args.show_all_checkins:
            for num, chin in enumerate(data["checkins"], 1):
                pfcs(f"   o[#{num:02d}] {chin}")
        elif num_checkins == 1:
            print(f" ({data['checkins'][0]})")
        elif num_checkins > 1:
            print(f" (most recent at {data['checkins'][-1]})")
        else:
            print()
        if cli_args.filenameify:
            pfcs(f"  y[{beer_obj.filename()}]")
        print()
        return True

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
        if not hashes:
            for _hash in self.list:
                yield self.list[_hash]
        else:
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
        alc = float(check_in.get("beer_abv", 0.0))
        beer_type = check_in.get("beer_type")
        city = check_in.get("venue_city", "")
        if city == "":
            city = None
        venue = check_in.get("venue_name", "")
        if venue == "":
            venue = None
        beer = Beer(beer_name, brewery, alc, beer_type)
        date = datetime.strptime(check_in.get(
            "created_at", ""), UNTAPPD_DATETIME_FMT)
        beer_list.add_checkin(beer, CheckIn(date, venue, city))
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
    parser.add_argument("--show-all-checkins",
                        "-a",
                        action="store_true",
                        dest="show_all_checkins")
    parser.add_argument("--filter",
                        type=str,
                        help="Only show beers where filter matches name. "
                             "Case-Insensitive",
                        default=None)
    parser.add_argument("--date",
                        type=str,
                        default=None,
                        help="List beers had at date",
                        dest="date")
    parser.add_argument("--filenameify",
                        action="store_true")
    return parser.parse_args()


def main():
    args = generate_cli_args()
    data = load_untappd_export(Path(args.json_export_file))
    if data is None:
        return
    beer_list = init_list(data)
    # Top 10 most checked in
    sorting = BeerList.Sorting(args.sort_by) if args.sort_by else None
    beer_list.print_list(args, sort_by=sorting)


if __name__ == "__main__":
    main()
