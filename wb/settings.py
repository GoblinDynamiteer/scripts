from typing import List, Optional
from dataclasses import dataclass, field
from argparse import ArgumentParser, Namespace

from wb.enums import Command


def _get_args():
    _parser = ArgumentParser("WB Handler")
    _parser.add_argument("--download",
                         "-d",
                         default=None,
                         dest="download_items",
                         help="item(s) to download, can be index(es) or name.")
    _parser.add_argument("--list",
                         "-l",
                         action="store_true",
                         dest="list_items",
                         help="list items on WB server(s)")
    _parser.add_argument("--extra-info",
                         "-i",
                         action="store_true",
                         dest="show_extra_listing_info",
                         help="Show additional info in listing view")
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


@dataclass
class WBSettings:
    commands: List[Command] = field(default_factory=list)
    __args: Optional[Namespace] = None

    def __post_init__(self):
        self.__args = _get_args()
        if self.__args.list_items:
            self.commands.append(Command.List)
        if self.__args.download_items is not None:
            self.commands.append(Command.Download)

    @property
    def use_rsa_key(self) -> bool:
        return self.__args.use_rsa

    @property
    def use_password(self) -> bool:
        return self.__args.fallback

    @property
    def verbose(self) -> bool:
        return self.__args.verbose

    @property
    def use_system_scp(self) -> bool:
        return self.__args.use_system_scp

    @property
    def download_items(self) -> str:
        return self.__args.download_items

    @property
    def show_extra_info(self) -> bool:
        return self.__args.show_extra_listing_info
