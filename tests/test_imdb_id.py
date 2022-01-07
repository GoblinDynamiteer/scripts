from typing import List
from pathlib import Path

import pytest

from media.imdb_id import IMDBId


class TestIMDBIdStringParse:
    def test_single(self):
        iid = IMDBId("https://www.imdb.com/title/tt9174578/")
        assert str(iid) == "tt9174578"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True
        iid = IMDBId("xxx TT0112015 zzz")
        assert str(iid) == "tt0112015"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True

    def test_multiple(self):
        iid = IMDBId("texttext https://www.imdb.com/title/tt9174578/"
                     " texttexttext https://www.imdb.com/title/tt13315308/ x")
        assert str(iid) == "tt9174578"
        assert iid.has_multiple_ids() is True
        assert iid.valid() is True

    def test_multiple_same_id(self):
        iid = IMDBId("texttext https://www.imdb.com/title/tt9174578/"
                     " texttexttext https://www.imdb.com/title/tt9174578/ x")
        assert str(iid) == "tt9174578"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True

    def test_invalid(self):
        iid = IMDBId("something else")
        assert str(iid) == ""
        assert iid.has_multiple_ids() is False
        assert iid.valid() is False


class TestIMDBIdPathParse:
    def test_movie_nfo(self, tmp_path):
        _dirs = tmp_path / "movies" / "M"
        _dirs.mkdir(parents=True)
        _file_mov = _dirs / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv"
        _file_mov.touch()
        _file_nfo = _dirs / "movie.nfo"
        with open(_file_nfo, "w") as fp:
            fp.write("tt2782868")
        assert _file_nfo.is_file()
        iid = IMDBId(_file_nfo)
        assert str(iid) == "tt2782868"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True

    def test_movie_path_containing_nfo(self, tmp_path):
        _dirs = tmp_path / "movies" / "M"
        _dirs.mkdir(parents=True)
        _file_mov = _dirs / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv"
        _file_mov.touch()
        _file_nfo = _dirs / "movie.nfo"
        with open(_file_nfo, "w") as fp:
            fp.write("tt5834426")
        assert _file_nfo.is_file()
        iid = IMDBId(_dirs)
        assert str(iid) == "tt5834426"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True

    def test_release_nfo(self, tmp_path):
        _base: str = "movie.2021.1080p.bluray.x264-grp"
        _mp: Path = tmp_path / "Movie.2021.1080p.BluRay.x264-Grp"
        _mp.mkdir()
        nfo_contents: List[str] = ["Name: Movie.2021.1080p.BluRay.x264-Grp",
                                   "",
                                   "Release date: 04-01-2022",
                                   "",
                                   "IMDB link: http://www.imdb.com/title/tt7740510",
                                   "",
                                   "Resolution: 1920x1036",
                                   "Audio: English DTS-HD Master 6ch 3821 kbps",
                                   "Video: 7750 kbps, CRF 15.5",
                                   "Source: 35970 kbps",
                                   "Subtitles: English SDH, French, Spanish"]
        for ext in ["rar", "sfv"] + [f"r{n:02d}" for n in range(90)]:
            _f = _mp / f"{_base}.{ext}"
            _f.touch()
        with open(_mp / f"{_base}.nfo", "w") as fp:
            fp.writelines(nfo_contents)
        iid = IMDBId(_mp)
        assert str(iid) == "tt7740510"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True


class TestIMDBIdExceptions:
    def test_pass_incorrect_type(self):
        with pytest.raises(TypeError):
            IMDBId(999)  # TODO: this should possibly be valid...
        with pytest.raises(TypeError):
            IMDBId(123.123)
        with pytest.raises(TypeError):
            IMDBId(IMDBId("http://www.imdb.com/title/tt7740510"))

    def test_pass_non_existing_path(self):
        _p = Path("/Nonexisting/Path/")
        assert _p.exists() is False
        with pytest.raises(FileNotFoundError):
            IMDBId(_p)
