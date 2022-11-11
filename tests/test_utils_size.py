from utils.size_utils import SizeBytes


class TestSizeUtils:
    def test_size_bytes_to_string_1kb(self):
        assert SizeBytes(1024).to_string() == "1.0KiB"

    def test_size_bytes_to_string_1_5kb(self):
        assert SizeBytes(int(1024 * 1.5)).to_string() == "1.5KiB"

    def test_size_bytes_to_string_1mb(self):
        assert SizeBytes(1024 ** 2).to_string() == "1.0MiB"

    def test_size_bytes_to_string_1_5mb(self):
        assert SizeBytes((1024 ** 2) * 1.5).to_string() == "1.5MiB"

    def test_size_bytes_to_string_1gb(self):
        assert SizeBytes(1024 ** 3).to_string() == "1.0GiB"

    def test_size_bytes_to_string_1_5gb(self):
        assert SizeBytes((1024 ** 3) * 1.5).to_string() == "1.5GiB"
