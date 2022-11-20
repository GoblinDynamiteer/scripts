import re
from typing import Optional, Union


def parse_percentage_from_string(string: str, return_string: bool = False) -> Optional[Union[str, int]]:
    """Parse a percentage value from a string, if possible"""
    for regex in (r"\d{1,3}%", r"\d{1,3}.%"):
        _match = re.search(regex, string)
        if not _match:
            continue
        _pstr = _match.group().replace("%", " ").strip()
        if _pstr.isdigit():
            if return_string:
                return f"{int(_pstr)}%"
            return int(_pstr)
    return None
