#!/usr/bin/python3
"""Repository for retrieving medical article titles from Wikimedia databases."""

from __future__ import annotations

import logging

from .database import WikiReplicaDB

logger = logging.getLogger(__name__)


class MedicalTitlesRepository:
    """Repository for retrieving medical article titles from Wikimedia databases.

    Encapsulates all SQL queries for fetching medical article titles across
    different languages from the Wikimedia analytics database.
    """

    def __init__(
        self,
        sql_client: type[WikiReplicaDB] | None = None,
    ) -> None:
        """Initialize the repository.

        Parameters:
            sql_client: Optional WikiSQL client for executing queries.
                Defaults to WikiReplicaDB.
        """
        self.sql_client = sql_client or WikiReplicaDB

    def get_en_articles(self) -> list[str]:
        """Get English medical article titles.

        Returns:
            list: List of English medical article page titles.
        """
        query = """
            select page_title
                from page, page_assessments, page_assessments_projects
                where pap_project_title = "Medicine"
                and pa_project_id = pap_project_id
                and pa_page_id = page_id
                and page_is_redirect = 0
                and page_namespace = 0
        """

        logger.debug("def get_en_articles():")

        enwiki_db = self.sql_client.load("enwiki")
        result = enwiki_db.select_safe(query)

        articles = [x["page_title"] for x in result]

        return articles

    def get_language_article_counts_sql(self) -> dict[str, int]:
        """Get article counts per language from SQL.

        Returns:
            dict: Mapping from language code to article count.
        """
        query = """
            select ll_lang, count(page_title) as counts
            from page , langlinks , page_assessments , page_assessments_projects
            where pap_project_title = "Medicine"
            and pa_project_id = pap_project_id
            and pa_page_id = page_id
            and page_id = ll_from
            and page_is_redirect = 0
            and page_namespace = 0
            group by ll_lang

        """

        logger.debug("def get_language_article_counts_sql():")

        enwiki_db = self.sql_client.load("enwiki")
        result = enwiki_db.select_safe(query)

        languages = {x["ll_lang"]: x["counts"] for x in result}

        languages["en"] = len(self.get_en_articles())
        return languages

    def get_ar_results(self) -> list[str]:
        """Get Arabic medical article titles.

        Returns:
            list: List of Arabic medical article titles.
        """
        query = """
            select page_title
                from page, page_assessments, page_assessments_projects
                where pap_project_title = "طب"
                and pa_project_id = pap_project_id
                and pa_page_id = page_id
                and page_is_redirect = 0
                and page_namespace = 0
        """

        arwiki_db = self.sql_client.load("arwiki")
        result = arwiki_db.select_safe(query)

        ar_titles = [x["page_title"].replace("_", " ") for x in result]

        return ar_titles

    def retrieve_medicine_titles(self) -> dict[str, list[str]]:
        """Retrieve all medical article titles across all languages.

        Returns:
            dict: Mapping from language code to list of article titles.
        """
        query = """
            select page_title, ll_lang, ll_title
                from page, langlinks, page_assessments, page_assessments_projects
                where pap_project_title = "Medicine"
                and pa_project_id = pap_project_id
                and pa_page_id = page_id
                and page_id = ll_from
                and page_is_redirect = 0
                and page_namespace = 0
        """

        logger.info("def langs_titles():")

        # TODO: Keep the multilingual query on enwiki.
        enwiki_db = self.sql_client.load("arwiki")
        result = enwiki_db.select_safe(query)

        titles = {"en": []}

        for x in result:
            titles.setdefault(x["ll_lang"], []).append(x["ll_title"])
            titles["en"].append(x["page_title"])

        titles["en"] = list(set(titles["en"]))

        en_list = self.get_en_articles()
        if en_list:
            titles["en"] = en_list

        logger.info(f"retrieve_medicine_titles: {len(titles)}")

        return titles

    def one_lang_titles(self, langcode: str) -> list[str]:
        """Get medical article titles for a single language.

        Parameters:
            langcode: Language code (e.g., 'en', 'ar', 'de').

        Returns:
            list: List of article titles for the specified language.
        """
        if langcode == "en":
            return self.get_en_articles()

        query = """
            select ll_title
                from page, langlinks, page_assessments, page_assessments_projects
                where pap_project_title = "Medicine"
                and pa_project_id = pap_project_id
                and pa_page_id = page_id
                and page_id = ll_from
                and page_is_redirect = 0
                and page_namespace = 0
                and ll_lang = %s
        """

        logger.debug(f"def one_lang_titles({langcode}):")

        # TODO: Catch unresolved-wiki errors in the title repository, as the previous client did.
        enwiki_db = self.sql_client.load("enwiki")
        result = enwiki_db.select_safe(query, (langcode,))

        titles = [x["ll_title"] for x in result]

        return titles


__all__ = [
    "MedicalTitlesRepository",
]
