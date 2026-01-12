"""

from api_bots.mdwiki_page import load_main_api

"""
# ---
import functools
import logging
import mwclient
import os
import configparser
from newapi import ALL_APIS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

home_dir = os.getenv("HOME")
project = home_dir if home_dir else "I:/mdwiki/mdwiki"
# ---
config = configparser.ConfigParser()
config.read(f"{project}/confs/user.ini")

my_username = config["DEFAULT"].get("my_username", "")
mdwiki_pass = config["DEFAULT"].get("mdwiki_pass", "")


@functools.lru_cache(maxsize=1)
def load_main_api() -> ALL_APIS:
    return ALL_APIS(lang='www', family='mdwiki', username=my_username, password=mdwiki_pass)


class page:
    def __init__(self, title: str):
        api = load_main_api()
        self.page = api.MainPage(title)

    def get_text(self):
        return self.page.get_text()

    def exists(self):
        return self.page.exists()

    def save(self, newtext: str, summary: str, nocreate: int, minor: str):
        self.page.save(newtext=newtext, summary=summary, nocreate=nocreate, minor=minor)

    def create(self, newtext: str, summary: str):
        self.page.Create(newtext, summary=summary)


class page_mwclient:
    def __init__(self, title: str):
        self.site_mw = mwclient.Site('www.mdwiki.org')
        self.username = my_username
        self.password = mdwiki_pass

        try:
            self.site_mw.login(self.username, self.password)
        except mwclient.errors.LoginError as e:
            logger.error(f"Error logging in: {e}")
            return None

        self.page = self.site_mw.pages[title]

    def get_text(self):
        return self.page.text()

    def exists(self):
        return self.page.exists

    def save(self, newtext: str, summary: str, minor: bool = False):
        self.page.save(newtext, summary=summary, minor=minor)

    def create(self, newtext: str, summary: str):
        self.page.save(newtext, summary=summary)
