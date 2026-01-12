"""

"""
# ---
import logging
import mwclient
from ..config import my_username, mdwiki_pass


logger = logging.getLogger(__name__)


class page_mwclient:
    def __init__(self, title: str):
        self.site_mw = mwclient.Site("www.mdwiki.org")
        self.username = my_username
        self.password = mdwiki_pass

        try:
            self.site_mw.login(self.username, self.password)
        except mwclient.errors.LoginError as e:
            logger.error(f"Error logging in: {e}")

        self.page = self.site_mw.pages[title]

    def get_text(self):
        return self.page.text()

    def exists(self):
        return self.page.exists

    def save(self, newtext: str, summary: str, minor: bool = False):
        self.page.save(newtext, summary=summary, minor=minor)

    def create(self, newtext: str, summary: str):
        self.page.save(newtext, summary=summary)
