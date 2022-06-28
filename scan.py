from argparse import ArgumentParser, Namespace
from typing import List, Callable

from media.scan.show import ShowScanner
from media.scan.movie import MovieScanner

from db.db_mov import MovieDatabase
from db.db_tv import EpisodeDatabase

SCAN_TYPE_MOV = ("mov", "movie", "film")
SCAN_TYPE_TV = ("tv", "show", "ep", "episodes")


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


def _args_to_funcs(args: Namespace) -> List[Callable[[Namespace], None]]:
    if not isinstance(args.scan_types, list) or not args.scan_types:
        return [scan_movies, scan_shows]
    _ret = []
    for scan_type in args.scan_types:
        if scan_type in SCAN_TYPE_TV:
            _ret.append(scan_shows)
        elif scan_type in SCAN_TYPE_MOV:
            _ret.append(scan_movies)
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
