#!/usr/bin/env python3

from argparse import ArgumentParser
from typing import List

from config import ConfigurationManager, SettingSection, SettingKeys
from base_log import BaseLogGlobalSettings

from wb.helper_methods import parse_download_arg
from wb.server import ServerHandler, ConnectionSettings


def get_args():
    _parser = ArgumentParser("WB Handler")
    _parser.add_argument("--download",
                         "-d",
                         default="",
                         dest="download_items",
                         help="item(s) to download, can be index(es) or name.")
    _parser.add_argument("--list",
                         "-l",
                         action="store_true",
                         dest="list_items",
                         help="list items on WB server(s)")
    _parser.add_argument("--verbose",
                         "-v",
                         action="store_true")
    _rsa_grp = _parser.add_mutually_exclusive_group()
    _rsa_grp.add_argument("--fallback-to-password",
                          "--fallback",
                          "-f",
                          action="store_true",
                          dest="fallback",
                          help="attempt to connect with password if RSA fails")
    _rsa_grp.add_argument("--no-rsa",
                          "-n",
                          action="store_false",
                          dest="use_rsa",
                          help="do not use RSA to connect, instead only attempt password")
    _parser.add_argument("--no-system-scp",
                         "-s",
                         action="store_false",
                         dest="use_system_scp",
                         help="do not use system SCP for transferring files, instead use the "
                              "(potentially slower) python lib SCPClient")
    return _parser.parse_args()


def get_server_addresses_from_settings() -> List[str]:
    _ret = []
    _num = ConfigurationManager().get(key=SettingKeys.WB_NUM_SERVERS, section=SettingSection.WB, assert_exists=True,
                                      convert=int)
    for _n in range(1, _num + 1):
        _key = SettingKeys.WB_SERVER_PREFIX.value + str(_n)
        _ret.append(ConfigurationManager().get(key=_key, section=SettingSection.WB, assert_exists=True))
    return _ret


def main():
    args = get_args()
    BaseLogGlobalSettings().verbose = args.verbose
    BaseLogGlobalSettings().use_timestamps = True
    handler = ServerHandler(ConnectionSettings(use_password=args.fallback or not args.use_rsa,
                                               use_rsa_key=args.use_rsa,
                                               use_system_scp=args.use_system_scp))
    for _addr in get_server_addresses_from_settings():
        handler.add(_addr)
    if not len(handler):
        print(f"no servers found in settings!")
    if not handler.valid():
        print("could not connect to server(s)")
        return
    if not args.download_items or args.list_items:
        handler.print_file_list()
    elif args.download_items:
        _dl_dir = ConfigurationManager().path("download", convert_to_path=True, assert_path_exists=True)
        _keys = parse_download_arg(args.download_items, number_of_items=handler.number_of_items())
        for _key in _keys:
            handler.download(_key, _dl_dir)


if __name__ == "__main__":
    main()
