#!/usr/bin/python3
"""

"""

from .api_sql.wiki_sql import sql_new


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
    print("def get_en_articles():")
    # ---
    result = sql_new(query, "enwiki")
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
        #and ll_lang = 'ar'
        group by ll_lang
        #limit 10
    """
    # ---
    print("def get_language_article_counts_sql():")
    # ---
    result = sql_new(query, "enwiki")
    # ---
    languages = {x["ll_lang"]: x["counts"] for x in result}
    # ---
    if "en" not in languages:
        languages["en"] = len(get_en_articles())
    # ---
    return languages


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
    print(f"def one_lang_titles({langcode}):")
    # ---
    result = sql_new(query, "enwiki", values=(langcode,))
    # ---
    titles = [x["ll_title"] for x in result]
    # ---
    return titles


def retrieve_medicine_titles():
    # ---
    query = """
        select ll_lang, ll_title
            from page, langlinks, page_assessments, page_assessments_projects
            where pap_project_title = "Medicine"
            and pa_project_id = pap_project_id
            and pa_page_id = page_id
            and page_id = ll_from
            and page_is_redirect = 0
            and page_namespace = 0
    """
    # ---
    print("def langs_titles():")
    # ---
    result = sql_new(query, "enwiki")
    # ---
    titles = {}
    # ---
    for x in result:
        titles.setdefault(x["ll_lang"], []).append(x["ll_title"])
    # ---
    titles["en"] = get_en_articles()
    # ---
    return titles
