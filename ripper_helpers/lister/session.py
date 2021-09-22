from pathlib import Path
from http.cookiejar import MozillaCookieJar, LoadError
from printout import pfcs

from requests import Session
from singleton import Singleton
from config import ConfigurationManager


class SessionSingleton(metaclass=Singleton):
    SESSION = None
    GETS = {}

    def init_session(self):
        if self.SESSION is None:
            self.SESSION = Session()

    def load_cookies_txt(self, file_path=None):
        self.init_session()
        if not file_path:
            file_path = ConfigurationManager().path("cookies_txt")
        if not Path(file_path).exists():
            file_path = Path(__file__).resolve().parent / "cookies.txt"
        if not Path(file_path).exists():
            pfcs("e[error]: could not find cookies.txt!")
            return
        # NOTE use: https://addons.mozilla.org/en-US/firefox/addon/export-cookies-txt/
        try:
            jar = MozillaCookieJar(file_path)
            jar.load(ignore_discard=True, ignore_expires=True)
            self.SESSION.cookies.update(jar)
        except LoadError as error:
            pfcs(f"w[warning] could not load cookies.txt:\n{error}")

    def get(self, url):
        self.init_session()
        if url in self.GETS:
            return self.GETS[url]
        self.GETS[url] = self.SESSION.get(url)
        return self.GETS[url]