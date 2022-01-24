import json


class SearchResult:
    def __init__(self, data):
        self._raw = data

    def print(self):
        if not self._raw:
            print(None)
        _str = json.dumps(self._raw, indent=4)
        print(_str)

    def __repr__(self):
        return json.dumps(self._raw, indent=4)

    @property
    def valid(self):
        return "Title" in self._raw

    @property
    def year(self):
        return self._raw.get("Year", None)

    @property
    def title(self):
        return self._raw.get("Title", None)

    @property
    def genre(self):
        return self._raw.get("Genre", None)

    @property
    def id(self):
        return self._raw.get("imdbID", None)