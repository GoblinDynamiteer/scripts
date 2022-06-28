from argparse import ArgumentParser, Namespace

from media.scan.show import ShowScanner
from media.scan.movie import MovieScanner


def get_args() -> Namespace:
    parser = ArgumentParser("media scanner")
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="be verbose")
    parser.add_argument("--simulate", "-s",
                        action="store_true",
                        help="do not modify database")
    return parser.parse_args()


def main():
    args = get_args()  # TODO: use simulate from args
    mov_scan = MovieScanner(update_database=False, verbose=args.verbose)
    print("Scanning for new movies...")
    count = mov_scan.scan()
    if count == 0:
        print("-> No new movies found")
    else:
        print(f"-> Found {count} new movie(s)")
    show_scan = ShowScanner(update_database=False, verbose=args.verbose)
    print("Scanning for new episodes...")
    count = show_scan.scan()
    if count == 0:
        print("-> No new episodes found")
    else:
        print(f"-> Found {count} new episode(s)")


if __name__ == "__main__":
    main()
