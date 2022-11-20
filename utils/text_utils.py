import re
from typing import Optional, Union, List


def parse_percentage_from_string(string: str,
                                 return_string: bool = False,
                                 get_highest_found: bool = True) -> Optional[Union[str, int]]:
    """Parse a percentage value from a string, if possible"""
    _ints: List[int] = []
    for regex in (r"\d{1,3}%", r"\d{1,3}.%"):
        _matches = re.findall(regex, string)
        if not _matches:
            continue
        for _m in _matches:
            _pstr = _m.replace("%", " ").strip()
            if _pstr.isdigit():
                _ints.append(int(_pstr))
    if not _ints:
        return None
    _ret_int: int = _ints[0] if not get_highest_found else _ints[-1]
    if return_string:
        return f"{int(_ret_int)}%"
    return _ret_int
