import os
import sys

try:
    from newapi import ALL_APIS  # noqa: F401

    from .mdwiki_page import page
except ImportError:
    newapi_bot_path = "I:/core/bots/new/newapi_bot"
    if os.path.exists(newapi_bot_path):
        sys.path.insert(0, newapi_bot_path)
        from newapi import ALL_APIS  # noqa: F401

        from .mdwiki_page import page
    else:
        print("newapi_bot not found, using mwclient fallback")
        from .mdwiki_page_mwclient import page_mwclient as page

__all__ = ["page"]
