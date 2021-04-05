from argparse import Namespace
from pathlib import Path
import json

from pytest_mock import mocker
from datetime import datetime

from ripper_scheduler import ScheduledShowList, get_cli_args, get_now

DATA = [
    {
        "name": "SomeShow",
        "process": True,
        "url": "https://www.tv4play.se/program/some_show",
        "dest": "$TV_TEMP/some_show",
        "airtime": {
            "fri": "20:00"
        }
    },
    {
        "name": "SomeOtherShow",
        "process": True,
        "url": "https://www.tv4play.se/program/some_other_show",
        "dest": "$TV_TEMP/some_other_show",
        "airtime": {
            "sat": "20:00"
        }
    }
]

DATE_FRIDAY_1900 = datetime(2021, 4, 9, 19, 0, 0)
DATE_FRIDAY_2100 = datetime(2021, 4, 9, 21, 0, 0)

def test_scheduled_show_list_no_existing_file():
    non_file = Path("/tmp/non_existing_schedule___.json")
    assert not non_file.exists()
    args = get_cli_args()
    args.json_file = non_file
    show_list = ScheduledShowList(args)
    assert not show_list.valid
    assert show_list.empty()


def test_scheduled_show_list():
    sched_file = Path("/tmp/test_show_schedule.json")
    with open(sched_file, "w") as _file:
        json.dump(DATA, _file)
    args = get_cli_args()
    args.json_file = sched_file
    args.verbose = True
    show_list = ScheduledShowList(args)
    assert show_list.valid
    assert len([s for s in show_list]) == 2
    assert not show_list.empty()


def test_scheduled_show_list_one_show_next_show():
    sched_file = Path("/tmp/test_show_schedule.json")
    with open(sched_file, "w") as _file:
        json.dump(DATA, _file)
    args = get_cli_args()
    args.json_file = sched_file
    args.verbose = True
    show_list = ScheduledShowList(args)
    next_show = show_list.next_show()
    assert next_show.name == "SomeShow"


def test_scheduled_show_list_one_show_next_show_seconds_to(mocker):
    mocker.patch("ripper_scheduler.get_now", return_value=DATE_FRIDAY_1900)
    sched_file = Path("/tmp/test_show_schedule.json")
    with open(sched_file, "w") as _file:
        json.dump(DATA, _file)
    args = get_cli_args()
    args.json_file = sched_file
    args.verbose = True
    show_list = ScheduledShowList(args)
    next_show = show_list.next_show()
    assert not next_show.should_download()
    assert next_show.shortest_airtime() == 60 * 60
