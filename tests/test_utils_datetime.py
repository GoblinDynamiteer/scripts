import utils.datetime_utils
import datetime

from unittest.mock import MagicMock


class TestUtilsDatetime:
    def test_datetime_now_int(self, monkeypatch):
        _expected: int = 1643525776
        datetime_mock = MagicMock(wrap=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.fromtimestamp(_expected)
        monkeypatch.setattr(datetime, "datetime", datetime_mock)
        assert utils.datetime_utils.now_timestamp() == _expected

