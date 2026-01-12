"""


"""
# ---
import functools
import sys
import logging
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
    return ALL_APIS(lang="www", family="mdwiki", username=my_username, password=mdwiki_pass)


class page:
    def __init__(self, title: str):
        api = load_main_api()
        self.page = api.MainPage(title)

    def get_text(self):
        return self.page.get_text()

    def exists(self):
        return self.page.exists()

    def save(self, newtext: str, summary: str, nocreate: int, minor: str) -> bool | str:
        if "save" not in sys.argv:
            logger.info("Dry run mode, not saving changes.")
            return True

        return self.page.save(newtext=newtext, summary=summary, nocreate=nocreate, minor=minor)

    def create(self, newtext: str, summary: str) -> bool:
        if "save" not in sys.argv:
            logger.info("Dry run mode, not saving changes.")
            return True

        return self.page.Create(newtext, summary=summary)
