"""

from api_bots.mdwiki_page import load_main_api

"""
# ---
import functools
import os
import configparser
from newapi import ALL_APIS

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


main_api = load_main_api()

NEW_API = main_api.NEW_API
MainPage = main_api.MainPage
