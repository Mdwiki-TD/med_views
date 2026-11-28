""" """

from __future__ import annotations

import logging

import mwclient
import mwclient.errors

from ..config import Config

logger = logging.getLogger(__name__)


class MwclientPage:
    def __init__(self, title: str) -> None:
        config = Config.get_instance()
        self.site_mw = mwclient.Site("www.mdwiki.org")
        self.username = config.my_username
        self.password = config.mdwiki_pass

        try:
            self.site_mw.login(self.username, self.password)
        except mwclient.errors.LoginError as e:
            logger.error(f"Error logging in: {e}")

        self.page = self.site_mw.pages[title]

    def get_text(self):
        return self.page.text()

    def exists(self):
        return self.page.exists

    def save(self, newtext: str, summary: str) -> None:
        self.page.save(newtext, summary=summary)

    def create(self, newtext: str, summary: str) -> None:
        self.page.save(newtext, summary=summary)


__all__ = [
    "MwclientPage",
]
