#!/usr/bin/python3
"""

"""
import logging

from .api_sql.wiki_sql import retrieve_sql_results

logger = logging.getLogger(__name__)


def get_en_articles():
    # ---
    query = """
        select page_title
            from page, page_assessments, page_assessments_projects
            where pap_project_title = "Medicine"
            and pa_project_id = pap_project_id
            and pa_page_id = page_id
            and page_is_redirect = 0
            and page_namespace = 0
    """
    # ---
    logger.debug("def get_en_articles():")
    # ---
    result = retrieve_sql_results(query, "enwiki")
    # ---
    articles = [x["page_title"] for x in result]
    # ---
    return articles


def get_language_article_counts_sql():
    # ---
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
    # ---
    logger.debug("def get_language_article_counts_sql():")
    # ---
    result = retrieve_sql_results(query, "enwiki")
    # ---
    languages = {x["ll_lang"]: x["counts"] for x in result}
    # ---
    languages["en"] = len(get_en_articles())
    return languages


def get_ar_results():
    qua = """
        select page_title
            from page, page_assessments, page_assessments_projects
            where pap_project_title = "طب"
            and pa_project_id = pap_project_id
            and pa_page_id = page_id
            and page_is_redirect = 0
            and page_namespace = 0
    """
    # ---
    result = retrieve_sql_results(qua, "arwiki")
    # ---
    ar_titles = [x["page_title"].replace("_", " ") for x in result]
    # ---
    return ar_titles


def retrieve_medicine_titles() -> dict:
    # ---
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
    # ---
    logger.info("def langs_titles():")
    # ---
    result = retrieve_sql_results(query, "enwiki")
    # ---
    titles = {"en": []}
    # ---
    for x in result:
        titles.setdefault(x["ll_lang"], []).append(x["ll_title"])
        titles["en"].append(x["page_title"])
    # ---
    titles["en"] = list(set(titles["en"]))
    # ---
    en_list = get_en_articles()
    if en_list:
        titles["en"] = en_list
    # ---
    # ar_list = get_ar_results()
    # ---
    # if ar_list: titles["ar"].extend(ar_list)
    # titles["ar"] = list(set(titles["ar"]))
    # ---
    logger.info(f"retrieve_medicine_titles: {len(titles)}")
    # ---
    return titles


def one_lang_titles(langcode):
    # ---
    if langcode == "en":
        return get_en_articles()
    # ---
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
    # ---
    logger.debug(f"def one_lang_titles({langcode}):")
    # ---
    result = retrieve_sql_results(query, "enwiki", values=(langcode,))
    # ---
    titles = [x["ll_title"] for x in result]
    # ---
    return titles
