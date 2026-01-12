#!/usr/bin/python3
"""

"""
import logging

logger = logging.getLogger(__name__)


def make_text(languages, views) -> str:
    # ---
    """
    Produce a MediaWiki-formatted block summarizing medical article counts and views by language.
    
    Parameters:
        languages (Mapping[str, int]): Mapping from language code or name to number of articles.
        views (Mapping[str, int]): Mapping from language code or name to total views.
    
    Returns:
        str: Wikitext containing a header, total views and article counts, and a sortable table with columns for rank, language (as a wiki link), number of articles, total views, and average views. Average views are computed with integer division (floor).
    """
    total_views = sum(views.values())
    total_articles = sum(languages.values())
    # ---
    text = "{{WPM:WikiProject Medicine/Total medical views by language}}\n"
    # ---
    text += f"* Total views for medical content = {total_views:,}\n"
    text += f"* Total articles= {total_articles:,}\n"
    # ---
    text += "\n"
    # ---
    text += """{| class="wikitable sortable"\n!Rank\n!Lang\n!# of articles\n!Total views\n!Ave. views\n|----"""
    # ---
    # sort languages by count
    languages = {k: v for k, v in sorted(languages.items(), key=lambda item: item[1], reverse=True)}
    # ---
    for n, (lang, articles) in enumerate(languages.items(), start=1):
        # ---
        lang_views = views.get(lang, 0)
        # ---
        Average_views = lang_views // articles if articles and lang_views else 0
        # ---
        text += (
            f"\n|{n}"
            f"\n|[//{lang}.wikipedia.org {lang}]"
            f"\n|{articles:,}"
            f"\n|{lang_views:,}"
            f"\n|{Average_views:,}"
            "\n|-"
        )
    # ---
    text += "\n|}"
    # ---
    return text