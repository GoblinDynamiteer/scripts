#!/usr/bin/env python3.8

import argparse
import csv
from enum import Enum
from pathlib import Path
from datetime import datetime

import config


class Command(Enum):
    Add = "add"
    Info = "info"


class Columns(Enum):
    Date = "date"
    Bank = "bank"
    Account = "account_name"
    Balance = "balance"


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
    parser.add_argument("command",
                        help=f"valid: {[x.value for x in Command]}",
                        type=Command)
    return parser.parse_args()


def read_csv() -> list:
    csv_path = config.ConfigurationManager().get(
        config.SettingKeys.PATCH_ECONOMY_CSV, convert=Path)
    if not csv_path.is_file():
        return {}
    with open(csv_path, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [r for r in reader]


def update_csv(bank: str, account: str, balance: int):
    date = datetime.now().strftime("%Y-%m-%d")
    csv_path = config.ConfigurationManager().get(
        config.SettingKeys.PATCH_ECONOMY_CSV, convert=Path)
    fieldnames = [c.value for c in Columns]
    if not csv_path.is_file():
        print(f"creating new file: {csv_path}")
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    with open(csv_path, "a+", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        data_dict = {Columns.Date.value: date,
                     Columns.Bank.value: bank,
                     Columns.Account.value: account,
                     Columns.Balance.value: balance}
        writer.writerow(data_dict)


def print_info():
    data = read_csv()
    if data == {}:
        print("no data available!")
        return
    print(data)


def main():
    args = get_args()
    if args.command == Command.Info:
        print_info()
    elif args.command == Command.Add:
        if any([args.bank is None, args.account is None, args.balance is None]):
            raise ValueError("--bank, --account, --balance has to be set!")
        update_csv(args.bank, args.account, args.balance)


if __name__ == "__main__":
    main()
