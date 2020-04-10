#!/usr/bin/env python3.8

"""Script to interact with torrent-server"""

import argparse
from pathlib import Path
import re

import config
import extract
import util
from db_mov import MovieDatabase
from db_tv import EpisodeDatabase
from printing import pfcs
from printing import to_color_str as CSTR
from release import determine_release_type
from run import local_command, remote_command_get_output


def parse_ls_line(line: str):
    splits = line.split()
    if len(splits) < 4:
        return {}
    data = {}
    data["type"] = "dir" if line.startswith("d") else "file"
    data["size"] = util.bytes_to_human_readable(splits[4])
    data["date"] = f"{splits[5]} {splits[6]}"
    data["name"] = line.split(data["date"])[1].strip()
    return data


def ls_remote_items(filter_re: str = ""):
    file_list = remote_command_get_output(
        r'ls -trl --time-style="+%Y-%m-%d %H:%M" ~/files', "wb"
    ).split("\n")
    items = [parse_ls_line(line) for line in file_list]
    index = 1

    db_mov = MovieDatabase()
    db_ep = EpisodeDatabase()

    for item in items:
        if not item:
            continue
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
    if filter_re:
        return [i for i in items if i and re.search(filter_re, i["name"], re.IGNORECASE)]
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


def filter_using_get_arg_indexes(items: list, indexes: str) -> list:
    if indexes.startswith("-"):  # download last x items
        return items[int(indexes):]
    indexes_to_dl = []
    if "+" in indexes and "-" in indexes:
        pfcs("e[indexes connot contain both '-' and '+'! aborting]")
    try:
        for ix_split in indexes.split(","):
            if "-" in ix_split:
                ranges = ix_split.split("-")
                ran = [r for r in range(int(ranges[0]), int(ranges[1]) + 1)]
                indexes_to_dl.extend(ran)
            elif "+" in ix_split:
                start_num = int(ix_split.split("+")[0])
                addition = int(ix_split.split("+")[1])
                ran = [r for r in range(start_num, start_num + addition + 1)]
                indexes_to_dl.extend(ran)
            else:
                indexes_to_dl.append(int(ix_split))
        return [item for item in items if item["index"] in indexes_to_dl]
    except:
        print(f'{CSTR("could not parse indexes, aborting!", "red")}')
        return []


def download(item: dict, extr: bool = False):
    file_name = item["name"]
    for char, repl in [(" ", r"\ "), ("'", "*")]:
        file_name = file_name.replace(char, repl)
    print(f'downloading: {CSTR(file_name, "orange")}')
    dl_dir = CFG.get("path_download")
    command = f'scp -r wb:"~/files/{file_name}" "{dl_dir}"'
    local_command(command, hide_output=False)
    # only run extract if dest was default dl dir
    if extr:
        path_for_extract_cmd = Path(dl_dir) / file_name
        if not path_for_extract_cmd.exists():
            return
        pfcs(f"running extract command on: g[{path_for_extract_cmd}]")
        extract.extract_item(path_for_extract_cmd)


def wb_download_items(items: list, indexes: str, extr=False):
    "Downloads the items passed, based on indexes, to dest_dir"
    items_to_dl = filter_using_get_arg_indexes(items, indexes)
    if not items_to_dl:
        return
    print("Will download the following:")
    for item in items_to_dl:
        pfcs(f" - g[{item['name']}]")
    [download(item, extr=extr) for item in items_to_dl]


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
    PARSER.add_argument(
        "command",
        type=str,
        choices=["list", "new", "download", "get", "send"])
    PARSER.add_argument(
        "--get",
        type=str,
        default="-1",
        help="items to download. indexes"
    )
    PARSER.add_argument(
        "--filter",
        "-f",
        type=str,
        default="",
        help="Filter items to be downloaded/listed, regex"
    )
    PARSER.add_argument(
        "--extract",
        "-e",
        action="store_true",
        help="Run extract after download",
        dest="extract"
    )
    ARGS = PARSER.parse_args()

    if ARGS.command in ["list", "new"]:
        wb_list_items(ls_remote_items(ARGS.filter))
    elif ARGS.command in ["download", "get"]:
        wb_download_items(ls_remote_items(ARGS.filter), ARGS.get, ARGS.extract)
    elif ARGS.command == "send":
        wb_scp_torrents()
    else:
        print(CSTR("wrong command!", "orange"))
