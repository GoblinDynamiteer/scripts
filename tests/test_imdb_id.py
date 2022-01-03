from media.imdb_id import IMDBId


class TestIMDBId:
    def test_string_parse_single(self):
        iid = IMDBId("https://www.imdb.com/title/tt9174578/")
        assert str(iid) == "tt9174578"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True
        iid = IMDBId("xxx TT0112015 zzz")
        assert str(iid) == "tt0112015"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True

    def test_string_parse_multiple(self):
        iid = IMDBId("texttext https://www.imdb.com/title/tt9174578/"
                     " texttexttext https://www.imdb.com/title/tt13315308/ x")
        assert str(iid) == "tt9174578"
        assert iid.has_multiple_ids() is True
        assert iid.valid() is True

    def test_string_parse_multiple_same_id(self):
        iid = IMDBId("texttext https://www.imdb.com/title/tt9174578/"
                     " texttexttext https://www.imdb.com/title/tt9174578/ x")
        assert str(iid) == "tt9174578"
        assert iid.has_multiple_ids() is False
        assert iid.valid() is True

    def test_string_parse_invalid(self):
        iid = IMDBId("something else")
        assert str(iid) == ""
        assert iid.has_multiple_ids() is False
        assert iid.valid() is False
