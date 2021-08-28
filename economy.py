#!/usr/bin/env python3.8

import argparse
import csv
from enum import Enum
from pathlib import Path
from datetime import datetime
import shutil

import config
from printing import print_line, pfcs, fcs
from util import BaseLog, now_timestamp

DATE_FMT = r"%Y-%m-%d"


def to_kr_str(value: int, color=True, show_prefix=False):
    ret = f"{value:,}".replace(",", " ") + " kr"
    if show_prefix:
        prefix = "+" if value >= 0 else ""
    else:
        prefix = ""
    if color:
        format_char = "i" if value >= 0 else "r"
        return fcs(f"{format_char}[{prefix}{ret}]")
    return prefix + ret


class MainLog(BaseLog):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.set_log_prefix("ECONOMY_MAIN")
        self.verbose = verbose


class Command(Enum):
    Add = "add"
    Info = "info"


class Columns(Enum):
    Date = "date"
    Bank = "bank"
    Account = "account_name"
    Balance = "balance"


class Balance():
    def __init__(self, date: datetime, value: int):
        self.date = date
        self.value = value

    def print(self, show_date=True, end="\n"):
        if show_date:
            suffix = fcs(f" d[({self.date.strftime(DATE_FMT)})]")
        else:
            suffix = ""
        print(to_kr_str(self.value) + suffix, end=end)

    def print_change(self, other):
        change = self.value - other.value
        percentage = round(self.value / other.value * 100 - 100, 2)
        print("->", to_kr_str(change, show_prefix=True), "since",
                other.date.strftime(DATE_FMT), fcs(f"d[({percentage:.2f} %)]"))


class Account():
    def __init__(self, name, bank):
        self.name = name
        self.bank = bank
        self.balance_history = []

    def add_balance(self, date: datetime, balance: int):
        self.balance_history.append(Balance(date, balance))

    def print(self, print_change=True):
        latest_balance = self.get_latest_balance()
        first_balance = self.get_first_balance()
        if latest_balance is None:
            print(f"{self.bank}/{self.name} : N/A")
        else:
            print(f"{self.bank}/{self.name}: ", end="")
            if print_change and first_balance != latest_balance:
                latest_balance.print(end="")
                latest_balance.print_change(first_balance)
            else:
                latest_balance.print()

    def get_latest_balance(self):
        ret_bal = None
        for bal in self.balance_history:
            if ret_bal is None:
                ret_bal = bal
                continue
            if ret_bal.date < bal.date:
                ret_bal = bal
        return ret_bal

    def get_first_balance(self):
        ret_bal = None
        for bal in self.balance_history:
            if ret_bal is None:
                ret_bal = bal
                continue
            if ret_bal.date > bal.date:
                ret_bal = bal
        return ret_bal


class AccountList():
    def __init__(self, csv_data_dict):
        self.accounts = self._parse_data(csv_data_dict)

    def _parse_data(self, csv_data_dict):
        ret_dict = {}
        for row in csv_data_dict:
            date = datetime.strptime(row["date"], DATE_FMT)
            bank_name = row["bank"]
            account_name = row["account_name"]
            balance = int(row["balance"])
            try:
                account = ret_dict[bank_name][account_name]
            except KeyError as _:
                if bank_name not in ret_dict:
                    ret_dict[bank_name] = {}
                ret_dict[bank_name][account_name] = Account(
                    account_name, bank_name)
                account = ret_dict[bank_name][account_name]
            finally:
                account.add_balance(date, balance)
        return ret_dict

    def print(self):
        tot = 0
        for bank_str in self.accounts:
            tot_bank = 0
            for _, account in self.accounts[bank_str].items():
                account.print()
                val = account.get_latest_balance().value
                tot_bank += val
                tot += val
            print(fcs(f" o[- {bank_str} total]: {to_kr_str(tot_bank)}"))
            print_line()
        print(fcs(f"o[ - total]: {to_kr_str(tot)}"))


def get_args():
    parser = argparse.ArgumentParser("Economy!")
    parser.add_argument("--bank",
                        default=None,
                        type=str)
    parser.add_argument("--account",
                        default=None,
                        type=str)
    parser.add_argument("--balance",
                        default=None,
                        type=int)
    parser.add_argument("--verbose",
                        action="store_true")
    parser.add_argument("command",
                        nargs="?",
                        help=f"valid: {[x.value for x in Command]}",
                        default=Command.Info,
                        type=Command)
    return parser.parse_args()


def backup_csv(cli_args):
    log = MainLog(cli_args.verbose)
    timestamp = now_timestamp()
    backup_path = config.ConfigurationManager().get(
        config.SettingKeys.PATH_BACKUP, convert=Path)
    csv_file_path = config.ConfigurationManager().get(
        config.SettingKeys.PATH_ECONOMY_CSV, convert=Path)
    dest = backup_path / "databases" / f"{csv_file_path.name}_{timestamp}"
    try:
        shutil.copy(csv_file_path, dest)
    except PermissionError:
        shutil.copyfile(csv_file_path, dest)
    log.log(f"backed up: {csv_file_path} --> {dest}")


def read_csv(cli_args) -> [list, None]:
    log = MainLog(True)
    csv_path = config.ConfigurationManager().get(
        config.SettingKeys.PATH_ECONOMY_CSV, convert=Path)
    if csv_path is None:
        log.log_warn(f"csv path not set in settings file!")
        return None
    if not csv_path.is_file():
        log.log_warn(f"not such file: {csv_path}")
        return None
    with open(csv_path, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [r for r in reader]


def update_csv(cli_args):
    log = MainLog(cli_args.verbose)
    date = datetime.now().strftime(DATE_FMT)
    csv_path = config.ConfigurationManager().get(
        config.SettingKeys.PATH_ECONOMY_CSV, convert=Path)
    fieldnames = [c.value for c in Columns]
    if not csv_path.is_file():
        log.log(f"creating new file: {csv_path}")
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    with open(csv_path, "a+", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        data_dict = {Columns.Date.value: date,
                     Columns.Bank.value: cli_args.bank,
                     Columns.Account.value: cli_args.account,
                     Columns.Balance.value: cli_args.balance}
        writer.writerow(data_dict)
        log.log(f"wrote to {csv_path}:", info_str_line2=f"{data_dict}")


def print_info(cli_args):
    data = read_csv(cli_args)
    if not data:
        print("no data available!")
        return
    account_list = AccountList(data)
    account_list.print()


def main():
    args = get_args()
    if args.command == Command.Info:
        print_info(args)
    elif args.command == Command.Add:
        if any([args.bank is None, args.account is None, args.balance is None]):
            raise ValueError("--bank, --account, --balance has to be set!")
        backup_csv(args)
        update_csv(args)


if __name__ == "__main__":
    main()
