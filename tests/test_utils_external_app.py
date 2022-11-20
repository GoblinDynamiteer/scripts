from pathlib import Path

from utils.external_app_utils import UnrarOutputParser


class TestUnrarOutputParser:
    def test_parse_one_file_extraction(self):
        lines = """UNRAR 6.12 freeware      Copyright (c) 1993-2022 Alexander Roshal
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.rar
        Extracting  /home/user/.tmp/tmp.1Oiveqc5ar/skmv2022.mkv  10%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r00
        ...         skmv2022.mkv                   20%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r01
        ...         skmv2022.mkv                   30%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r02
        ...         skmv2022.mkv                   40%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r03
        ...         skmv2022.mkv                   51%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r04
        ...         skmv2022.mkv                   61%
        """.splitlines()
        parser = UnrarOutputParser()
        for line in lines:
            parser.parse_output(line)
        assert parser.percentage_done == 61
        assert parser.current_file == "skmv2022.mkv"
        assert parser.extracted_files == []
        assert parser.source_path == Path("/home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp")
        assert parser.current_rar == "skmv2022.r04"
        assert parser.destination == Path("/home/user/.tmp/tmp.1Oiveqc5ar/")
        lines = """Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r05
        ...         skmv2022.mkv                   71%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r06
        ...         skmv2022.mkv                   81%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r07
        ...         skmv2022.mkv                   91%
        Extracting from /home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp/skmv2022.r08
        ...         skmv2022.mkv                   OK 
        All OK""".splitlines()
        for line in lines:
            parser.parse_output(line)
        assert parser.percentage_done == 100
        assert parser.current_file == "skmv2022.mkv"
        assert parser.extracted_files == ["skmv2022.mkv"]
        assert parser.source_path == Path("/home/user/files/Some.Cool.Movie.2022.1080p.WEB.H264-GRp")
        assert parser.current_rar == "skmv2022.r08"
        assert parser.destination == Path("/home/user/.tmp/tmp.1Oiveqc5ar/")
