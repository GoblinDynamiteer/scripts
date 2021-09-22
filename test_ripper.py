from pathlib import Path
import json

from datetime import datetime

import pytest

from ripper_scheduler import ScheduledShowList, get_cli_args

from ripper_helpers.lister.discovery import DPlayEpisodeLister
from ripper_helpers.lister.svtplay import SVTPlayEpisodeLister
from ripper_helpers.lister.tv4 import Tv4PlayEpisodeLister
from ripper_helpers.lister.viafree import ViafreeEpisodeLister
from ripper_helpers.lister.episode_lister import EpisodeLister
from ripper_helpers.ripper_helpers import ListerFactory

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


class TestEpisodeLister:
    URL_TV4 = r"https://www.tv4play.se/program/idol"
    URL_VIAFREE = r"https://www.viafree.se/program/livsstil/lyxfallan"
    URL_SVTPLAY = r"https://www.svtplay.se/skavlan"
    URL_INVALID = r"http://www.somerandomsite.se/tvshow/"
    URL_DISCOVERY = r"https://www.discoveryplus.se/program/alla-mot-alla-med-filip-och-fredrik"

    def test_get_lister_viafree(self):
        lister = ListerFactory().get_lister(self.URL_VIAFREE)
        assert isinstance(lister, ViafreeEpisodeLister) is True

    def test_get_lister_tv4play(self):
        lister = ListerFactory().get_lister(self.URL_TV4)
        assert isinstance(lister, Tv4PlayEpisodeLister) is True

    def test_get_lister_dplay(self):
        lister = ListerFactory().get_lister(self.URL_DISCOVERY)
        assert isinstance(lister, DPlayEpisodeLister) is True

    def test_get_lister_svtplay(self):
        lister = ListerFactory().get_lister(self.URL_SVTPLAY)
        assert isinstance(lister, SVTPlayEpisodeLister) is True

    def test_get_lister_invalid(self):
        with pytest.raises(ValueError):
            ListerFactory().get_lister(self.URL_INVALID)

    def test_get_lister_svtplay_verbose(self):
        lister = ListerFactory().get_lister(self.URL_SVTPLAY, verbose=True)
        assert isinstance(lister, SVTPlayEpisodeLister) is True
        assert lister.verbose is True

    def test_get_lister_svtplay_save_json(self):
        lister = ListerFactory().get_lister(self.URL_SVTPLAY, save_json_data=True)
        assert isinstance(lister, SVTPlayEpisodeLister) is True
        assert lister._save_json_data is True
