class SizeBytes:
    SUFFIX = "B"
    DIV = 1024.0

    def __init__(self, size_in_bytes: int):
        self.size_bytes: int = size_in_bytes

    def to_string(self) -> str:
        return self._to_human_readable()

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"SizeBytes(size_bytes={self.size_bytes}),{self._to_human_readable()})"

    def _to_human_readable(self) -> str:
        _val = self.size_bytes
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(_val) < self.DIV:
                return f"{_val:3.1f}{unit}{self.SUFFIX}"
            _val /= self.DIV
        return f"{_val:.1f}Yi{self.SUFFIX}"
