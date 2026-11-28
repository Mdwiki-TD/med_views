#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import sys
import time
from collections import defaultdict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import quote

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

default_user_agent: str = "himo bot/1.0 (https://himo.toolforge.org/; tools.himo@toolforge.org)"

endpoints: dict[str, str] = {
    "article": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article",
}


def parse_date(string_date: str) -> datetime:
    return datetime.strptime(string_date.ljust(10, "0"), "%Y%m%d%H")


def format_date(d: date | datetime) -> str:
    if isinstance(d, datetime):
        return d.strftime("%Y%m%d%H")
    # For date objects, convert to datetime first
    return datetime(d.year, d.month, d.day).strftime("%Y%m%d%H")


def timestamps_between(start: date | datetime, end: date | datetime, increment: timedelta) -> Iterator[datetime]:
    # convert both start and end to datetime just in case either are dates
    start = datetime(start.year, start.month, start.day, getattr(start, "hour", 0))
    end = datetime(end.year, end.month, end.day, getattr(end, "hour", 0))

    while start <= end:
        yield start
        start += increment


def month_from_day(dt: date | datetime) -> datetime:
    return datetime(dt.year, dt.month, 1)


class PageviewsClientHelper:
    def format_article_title(self, title: str) -> str:
        return title.replace(" ", "_")

    def filter_data(self, data: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
        # remove any key < 2015 and not = "all"

        new_data: dict[str, dict[str, int]] = {}

        for title, views in data.items():
            new_data[title] = {
                k: v for k, v in views.items() if (k.isnumeric() and int(k) >= 2015) or k == "all" or (v is not None and v > 0)
            }

        return new_data

    def summarize_monthly_views(
        self, article_monthly_data: defaultdict[datetime, dict[str, int | None]]
    ) -> dict[str, dict[str, int]]:
        new_data: dict[str, dict[str, int]] = {}

        for month, y in article_monthly_data.items():
            # month = datetime.datetime(2024, 5, 1, 0, 0)
            year_n = month.strftime("%Y")
            for article, count in y.items():
                article = article.replace("_", " ")
                # ensure nested dict & the specific year key both exist
                article_dict = new_data.setdefault(article, {"all": 0, year_n: 0})

                if count is not None:
                    article_dict[year_n] = article_dict.get(year_n, 0) + count
                    article_dict["all"] = article_dict.get("all", 0) + count

                # sort article_dict keys
                article_dict = dict(sorted(article_dict.items(), key=lambda item: item[0]))

                new_data[article] = article_dict
        return new_data


class PageviewsClient(PageviewsClientHelper):
    def __init__(self, user_agent: str = "", parallelism: int = 10) -> None:
        """
        Create a PageviewsClient

        :Parameters:
            user_agent : User-Agent string to use for HTTP requests. Should be
                         set to something that allows you to be contacted if
                         need be, ref:
                         https://www.mediawiki.org/wiki/REST_API

            parallelism : The number of parallel threads to use when making
                          multiple requests to the API at the same time
        """

        self.headers = {"User-Agent": user_agent if user_agent else default_user_agent}
        self.parallelism = parallelism or 10

    def article_views(
        self,
        project: str,
        articles: str | list[str],
        access: str = "all-access",
        agent: str = "all-agents",
        granularity: str = "daily",
        start: str | date | None = None,
        end: str | date | None = None,
    ) -> defaultdict[datetime, dict[str, int | None]]:
        """
        Get pageview counts for one or more articles
        See `<https://wikimedia.org/api/rest_v1/metrics/pageviews/?doc#!/Pageviews_data/get_metrics_pageviews_per_article_project_access_agent_article_granularity_start_end>`_

        :Parameters:
            project : str
                a wikimedia project such as en.wikipedia or commons.wikimedia
            articles : list(str) or a simple str if asking for a single article
            access : str
                access method (desktop, mobile-web, mobile-app, or by default, all-access)
            agent : str
                user agent type (spider, user, bot, or by default, all-agents)
            end : str|date
                can be a datetime.date object or string in YYYYMMDD format
                default: today
            start : str|date
                can be a datetime.date object or string in YYYYMMDD format
                default: 30 days before end date
            granularity : str
                can be daily or monthly
                default: daily

        :Returns:
            a nested dictionary that looks like: {
                start_date: {
                    article_1: view_count,
                    article_2: view_count,
                    ...
                    article_n: view_count,
                },
                ...
                end_date: {
                    article_1: view_count,
                    article_2: view_count,
                    ...
                    article_n: view_count,
                }
            }
            The view_count will be None where no data is available, to distinguish from 0
        """
        end_date = end or date.today()
        if not isinstance(end_date, date):
            end_date = parse_date(end_date)

        start_date = start or end_date - timedelta(30)
        if not isinstance(start_date, date):
            start_date = parse_date(start_date)

        # If the user passes in a string as "articles", convert to a list
        if isinstance(articles, str):
            articles = [articles]

        articles = [self.format_article_title(a) for a in articles]
        articles_safe = [quote(a, safe="") for a in articles]

        project = "be-tarask.wikipedia" if project == "be-x-old.wikipedia" else project

        urls = [
            "/".join(
                [
                    endpoints["article"],
                    project,
                    access,
                    agent,
                    a,
                    granularity,
                    format_date(start_date),
                    format_date(end_date),
                ]
            )
            for a in articles_safe
        ]

        output_days = timestamps_between(start_date, end_date, timedelta(days=1))
        if granularity == "monthly":
            output_days = list({month_from_day(day) for day in output_days})
        output = defaultdict(dict, {day: dict.fromkeys(articles) for day in output_days})

        # try:
        results = self.get_concurrent(urls)
        some_data_returned = False
        details = {}
        for result in results:
            some_data_returned = "items" in result

            if not some_data_returned:
                detail = result.get("detail")  # or result.get('error')
                # detail = str(result)
                if detail:
                    details.setdefault(detail, 0)
                    details[detail] += 1
                continue

            for item in result["items"]:
                article = item["article"].replace("_", " ")
                output[parse_date(item["timestamp"])][article] = item["views"]

        if not some_data_returned:
            logger.exception(f"The pageview API returned nothing useful at: ({len(urls)})")

            for detail, count in details.items():
                logger.info(f">>>>>>>>>({count}): {detail=}")

        return output

    def get_concurrent(self, urls: list[str]) -> list[dict[str, Any]]:
        def fetch(url: str) -> dict[str, Any]:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                return {"error": f"{exc}", "url": url}

        if self.parallelism == 1:
            return [
                fetch(url)
                for url in tqdm(urls, total=len(urls), desc=f"Fetching URLs, parallelism: {self.parallelism}")
            ]

        with ThreadPoolExecutor(self.parallelism) as executor:
            # results = executor.map(fetch, urls)
            results = tqdm(
                executor.map(fetch, urls), total=len(urls), desc=f"Fetching URLs, parallelism: {self.parallelism}"
            )

            return list(results)

    def article_views_new(self, project: str, articles: list[str], **kwargs: Any) -> dict[str, dict[str, int]]:
        """
        Aggregate pageview counts per article into yearly totals and an overall total.

        Calls article_views to retrieve monthly view counts, converts article names (underscores to spaces), sums counts by year and a cumulative "all" key (ignoring None values), sorts each article's keys, filters entries via filter_data, and returns the resulting structure.

        Returns:
            dict: Mapping from article title (str) to a dictionary whose keys are year strings (e.g., "2024") and "all", with integer cumulative view counts for each key.
        """
        time_start = time.time()

        article_monthly_data = self.article_views(project, articles, **kwargs)

        new_data = self.summarize_monthly_views(article_monthly_data)
        new_data = self.filter_data(new_data)

        delta = time.time() - time_start

        logger.debug(f"article_views, (articles:{len(articles):,}) new_data:{len(new_data):,} time: {delta:.2f} sec")

        return new_data


__all__ = [
    "PageviewsClientHelper",
    "PageviewsClient",
    "parse_date",
    "format_date",
    "timestamps_between",
    "month_from_day",
]
