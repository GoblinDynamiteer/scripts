#!/usr/bin/env python3

import json
from pathlib import Path

from printing import pfcs


class Beer():
    def __init__(self, name, brewery = "Unknown", alc = 0.0, beer_type = "Unknown"):
        self.name = name
        self.brewery = brewery
        self.alc = alc
        self.type = beer_type


def load_untappd_export(file_path : Path):
    if file_path.is_file():
        with open(file_path) as export_file:
            try:
                return json.load(export_file)
            except Exception as error:
                print(error)
                return None
    return None

def main():
    data = load_untappd_export(Path("untappd.json"))
    beers_had = [f'{x.get("brewery_name", "Unknown")} - {x.get("beer_name", "Unknown")}' for x in data]
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
