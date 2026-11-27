#!/usr/bin/python3
"""MediaWiki table generation utilities."""

from __future__ import annotations

import logging
from collections.abc import Mapping

logger = logging.getLogger(__name__)


class WikiTextBuilder:
    """Builder for generating MediaWiki-formatted tables and text.

    Generates formatted wiki markup for displaying medical article statistics.
    """

    def build_wiki_text(self, languages: Mapping[str, int], views: Mapping[str, int]) -> str:
        """Produce a MediaWiki-formatted block summarizing medical article counts and views.

        Parameters:
            languages: Mapping from language code to number of articles.
            views: Mapping from language code to total views.

        Returns:
            str: Wikitext containing a header, total views and article counts,
                and a sortable table with columns for rank, language (as a wiki
                link), number of articles, total views, and average views.
        """
        total_views = sum(views.values())
        total_articles = sum(languages.values())

        text = "{{WPM:WikiProject Medicine/Total medical views by language}}\n"

        text += f"* Total views for medical content = {total_views:,}\n"
        text += f"* Total articles= {total_articles:,}\n"

        text += "\n"

        text += """{| class="wikitable sortable"\n!Rank\n!Lang\n!# of articles\n!Total views\n!Ave. views\n|----"""

        # sort languages by count
        languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=True))

        for n, (lang, articles) in enumerate(languages.items(), start=1):
            lang_views = views.get(lang, 0)

            average_views = lang_views // articles if articles and lang_views else 0

            text += f"\n|{n}\n|[//{lang}.wikipedia.org {lang}]\n|{articles:,}\n|{lang_views:,}\n|{average_views:,}\n|-"

        text += "\n|}"

        return text


__all__ = [
    "WikiTextBuilder",
]
