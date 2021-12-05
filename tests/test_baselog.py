from base_log import BaseLog


def test_warn_once(capsys):
    class C(BaseLog):
        def __init__(self):
            BaseLog.__init__(self, verbose=True)

    c = C()
    c.warn_once("warn")
    captured = capsys.readouterr()
    assert captured.out != ""
    c.warn_once("warn")
    captured = capsys.readouterr()
    assert captured.out == ""
