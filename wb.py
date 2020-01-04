#!/usr/bin/env python3.8

"""Script to interact with torrent-server"""

import argparse
import os
from pathlib import Path

import config
import extract
import util
import util_tv
from db_mov import MovieDatabase
from db_tv import EpisodeDatabase
from printing import pfcs
from printing import to_color_str as CSTR
from release import ReleaseType, determine_release_type
from run import local_command, remote_command_get_output


def _parse_ls(line: str):
    splits = line.split()
    if len(splits) < 4:
        return {}
    data = {}
    data["type"] = "dir" if line.startswith("d") else "file"
    data["size"] = util.bytes_to_human_readable(splits[4])
    data["date"] = f"{splits[5]} {splits[6]}"
    data["name"] = line.split(data["date"])[1].strip()
    return data


def _get_items():
    file_list = remote_command_get_output(
        r'ls -trl --time-style="+%Y-%m-%d %H:%M" ~/files', "wb"
    ).split("\n")
    items = [_parse_ls(line) for line in file_list]
    index = 1

    db_mov = MovieDatabase()
    db_ep = EpisodeDatabase()

    for item in items:
        if item:
            item["index"] = index
            index += 1
            item["downloaded"] = False
            if item["name"].replace(".mkv", "") in db_mov:
                item["downloaded"] = True
            if not item["downloaded"]:
                tv_item_names = [
                    item["name"],
                    item["name"].lower(),
                    f"{item['name']}.mkv",
                    f"{item['name']}.mkv".lower(),
                ]
                if any(x in db_ep for x in tv_item_names):
                    item["downloaded"] = True
    return [item for item in items if item]


def wb_list_items(items):
    "Lists items on server"
    len_without_itemname = 45
    item_len = len(items)
    for item in items:
        index = f'#{item["index"]:02d}'
        media_type = determine_release_type(item["name"]).strshort
        item_str_color = "orange"
        if item["downloaded"]:
            item_str_color = "lgreen"
        item_name = CSTR(item["name"], item_str_color)
        # Right trim filename strings if to prevent multiple lines in terminal window
        if len_without_itemname + len(item["name"]) + 1 > util.terminal_width():
            diff = abs(
                util.terminal_width() - len_without_itemname -
                len(item["name"]) - 1
            )
            trimmed_item_name = util.shorten_string(
                item["name"], len(item["name"]) - diff
            )
            item_name = CSTR(trimmed_item_name, item_str_color)
        print(
            f'[{CSTR(index, item_str_color)}] (-{item_len:03d}) {item["date"]} '
            f'{item["size"]:>10} ({media_type}) '
            f"[{item_name}]"
        )
        item_len -= 1


def _parse_get_indexes(items: list, indexes: str) -> list:
    if indexes.startswith("-"):  # download last x items
        return items[int(indexes):]
    indexes_to_dl = []
    try:
        for ix_split in indexes.split(","):
            if "-" in ix_split:
                ranges = ix_split.split("-")
                ran = [r for r in range(int(ranges[0]), int(ranges[1]) + 1)]
                indexes_to_dl.extend(ran)
            else:
                indexes_to_dl.append(int(ix_split))
        return [item for item in items if item["index"] in indexes_to_dl]
    except:
        print(f'{CSTR("could not parse indexes, aborting!", "red")}')
        return []


def download(item: dict, dest: str, extr: bool = False):
    file_name = item["name"].replace(" ", r"\ ")
    print(f'downloading: {CSTR(file_name, "orange")}')
    if dest == "auto":
        dest = CFG.get("path_download")
        if util_tv.is_episode(file_name) and file_name.endswith(".mkv"):
            show = util_tv.determine_show_from_episode_name(file_name)
            if show:
                path = Path(CFG.get("path_tv")) / show
                season = util_tv.parse_season(file_name)
                if path.exists() and season:
                    path = Path(path) / f"S{season:02d}"
                    if path.exists():
                        dest = path
                        pfcs(f"using auto destination:\n  g[{dest}]")
    command = f'scp -r wb:"~/files/{file_name}" "{dest}"'
    local_command(command, hide_output=False)
    # only run extract if dest was default dl dir
    if dest == CFG.get("path_download") and extr:
        path_for_extract_cmd = Path(dest) / file_name
        if not path_for_extract_cmd.exists():
            return
        pfcs(f"running extract command on: g[{path_for_extract_cmd}]")
        extract.extract_item(path_for_extract_cmd)


def wb_download_items(items: list, indexes: str, dest_dir: str, extr=False):
    "Downloads the items passed, based on indexes, to dest_dir"
    if dest_dir != "auto" and not os.path.exists(dest_dir):
        print(f'{CSTR("destination does not exist, aborting!", "red")}')
        return
    items_to_dl = _parse_get_indexes(items, indexes)
    [download(item, dest_dir, extr=extr) for item in items_to_dl]


def wb_scp_torrents():
    "send torrent files to wb watch dir"
    torrent_file_list = []
    dl_paths = [Path.home() / "mnt" / "downloads",
                Path(CFG.get("path_download"))]
    for dl_path in dl_paths:
        if not dl_path.exists():
            continue
        torrent_file_list += dl_path.glob("**/*.torrent")
    for torrent_file in torrent_file_list:
        command = f'scp "{str(torrent_file)}" wb:~/watch'
        pfcs(f"sending torrent: g[{torrent_file.name}]")
        if local_command(command, hide_output=True):
            try:
                torrent_file.unlink()  # remove file
                pfcs(f"removed local torrent: o[{torrent_file.name}]")
            except:
                pfcs(f"failed to remove local torrent: e[{torrent_file.name}]")


if __name__ == "__main__":
    CFG = config.ConfigurationManager()
    PARSER = argparse.ArgumentParser(description="ripper")
    PARSER.add_argument("command", type=str, choices=[
                        "list", "new", "download", "get", "send"])
    PARSER.add_argument("--dest", type=str, default=CFG.get("path_download"))
    PARSER.add_argument(
        "--get", type=str, default="-1", help="items to download. indexes"
    )
    PARSER.add_argument(
        "--extract",
        "-e",
        action="store_true",
        help="Run extract after download",
        dest="extract",
    )
    ARGS = PARSER.parse_args()

    if ARGS.command in ["list", "new"]:
        wb_list_items(_get_items())
    elif ARGS.command in ["download", "get"]:
        wb_download_items(_get_items(), ARGS.get, ARGS.dest, ARGS.extract)
    elif ARGS.command == "send":
        wb_scp_torrents()
    else:
        print(CSTR("wrong command!", "orange"))
