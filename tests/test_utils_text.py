from utils.text_utils import parse_percentage_from_string


class TestTextUtils:
    def test_parse_percentage_from_string_0_to_100_no_space(self):
        for p in range(0, 100 + 1):
            _str = f"xxxx {p}% yyyy"
            assert parse_percentage_from_string(_str) == p

    def test_parse_percentage_from_string_0_to_100_with_space(self):
        for p in range(0, 100 + 1):
            _str = f"xxxx {p} % yyyy"
            assert parse_percentage_from_string(_str) == p

    def test_parse_percentage_from_string_0_to_100_no_space_to_str(self):
        for p in range(0, 100 + 1):
            _str = f"xxxx {p}% yyyy"
            assert parse_percentage_from_string(_str, return_string=True) == f"{p}%"

    def test_parse_percentage_from_string_0_to_100_with_space_to_str(self):
        for p in range(0, 100 + 1):
            _str = f"xxxx {p} % yyyy"
            assert parse_percentage_from_string(_str, return_string=True) == f"{p}%"

    def test_parse_percentage_from_string_multiple_get_highest(self):
        _str = f"xxxx 80 % 99 % yyyy"
        assert parse_percentage_from_string(_str) == 99

    def test_parse_percentage_from_string_multiple_get_lowest(self):
        _str = f"xxxx 80 % 99 % yyyy"
        assert parse_percentage_from_string(_str, get_highest_found=False) == 80

    def test_parse_percentage_from_string_multiple_get_highest_to_str(self):
        _str = f"xxxx 80 % 99 % yyyy"
        assert parse_percentage_from_string(_str, return_string=True) == "99%"

    def test_parse_percentage_from_string_multiple_get_lowest_to_str(self):
        _str = f"xxxx 80 % 99 % yyyy"
        assert parse_percentage_from_string(_str, return_string=True, get_highest_found=False) == "80%"
