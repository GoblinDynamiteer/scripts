#!/usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser


from vid import VideoFileMetadata
from run import move_file


def gen_args():
    parser = ArgumentParser()
    parser.add_argument("--source-path",
                        "-s",
                        type=str,
                        dest="source_path",
                        required=True)
    return parser.parse_args()


def process_source_item(item_path, dest_path):
    print(f"filename: {item_path.name}")
    suffix = ""
    # ask for title/seas/ep?
    if "dvdrip.xvid" in item_path.name:
        suffix = "DVDRip.XviD-MEMETiC"
    elif item_path.name.startswith("Smyth"):
        suffix = "SmythEdit"
    elif item_path.suffix == ".mp4":
        res = VideoFileMetadata(item_path).res
        print("> determined resolution:", res)
        suffix = f"{res}p.WEB-DL" if res != 0 else "WEB-DL"
    try:
        season = int(input("enter season: "))
    except ValueError:
        print("requires integer!")
        return False
    if 2003 < season > 2020:
        print("not a valid season!")
        return False
    try:
        episode = int(input("enter episode: "))
    except ValueError:
        print("requires integer!")
        return False
    if 1 < episode > 40:
        print("not a valid episode!")
        return
    title_words = input("enter title: ").split()
    title_str = ".".join([w.capitalize() for w in title_words])
    ext = item_path.suffix
    filename = f"Mythbusters.S{season}E{episode:02d}.{title_str}.{suffix}{ext}"
    season_dest_path = dest_path / f"S{season}"
    if not season_dest_path.is_dir():
        print("no season path:", season_dest_path)
        return False
    print("> moving to", item_path)
    move_file(item_path, season_dest_path, new_filename=filename)
    sub_path = item_path.with_suffix(".vtt")
    if sub_path.is_file():
        new_sub_name = f"Mythbusters.S{season}E{episode:02d}.{title_str}.{suffix}.sv.vtt"
        print("> moving sub to", season_dest_path)
        move_file(sub_path, season_dest_path, new_filename=new_sub_name)
    return True


def main():
    args = gen_args()
    dest_path = Path.cwd()
    if dest_path.name != "Mythbusters":
        print("make sure current working dir is Mythbusters root!")
        return 1
    source_path = Path(args.source_path)
    for item in sorted(source_path.glob("*.mp4")):
        if not process_source_item(item, dest_path):
            print("Aborting!")
            return 1


if __name__ == "__main__":
    main()
