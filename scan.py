#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from typing import List, Callable

from media.scan.show import ShowScanner
from media.scan.movie import MovieScanner
from media.scan.diagnostics import DiagnosticsScanner
from media.util import MediaPaths

from db.db_mov import MovieDatabase
from db.db_tv import EpisodeDatabase

from utils.file_utils import FileInfo

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
    parser.add_argument("--fix",
                        action="store_true",
                        dest="fix_issues")
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
    diag_scan = DiagnosticsScanner(verbose=args.verbose,
                                   simulate=args.simulate,
                                   fix_issues=args.fix_issues)

    if (count := diag_scan.find_duplicate_movies()) == 0:
        print("no duplicates found")
    else:
        print(f"found {count} duplicates!")

    if (count := diag_scan.find_removed_movies()) == 0:
        print("no removed movies found")
    else:
        print(f"found {count} duplicates!")

    if (count := diag_scan.find_invalid_directory_contents(DiagnosticsScanner.Type.Movie)) == 0:
        print("all movie directories are clean!")
    else:
        print(f"found {count} invalid files or directories!")

    if (count := diag_scan.check_file_and_directory_permissions(DiagnosticsScanner.Type.Movie)) == 0:
        print("all movie files have correct permissions!")
    else:
        print(f"found {count} files with wrong permissions!")


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
