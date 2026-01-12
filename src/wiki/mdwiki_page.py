"""


"""
# ---
import functools
import sys
import logging
from ..config import my_username, mdwiki_pass

all_apis_valid = None
try:
    from newapi import ALL_APIS
except ImportError:
    all_apis_valid = None


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def load_main_api() -> ALL_APIS | None:
    if all_apis_valid is None:
        return None
    return ALL_APIS(lang="www", family="mdwiki", username=my_username, password=mdwiki_pass)


class page:
    def __init__(self, title: str):
        api = load_main_api()
        if api is None:
            raise ValueError("API is not available")
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
