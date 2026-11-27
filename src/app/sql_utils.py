#!/usr/bin/python3
"""Repository for retrieving medical article titles from Wikimedia databases."""

from __future__ import annotations

import logging

from .api_sql.wiki_sql import WikiSQLClient

logger = logging.getLogger(__name__)


class MedicalTitlesRepository:
    """Repository for retrieving medical article titles from Wikimedia databases.

    Encapsulates all SQL queries for fetching medical article titles across
    different languages from the Wikimedia analytics database.
    """

    def __init__(
        self,
        sql_client: WikiSQLClient | None = None,
    ) -> None:
        """Initialize the repository.

        Parameters:
            sql_client: Optional WikiSQL client for executing queries.
                Defaults to WikiSQLClient.
        """
        self._sql_client = sql_client or WikiSQLClient()

    def get_en_articles(self) -> list:
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

        result = self._sql_client.retrieve_sql_results(query, "enwiki")

        articles = [x["page_title"] for x in result]

        return articles

    def get_language_article_counts_sql(self) -> dict:
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

        result = self._sql_client.retrieve_sql_results(query, "enwiki")

        languages = {x["ll_lang"]: x["counts"] for x in result}

        languages["en"] = len(self.get_en_articles())
        return languages

    def get_ar_results(self) -> list:
        """Get Arabic medical article titles.

        Returns:
            list: List of Arabic medical article titles.
        """
        qua = """
            select page_title
                from page, page_assessments, page_assessments_projects
                where pap_project_title = "طب"
                and pa_project_id = pap_project_id
                and pa_page_id = page_id
                and page_is_redirect = 0
                and page_namespace = 0
        """

        result = self._sql_client.retrieve_sql_results(qua, "arwiki")

        ar_titles = [x["page_title"].replace("_", " ") for x in result]

        return ar_titles

    def retrieve_medicine_titles(self) -> dict:
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

        result = self._sql_client.retrieve_sql_results(query, "enwiki")

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

    def one_lang_titles(self, langcode: str) -> list:
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

        result = self._sql_client.retrieve_sql_results(query, "enwiki", values=(langcode,))

        titles = [x["ll_title"] for x in result]

        return titles


# Legacy compatibility layer
_default_repo: MedicalTitlesRepository | None = None


def _get_default_repo() -> MedicalTitlesRepository:
    """Get or create the default MedicalTitlesRepository instance."""
    global _default_repo
    if _default_repo is None:
        _default_repo = MedicalTitlesRepository()
    return _default_repo


def get_en_articles():
    """Legacy entry point. Use MedicalTitlesRepository.get_en_articles instead."""
    return _get_default_repo().get_en_articles()


def get_language_article_counts_sql():
    """Legacy entry point. Use MedicalTitlesRepository.get_language_article_counts_sql instead."""
    return _get_default_repo().get_language_article_counts_sql()


def get_ar_results():
    """Legacy entry point. Use MedicalTitlesRepository.get_ar_results instead."""
    return _get_default_repo().get_ar_results()


def retrieve_medicine_titles() -> dict:
    """Legacy entry point. Use MedicalTitlesRepository.retrieve_medicine_titles instead."""
    return _get_default_repo().retrieve_medicine_titles()


def one_lang_titles(langcode):
    """Legacy entry point. Use MedicalTitlesRepository.one_lang_titles instead."""
    return _get_default_repo().one_lang_titles(langcode)


__all__ = [
    "MedicalTitlesRepository",
    "get_en_articles",
    "get_language_article_counts_sql",
    "get_ar_results",
    "retrieve_medicine_titles",
    "one_lang_titles",
]
