#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from typing import List, Callable

from media.scan.show import ShowScanner
from media.scan.movie import MovieScanner

from db.db_mov import MovieDatabase
from db.db_tv import EpisodeDatabase

from config import ConfigurationManager, SettingKeys, SettingSection

SCAN_TYPE_MOV = ("mov", "movie", "film")
SCAN_TYPE_TV = ("tv", "show", "ep", "episodes")
SCAN_TYPE_DIAG = ("diag", "diagnostics")


def get_args() -> Namespace:
    parser = ArgumentParser("media scanner")
    parser.add_argument("scan_types", nargs="*")
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="be verbose")
    parser.add_argument("--simulate", "-s",
                        action="store_true",
                        help="do not modify database")
    return parser.parse_args()


def scan_movies(args: Namespace) -> None:
    mov_scan = MovieScanner(update_database=not args.simulate,
                            verbose=args.verbose)
    print("Scanning for new movies...")
    count = mov_scan.scan()
    if count == 0:
        print("-> No new movies found")
        return
    print(f"-> Found {count} new movie(s)")
    if not args.simulate:
        _db = MovieDatabase()
        _db.export_latest_added_movies()


def scan_shows(args: Namespace) -> None:
    show_scan = ShowScanner(update_database=not args.simulate,
                            verbose=args.verbose)
    print("Scanning for new episodes...")
    count = show_scan.scan()
    if count == 0:
        print("-> No new episodes found")
        return
    print(f"-> Found {count} new episode(s)")
    if not args.simulate:
        _db = EpisodeDatabase()
        _db.export_latest_added_episodes()


def scan_diagnostics_movies(args: Namespace) -> None:
    _mdb = MovieDatabase()
    _allowed: List[str] = ConfigurationManager().get(
        assert_exists=True,
        section=SettingSection.MediaScanner,
        key=SettingKeys.SCANNER_ALLOWED_DUPLICATES).split(",")

    def _list_duplicate_movs() -> int:
        _count = 0
        for imdb_id, movies in _mdb.find_duplicates().items():
            _is_duplicate: bool = True
            for _needle in _allowed:
                _matching = [m for m in movies if _needle.lower() in m.lower()]
                if len(_matching) == 1:
                    _is_duplicate = False
            if _is_duplicate:
                _count += 1
                print(imdb_id)
                for mov in movies:
                    print(f" {mov}")
        return _count

    print("scanning for removed movies...")
    mov_scan = MovieScanner(update_database=not args.simulate,
                            verbose=args.verbose)
    count = mov_scan.scan_removed()
    if count == 0:
        print("no removed movies found")
    else:
        print(f"found {count} removed movies!")
        if not args.simulate:
            _mdb.export_latest_removed_movies()
    print("scanning for duplicate movies...")
    count = _list_duplicate_movs()
    if count == 0:
        print("no duplicates found")
    else:
        print(f"found {count} duplicates!")


def scan_diagnostics(args: Namespace) -> None:
    scan_diagnostics_movies(args)


def _args_to_funcs(args: Namespace) -> List[Callable[[Namespace], None]]:
    if not isinstance(args.scan_types, list) or not args.scan_types:
        return [scan_movies, scan_shows, scan_diagnostics]
    _ret = []
    for scan_type in args.scan_types:
        if scan_type in SCAN_TYPE_TV:
            _ret.append(scan_shows)
        elif scan_type in SCAN_TYPE_MOV:
            _ret.append(scan_movies)
        elif scan_type in SCAN_TYPE_DIAG:
            _ret.append(scan_diagnostics)
        elif args.verbose:
            print(f"invalid scan type: {scan_type}")
    if not _ret and args.verbose:
        print("could not determine scan types...")
    return list(set(_ret))


def main():
    args = get_args()
    for _func in _args_to_funcs(args):
        _func(args)


if __name__ == "__main__":
    main()
