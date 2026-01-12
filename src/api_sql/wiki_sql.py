#!/usr/bin/python3
"""

"""
import functools
import os
import time
import logging

from ..services import mysql_client

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def GET_SQL() -> bool:
    dir1 = "/mnt/nfs/labstore-secondary-tools-project/"
    dir2 = "/data/project/"

    if not os.path.isdir(dir1) and not os.path.isdir(dir2) or os.path.isdir("I:/core/bots"):
        return False

    return True


def make_labsdb_dbs_p(wiki):
    """Generate host and database name for a given wiki.

    This function takes a wiki name as input, processes it to conform to
    specific naming conventions, and generates the corresponding host and
    database name. It handles certain predefined wiki names by mapping them
    to standardized formats. The function ensures that the resulting names
    are suitable for use in a database connection context.

    Args:
        wiki (str): The name of the wiki, which may include a suffix or hyphens.

    Returns:
        tuple: A tuple containing the host string and the database name string.
    """
    if wiki.endswith("wiki"):
        wiki = wiki[:-4]
    # ---
    wiki = wiki.replace("-", "_")
    # ---
    databases = {
        "wikidata": "wikidatawiki",
        "be-x-old": "be_x_old",
        "be_tarask": "be_x_old",
        "be-tarask": "be_x_old",
    }
    # ---
    wiki = databases.get(wiki, wiki)
    # ---
    valid_ends = [
        "wiktionary",
    ]
    # ---
    if not (any((wiki.endswith(x)) for x in valid_ends)) and wiki.find("wiki") == -1:
        wiki = f"{wiki}wiki"
    # ---
    dbs = wiki
    # ---
    host = f"{wiki}.analytics.db.svc.wikimedia.cloud"
    # ---
    dbs_p = f"{dbs}_p"
    # ---
    return host, dbs_p


def retrieve_sql_results(queries, wiki="", values=None):
    # ---
    logger.debug(f"wiki_sql.py retrieve_sql_results wiki '{wiki}'")
    # ---
    host, dbs_p = make_labsdb_dbs_p(wiki)
    # ---
    logger.info(queries)
    # ---
    if not GET_SQL():
        logger.info("no GET_SQL()")
        return []
    # ---
    start = time.perf_counter()
    # ---
    rows = mysql_client.make_sql_connect(queries, db=dbs_p, host=host, values=values)
    # ---
    delta = time.perf_counter() - start
    # ---
    logger.info(f'wiki_sql.py retrieve_sql_results len(encats) = "{len(rows)}", in {delta:.2f} seconds')
    # ---
    return rows
