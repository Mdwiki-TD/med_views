import pytest
from src.texts_utils import (
    make_text,
)

def test_make_text():
    languages = {"en": 10, "fr": 5}
    views = {"en": 1000, "fr": 500}
    
    # en: 1000 views / 10 articles = 100 avg
    # fr: 500 views / 5 articles = 100 avg
    
    text = make_text(languages, views)
    
    # Check headers
    assert "Total views for medical content = 1,500" in text
    assert "Total articles= 15" in text
    
    # Check table content existence
    assert "|[//en.wikipedia.org en]" in text
    assert "|10" in text # articles
    assert "|1,000" in text # views
    
    assert "|[//fr.wikipedia.org fr]" in text
    assert "|5" in text # articles
    assert "|500" in text # views
    
    # Check sorting: en (10) should come before fr (5) because sorted by articles count
    pos_en = text.find("en.wikipedia.org")
    pos_fr = text.find("fr.wikipedia.org")
    assert pos_en < pos_fr