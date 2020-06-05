#!/usr/bin/env python3

import json
from pathlib import Path
from argparse import ArgumentParser

from printing import pfcs


class Beer():
    def __init__(self, name, brewery="Unknown", alc=0.0, beer_type="Unknown"):
        self.name = name
        self.brewery = brewery
        self.alc = alc
        self.type = beer_type


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
    return parser.parse_args()


def main():
    args = generate_cli_args()
    data = load_untappd_export(Path(args.json_export_file))
    if data is None:
        return
    beers_had = [
        f'{x.get("brewery_name", "Unknown")} - {x.get("beer_name", "Unknown")}' for x in data]
    beers_had_unique = set(beers_had)
    beer_count = {}
    for beer in beers_had_unique:
        beer_count[beer] = beers_had.count(beer)
    count = 0
    for beer in sorted(beer_count.items(), key=lambda x: x[1], reverse=True):
        pfcs(f"i[{beer[0]}] o[{beer[1]}]")
        if count > 10:
            break
        count += 1


if __name__ == "__main__":
    main()
