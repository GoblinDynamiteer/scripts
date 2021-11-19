#!/usr/bin/env python3

"""Script to interact with torrent-server"""

import argparse
import re
from pathlib import Path
from enum import Enum

import config
import extract
import util
from db.db_mov import MovieDatabase
from db.db_tv import EpisodeDatabase
from printout import pfcs, cstr
from release import determine_release_type
from run import local_command, remote_command_get_output

CACHED_WB_LIST_FILENAME = "cached_wb_list.txt"


class Server(Enum):
    WB1 = "wb"
    WB2 = "wb2"


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


def ls_remote_items(filter_re: str = "", use_cached_if_new=False, server=Server.WB1):
    file_name = Path(__file__).resolve().parent / CACHED_WB_LIST_FILENAME
    file_list = []
    if use_cached_if_new:
        with open(file_name, "r") as list_file:
            saved_stamp = int(list_file.readline())
            if abs(saved_stamp - util.now_timestamp() < (60 * 5)):
                file_list = [l.replace("\n", "")
                             for l in list_file.readlines()]
    if not file_list:
        file_list = remote_command_get_output(
            r'ls -trl --time-style="+%Y-%m-%d %H:%M" ~/files', server.value
        ).split("\n")
        with open(file_name, "w") as list_file:
            list_file.write(str(util.now_timestamp()) + "\n")
            list_file.writelines(f"{s}\n" for s in file_list)
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
        item_name = cstr(item["name"], item_str_color)
        # Right trim filename strings if to prevent multiple lines in terminal window
        if len_without_itemname + len(item["name"]) + 1 > util.terminal_width():
            diff = abs(
                util.terminal_width() - len_without_itemname -
                len(item["name"]) - 1
            )
            trimmed_item_name = util.shorten_string(
                item["name"], len(item["name"]) - diff
            )
            item_name = cstr(trimmed_item_name, item_str_color)
        print(
            f'[{cstr(index, item_str_color)}] (-{item_len:03d}) {item["date"]} '
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
        print(f'{cstr("could not parse indexes, aborting!", "red")}')
        return []


def download(item: dict, extr: bool = False, server=Server.WB1, limit=None):
    file_name = item["name"]
    repl_list = [(" ", r"\ "),  # TODO: use escaped for all?
                 ("'", "*"),
                 ("[", "*"),
                 ("]", "*"),
                 ("(", "*"),
                 (")", "*")]
    for char, repl in repl_list:
        file_name = file_name.replace(char, repl)
    print(f'downloading: {cstr(file_name, "orange")}')
    conf = config.ConfigurationManager()
    dl_dir = conf.get("path_download")
    limit_str = f"-l {limit} " if limit is not None else ""
    command = f'scp {limit_str}-r {server.value}:"~/files/{file_name}" "{dl_dir}"'
    local_command(command, hide_output=False)
    # only run extract if dest was default dl dir
    if extr:
        path_for_extract_cmd = Path(dl_dir) / file_name
        if not path_for_extract_cmd.exists():
            return
        pfcs(f"running extract command on: g[{path_for_extract_cmd}]")
        extract.extract_item(path_for_extract_cmd)


def wb_download_items(items: list, indexes: str, extr=False, server=Server.WB1, limit=None):
    "Downloads the items passed, based on indexes, to dest_dir"
    items_to_dl = filter_using_get_arg_indexes(items, indexes)
    if not items_to_dl:
        return
    print("Will download the following:")
    for item in items_to_dl:
        pfcs(f" - g[{item['name']}]")
    [download(item, extr=extr, server=server, limit=limit) for item in items_to_dl]


def wb_scp_torrents(server=Server.WB1):
    "send torrent files to wb watch dir"
    torrent_file_list = []
    conf = config.ConfigurationManager()
    dl_paths = [Path.home() / "mnt" / "downloads",
                Path(conf.get("path_download"))]
    for dl_path in dl_paths:
        if not dl_path.exists():
            continue
        torrent_file_list += dl_path.glob("**/*.torrent")
    for torrent_file in torrent_file_list:
        command = f'scp "{str(torrent_file)}" {server.value}:~/watch'
        pfcs(f"sending torrent: g[{torrent_file.name}]")
        if local_command(command, hide_output=True):
            try:
                torrent_file.unlink()  # remove file
                pfcs(f"removed local torrent: o[{torrent_file.name}]")
            except:
                pfcs(f"failed to remove local torrent: e[{torrent_file.name}]")


def get_cli_args():
    parser = argparse.ArgumentParser(description="wb tool")
    parser.add_argument("command",
                        type=str,
                        choices=["list", "new", "download", "get", "send"])
    parser.add_argument("--get",
                        type=str,
                        default="-1",
                        help="items to download. indexes")
    parser.add_argument("--filter",
                        "-f",
                        type=str,
                        default="",
                        help="Filter items to be downloaded/listed, regex")
    parser.add_argument("--extract",
                        "-e",
                        action="store_true",
                        help="Run extract after download",
                        dest="extract")
    parser.add_argument("--server",
                        "-s",
                        default=Server.WB1,
                        type=Server,
                        help="select server",
                        dest="server")
    parser.add_argument("--limit",
                        default=None,
                        type=int,
                        help="download speed limit in Kbit/s")
    return parser.parse_args()


def main():
    args = get_cli_args()
    if args.command in ["list", "new"]:
        wb_list_items(ls_remote_items(args.filter, server=args.server))
    elif args.command in ["download", "get"]:
        items = ls_remote_items(
            args.filter, use_cached_if_new=True, server=args.server)
        wb_download_items(items, args.get, args.extract, server=args.server, limit=args.limit)
    elif args.command == "send":
        wb_scp_torrents()
    else:
        print(cstr("wrong command!", "orange"))


if __name__ == "__main__":
    main()
