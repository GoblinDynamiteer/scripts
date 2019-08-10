#!/usr/bin/env python3.6

""" NZB Helper """

import os
import shutil
from pathlib import Path

import config
import util
from pre import pre_search_from_file
from printing import pfcs
from run import move_file

CFG = config.ConfigurationManager()


def nzbget_dest_path():
    return Path(CFG.path("nzbget")) / 'dst'


def nzbget_nzb_path():
    return Path(CFG.path("nzbget")) / 'nzb'


def user_download_dir():
    return Path(CFG.path("download"))


def find_finished_downloads(extensions=util.video_extensions()):
    dst_path = nzbget_dest_path()
    if not util.is_dir(dst_path):
        pfcs(f'NZBGet destination path does not exist: e[{dst_path}]')
    found_files = []
    for dir_name, _, file_list in os.walk(dst_path):
        matched_files = [Path(dir_name) / file_item for file_item in file_list if any(
            ext in file_item for ext in extensions) and 'sample' not in file_item.lower()]
        if len(matched_files) == 1:
            found_files.append(matched_files[0])
        # TODO: handle len == 0 or len > 1
    return found_files


def move_finished_downloads(extensions=util.video_extensions(),
                            delete_source_dir=True,
                            dest_dir=user_download_dir(),
                            pre_rename=True):
    if not util.is_dir(dest_dir):
        pfcs(f'destination dir does not exist: e[{dest_dir}]')
        return
    count = 0
    found_items = find_finished_downloads(extensions=extensions)
    if not found_items:
        pfcs(
            f'found no completed files with extension(s) i<{extensions}> in NZBGet destination path', format_chars=['<', '>'])
    if found_items:
        print("processing finished downloads...")
    for download in found_items:
        filename = download.name
        containing_dir = download.parent
        rename_log_str = ""
        if pre_rename:
            pre_result = pre_search_from_file(download.name)
            if pre_result:
                filename = f"{pre_result}{download.suffix}"
                rename_log_str = f"\n  renamed i[{filename}]"
        if move_file(download, dest_dir, new_filename=filename, debug_print=False):
            pfcs(f'moved i[{download.name}] to g[{dest_dir}]{rename_log_str}')
            count += 1
            if delete_source_dir:
                shutil.rmtree(containing_dir)
                pfcs(f'removed w[{containing_dir}]')
        else:
            pfcs(f'failed to move e[{download.name}] to w[{dest_dir}]!')
        pfcs(f"d[{'-' * util.terminal_width()}]")
    return count


def move_nzbs_from_download():
    dest_dir = nzbget_nzb_path()
    if not util.is_dir(dest_dir):
        pfcs(f'destination dir does not exist: e[{dest_dir}]')
        return
    count = 0
    for dir_name, _, file_list in os.walk(user_download_dir()):
        nzb_files = [Path(
            dir_name) / file_item for file_item in file_list if file_item.endswith('.nzb')]
        if not nzb_files:
            continue
        for nzb_file in nzb_files:
            if move_file(nzb_file, dest_dir, debug_print=False):
                pfcs(f'moved i[{nzb_file.name}] to g[{dest_dir}]')
                count += 1
            else:
                pfcs(f'failed to move e[{nzb_file.name}] to w[{dest_dir}]!')
    return count


if __name__ == "__main__":
    COUNT = move_nzbs_from_download()
    if not COUNT:
        print("found no new NZB files in downloads")
    else:
        print(f"moved {COUNT} NZB files to NZBGet watch directory")
    COUNT = move_finished_downloads()
    if COUNT:
        print(f"moved {COUNT} completed NZBGet downloads to download directory")
