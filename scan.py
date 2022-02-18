from media.scan.show import ShowScanner
from media.scan.movie import MovieScanner


def main():
    mov_scan = MovieScanner(update_database=False)
    mov_scan.scan()
    show_scan = ShowScanner(update_database=False)
    show_scan.scan()


if __name__ == "__main__":
    main()
