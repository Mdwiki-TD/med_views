#!/usr/bin/python3
"""

from med_views.helps import count_all_langs, get_en_articles, one_lang_titles, langs_titles, load_lang_titles_from_dump
from med_views.helps import dump_one
from med_views.helps import load_languages_counts

"""
import json
import sys
from pathlib import Path

from mdapi_sql import wiki_sql

t_dump_dir = Path(__file__).parent / "titles"

if not t_dump_dir.exists():
    t_dump_dir.mkdir()


def load_lang_titles_from_dump(lang):
    # ---
    json_file = t_dump_dir / f"{lang}.json"
    # ---
    if json_file.exists():
        # ---
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ---
        data = [x.replace("_", " ") for x in data]
        return data
    # ---
    return []


def dump_one(file, data):
    # ---
    if not data:
        return
    # ---
    print(f"dump_one({file}), {len(data)=}")
    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        # json.dump(data, f, ensure_ascii=False, indent=2)


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
    result = wiki_sql.sql_new(query, "enwiki")
    # ---
    articles = [x["page_title"] for x in result]
    # ---
    return articles


def dump_all(data):
    file = Path(__file__).parent / "languages_counts.json"
    # ---
    # sort data
    data = {k: v for k, v in sorted(data.items(), key=lambda item: item[1], reverse=True)}
    # ---
    if data and len(data) > 200:
        dump_one(file, data)


def load_languages_counts():
    file = Path(__file__).parent / "languages_counts.json"
    # ---
    if file.exists():
        # ---
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    # ---
    return {}


def count_all_langs_sql():
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
    print("def count_all_langs_sql():")
    # ---
    result = wiki_sql.sql_new(query, "enwiki")
    # ---
    languages = {x["ll_lang"]: x["counts"] for x in result}
    # ---
    if "en" not in languages:
        languages["en"] = len(get_en_articles())
    # ---
    dump_all(languages)
    # ---
    return languages


def count_all_langs():
    # ---
    all_infos = load_languages_counts()
    # ---
    if not all_infos and ("local" not in sys.argv):
        return count_all_langs_sql()
    # ---
    if all_infos:
        return all_infos
    # ---
    result = {}
    # ---
    for json_file in t_dump_dir.glob("*.json"):
        lang = json_file.stem
        # ---
        with open(json_file, "r", encoding="utf-8") as f:
            result[lang] = len(json.load(f))
    # ---
    print(f"count_all_langs local: {len(result)}")
    # ---
    return result


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
    result = wiki_sql.sql_new(query, "enwiki", values=(langcode,))
    # ---
    titles = [x["ll_title"] for x in result]
    # ---
    return titles


def langs_titles():
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
    result = wiki_sql.sql_new(query, "enwiki")
    # ---
    titles = {}
    # ---
    for x in result:
        titles.setdefault(x["ll_lang"], []).append(x["ll_title"])
    # ---
    titles["en"] = get_en_articles()
    # ---
    dump_all({x: len(y) for x, y in titles.items()})
    # ---
    return titles
