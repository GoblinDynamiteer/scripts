#!/usr/bin/env python3.6

''' Personal script for interacting with NAS '''

import argparse
import os
import sys
import platform
import config
import printing
from run import local_command

PRINT = printing.PrintClass(os.path.basename(__file__))
CONFIG = config.ConfigurationManager()
NAS_IP = CONFIG.get('ds_ip')


def is_ds_special_dir(dir_str):
    return dir_str.startswith('@')


def get_ds_shares() -> list:
    " Get a list of available DS shares "
    return ['APPS', 'TV', 'FILM', 'MISC', 'BACKUP', 'DATA', 'DOCEDU', 'AUDIO']


def get_mount_dest() -> str:
    " Get local mount destination path "
    return CONFIG.get("ds_mount_path")


def _print_error_invalid_share(string):
    PRINT.error(f"invalid share: [{string}]")


def mount(ds_share):
    " Mount a DS share on a linux system "
    if platform.system() != 'Linux':
        PRINT.error("mount: Not on a Linux-system, quitting.")
        sys.exit(1)
    mount_dest = get_mount_dest()
    ds_shares = get_ds_shares()
    cred_file = CONFIG.get('smb_credentials_reg')
    if ds_share == "all" or ds_share.upper() in ds_shares:
        for share in ds_shares:
            if share == ds_share.upper() or ds_share == "all":
                if ismounted(share):
                    PRINT.info(
                        f"{share} is mounted at {get_mount_path(share)}")
                    continue
                opt = f"credentials={cred_file},iocharset=utf8,vers=3.0,rw,file_mode=0777,dir_mode=0777"
                src = f"//{NAS_IP}/{share}"
                local_dest = f"{mount_dest}{share.lower()}"
                PRINT.info(f"mounting {share} to {local_dest}")
                success = local_command(
                    f"sudo mount -t cifs {src} {local_dest} -o {opt}", print_info=False)
                if not success:
                    PRINT.warning(f"mounting of {src} failed!")
    else:
        _print_error_invalid_share(ds_share)


def ismounted(ds_share) -> bool:
    " Check if share is mounted"
    ds_shares = get_ds_shares()
    mount_dest = get_mount_dest()
    if ds_share.upper() in ds_shares:
        local_dest = os.path.join(mount_dest, ds_share.lower())
        if not os.path.exists(local_dest):
            PRINT.info(f"creating mount destination [{local_dest}]")
            os.makedirs(local_dest)
        subdirs = os.listdir(local_dest)
        if subdirs:
            return True
        return False
    else:
        _print_error_invalid_share(ds_share)
        return False


def get_mount_path(ds_share):
    " Gets mount full mount path on DS "
    ds_shares = get_ds_shares()
    mount_dest = get_mount_dest()
    if ds_share.upper() in ds_shares:
        local_dest = os.path.join(mount_dest, ds_share.lower())
        return local_dest
    else:
        _print_error_invalid_share(ds_share)
        return None


def print_ifmounted(ds_share) -> None:
    " Prints out information about share mount status "
    ds_shares = get_ds_shares()
    for share in ds_shares:
        if ds_share == "all" or ds_share.lower() == share:
            if ismounted(share):
                PRINT.info(f"{share} is mounted at {get_mount_path(share)}")
            else:
                PRINT.info(f"{share} is not mounted!")


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("share", help="DS share to mount", type=str)
    ARGS = PARSER.parse_args()
    mount(ARGS.share)
