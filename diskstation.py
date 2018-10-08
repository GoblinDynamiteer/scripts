#!/usr/bin/env python3.6

''' Personal script for interacting with NAS '''

import argparse
import os
import sys
import platform
import subprocess
import config
import str_o

PRINT = str_o.PrintClass(os.path.basename(__file__))
CONFIG = config.ConfigurationManager()
NAS_IP = "192.168.0.101"


def get_ds_shares() -> list:
    " Get a list of available DS shares "
    return ['TV', 'FILM', 'MISC', 'BACKUP', 'DATA', 'DOCEDU', 'AUDIO', 'Rest']


def get_mount_dest() -> str:
    " Get local mount destination path "
    return CONFIG.get_setting("path", "dsmount")


def get_home() -> str:
    " Get path to home directory "
    return CONFIG.get_setting("path", "home")


def _get_credentials_file(share):
    if share == 'Rest':
        return get_home() + ".smbcredentials_drb"
    return get_home() + ".smbcredentials"


def _print_error_invalid_share(string):
    PRINT.error(f"invalid share: [{string}]")


def mount(ds_share):
    " Mount a DS share on a linux system "
    if platform.system() != 'Linux':
        PRINT.error("mount: Not on a Linux-system, quitting.")
        sys.exit(1)
    mount_dest = get_mount_dest()
    ds_shares = get_ds_shares()
    if ds_share == "all" or ds_share.upper() in ds_shares:
        for share in ds_shares:
            if share == ds_share.upper() or ds_share == "all":
                if ismounted(share):
                    PRINT.info(
                        f"{share} is mounted at {get_mount_path(share)}")
                    continue
                cred_file = _get_credentials_file(share)
                opt = f"credentials={cred_file},iocharset=utf8,vers=3.0,rw,file_mode=0777,dir_mode=0777"
                src = f"//{NAS_IP}/{share}"
                local_dest = f"{mount_dest}{share.lower()}"
                PRINT.info(f"mounting {share} to {local_dest}")
                subprocess.call(["sudo", "mount", "-t", "cifs",
                                 src, local_dest, "-o", opt])
    else:
        _print_error_invalid_share(ds_share)


def ismounted(ds_share) -> bool:
    " Check if share is mounted"
    if ds_share.lower() == 'rest':
        return False
    ds_shares = get_ds_shares()
    mount_dest = get_mount_dest()
    if ds_share.upper() in ds_shares:
        local_dest = os.path.join(mount_dest, ds_share.lower())
        subdirs = os.listdir(local_dest)
        if len(subdirs) > 1:
            return True
        return False
    else:
        _print_error_invalid_share(ds_share)
        return False


def get_mount_path(ds_share):
    " Gets mount full mount path on DS "
    if ds_share.lower() == 'rest':
        return None
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
        if share == 'Rest':
            continue
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