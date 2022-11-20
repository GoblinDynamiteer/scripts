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

