import datetime


def now_timestamp() -> int:
    return int(datetime.datetime.now().timestamp())
