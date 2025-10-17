import os

from dotenv import load_dotenv

from sommify.recipes import elastic
from sommify.recipes.reader import RecipeReader

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")

ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")

ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")


def test_elastic_search_by_query_term() -> bool:
    try:
        r = RecipeReader(ELASTIC_URL, ELASTIC_USERNAME, ELASTIC_PASSWORD)
        input_term = "reindeer"
        found_ings = r.extract_ingredients(input_term)
        elastic.search_by_query_term(r.es, input_term, found_ings)[1]
        assert True
    except Exception as e:
        print(e)
        raise AssertionError()


def test_elastic_read_terms() -> bool:
    try:
        r = RecipeReader(ELASTIC_URL, ELASTIC_USERNAME, ELASTIC_PASSWORD)
        input_term = "reindeer"
        r.read_terms(input_term)
        assert True
    except Exception as e:
        print(e)
        raise AssertionError()
