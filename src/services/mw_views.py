#!/usr/bin/python3
"""
"""
import sys
import os
import requests
import time
from requests.utils import quote
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from tqdm import tqdm


tool = os.getenv("HOME")
tool = tool.split("/")[-1] if tool else "himo"
# ---
default_user_agent = f"{tool} bot/1.0 (https://{tool}.toolforge.org/; tools.{tool}@toolforge.org)"

endpoints = {
    "article": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article",
}


def parse_date(stringDate):
    return datetime.strptime(stringDate.ljust(10, "0"), "%Y%m%d%H")


def format_date(d):
    return datetime.strftime(d, "%Y%m%d%H")


def timestamps_between(start, end, increment):
    # convert both start and end to datetime just in case either are dates
    start = datetime(start.year, start.month, start.day, getattr(start, "hour", 0))
    end = datetime(end.year, end.month, end.day, getattr(end, "hour", 0))

    while start <= end:
        yield start
        start += increment


def month_from_day(dt):
    return datetime(dt.year, dt.month, 1)


class PageviewsClient:
    def __init__(self, user_agent="", parallelism=10):
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
        self, project, articles, access="all-access", agent="all-agents", granularity="daily", start=None, end=None
    ):
        """
        Get pageview counts for one or more articles
        See `<https://wikimedia.org/api/rest_v1/metrics/pageviews/?doc\\
                #!/Pageviews_data/get_metrics_pageviews_per_article_project\\
                _access_agent_article_granularity_start_end>`_

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

        TODO: probably doesn't handle unicode perfectly, look into it
        """
        endDate = end or date.today()
        if type(endDate) is not date:
            endDate = parse_date(end)

        startDate = start or endDate - timedelta(30)
        if type(startDate) is not date:
            startDate = parse_date(start)

        # If the user passes in a string as "articles", convert to a list
        if type(articles) is str:
            articles = [articles]

        articles = [a.replace(" ", "_") for a in articles]
        articlesSafe = [quote(a, safe="") for a in articles]

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
                    format_date(startDate),
                    format_date(endDate),
                ]
            )
            for a in articlesSafe
        ]

        outputDays = timestamps_between(startDate, endDate, timedelta(days=1))
        if granularity == "monthly":
            outputDays = list(set([month_from_day(day) for day in outputDays]))
        output = defaultdict(dict, {day: {a: None for a in articles} for day in outputDays})

        # try:
        results = self.get_concurrent(urls)
        some_data_returned = False
        details = {}
        for result in results:
            if "items" in result:
                some_data_returned = True
            else:
                detail = result.get("detail")  # or result.get('error')
                # detail = str(result)
                if detail:
                    details.setdefault(detail, 0)
                    details[detail] += 1

                if "printresult" in sys.argv:
                    print("result:", result)
                continue

            for item in result["items"]:
                article = item["article"].replace("_", " ")
                output[parse_date(item["timestamp"])][article] = item["views"]

        if not some_data_returned:
            print(Exception(f"The pageview API returned nothing useful at: ({len(urls)})"))

            for detail, count in details.items():
                print(Exception(f">>>>>>>>>({count}): {detail=}"))

            if "printurl" in sys.argv:
                print(Exception(urls))

        return output
        # except Exception as e:
        #     print(f'ERROR {e} while fetching and parsing ' + str(urls))
        #     traceback.print_exc()

        return {}

    def get_concurrent(self, urls):
        def fetch(url):
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

    def filter_data(self, data):
        # remove any key < 2015 and not = "all"
        # ---
        new_data = {}
        """
        new_data = {
            title: {k: v for k, v in views.items() if (k.isnumeric() and int(k) >= 2015) or k == "all" or v > 0}
            for title, views in data.items()
        }
        """
        # ---
        for title, views in data.items():
            new_data[title] = {
                k: v for k, v in views.items() if (k.isnumeric() and int(k) >= 2015) or k == "all" or v > 0
            }
        # ---
        return new_data

    def article_views_new(self, project, articles, **kwargs):
        # ---
        time_start = time.time()
        # ---
        dd = self.article_views(project, articles, **kwargs)
        # ---
        new_data = {}
        # ---
        for month, y in dd.items():
            # month = datetime.datetime(2024, 5, 1, 0, 0)
            year_n = month.strftime("%Y")
            for article, count in y.items():
                article = article.replace("_", " ")
                # ensure nested dict & the specific year key both exist
                article_dict = new_data.setdefault(article, {"all": 0, year_n: 0})
                # ---
                if count is not None:
                    article_dict[year_n] = article_dict.get(year_n, 0) + count
                    article_dict["all"] = article_dict.get("all", 0) + count
                # ---
                # sort article_dict keys
                article_dict = {k: v for k, v in sorted(article_dict.items(), key=lambda item: item[0])}
                # ---
                new_data[article] = article_dict
        # ---
        new_data = self.filter_data(new_data)
        # ---
        delta = time.time() - time_start
        # ---
        print(f"<<green>> article_views, (articles:{len(articles):,}) new_data:{len(new_data):,} time: {delta:.2f} sec")
        # ---
        return new_data
