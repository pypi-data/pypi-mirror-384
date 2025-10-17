from __future__ import annotations

# from utils import *
import html
import os
import re
import unicodedata

# from data.categories import models
import numpy as np
import pandas as pd
import spacy
from qdrant_client import QdrantClient

# from sentence_transformers import SentenceTransformer
from unidecode import unidecode

try:
    spacy.load("en_core_web_sm")
except OSError:
    print("Downloading language model for the spaCy")
    from spacy.cli import download

    download("en_core_web_sm")
    print("Download complete")


from .. import regex as rgx

# from data.ingredient_funnel import dictionary as ing_funnel
from ..data.categories import (
    exceptions,
    function_map,
    ing_keys,
    ing_map,
    models,
    proteins,
    root_map,
    title_map,
)
from ..data.embeddings import mean_ing_embedding
from ..data.ingredient_categories import is_drink

from ..data.ingredient_funnel import dictionary as ing_funnel
from ..recipes import elastic

# from ..utils import *  # noqa: F403
from ..utils import (
    I_label_protein,
    I_simplify,
    I_to_singular,
    P_duplicates,
    P_filter,
    P_juice_zest_fix,
    P_missing_multiplier_symbol_fix,
    P_multi_misc_fix,
    P_quantity_dash_unit_fix,
    Q_to_number,
    Q_U_sugar,
    Q_U_unify,
    S_unify,
    U_unify,
    flatten,
    rm_accent,
    rm_nested_bracket,
    rm_roman_numerals,
    squish_multi_bracket,
    vf,
)

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))


class RecipeReader:
    def __init__(
        self,
        es_url: str = "",
        es_user_name: str = "",
        es_pass: str = "",
        es_port: int = 9200,
        small: bool = False,
    ) -> None:
        self._attributes = ["quantity", "unit", "size", "color", "ingredient", "simple"]
        # if not small:
        en_core_web_sm = "en_core_web_sm"
        if small:
            # 	 ner
            self.nlp = spacy.load(
                en_core_web_sm,
                exclude=[
                    "tok2vec",
                    "tagger",
                    "senter",
                    "attribute_ruler",
                    "lemmatizer",
                ],
            )
        else:
            self.nlp = spacy.load(en_core_web_sm)
            # dont initiallize es object if no es parameters are given
            self.es = (
                elastic.get_es_connection(es_url, es_user_name, es_pass, es_port)
                if es_url and es_user_name and es_pass
                else None
            )

    def normalize(self, phrase: str) -> str:
        phrase = unicodedata.normalize("NFD", phrase)
        phrase = unidecode(phrase)
        phrase = phrase.lower()
        phrase = re.sub(r"\([^)]*\)", "", phrase)
        phrase = re.sub(r"\(|\)", "", phrase)

        for vulgar_fraction, fraction_str in vf.dictionary.items():
            phrase = re.sub(vulgar_fraction, " " + fraction_str + " ", phrase)

        phrase = phrase.replace("–", "-")
        phrase = phrase.replace("⁄", "/")
        phrase = re.sub(r"half ?(?:and|-) ?half", "half-and-half", phrase)
        phrase = re.sub(r"\.\.+", "", phrase)
        phrase = re.sub(r" *\. *(?![0-9])", ". ", phrase)
        phrase = re.sub(r"(?<=[0-9]) *\. *(?=[0-9])", ".", phrase)
        phrase = re.sub(r" '", "'", phrase)
        phrase = re.sub(r"(,[^,]+)?< ?a href.*", "", phrase)
        phrase = re.sub(r""" *<(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+> *""", "", phrase)
        phrase = re.sub(r"(?<=[a-z])/[a-z]+", "", phrase)
        phrase = re.sub(r"\b(?:5|five)[- ]?spice", "fivespice", phrase)
        phrase = re.sub(r".*: ?", "", phrase)
        phrase = re.sub(r"\s+", " ", phrase)
        phrase = phrase.strip()
        return phrase

    def merge_ingredients(self, ingredients: list[str]) -> list[str]:
        out = []
        out_ings = []

        for ing in ingredients:
            if ing["simple"] not in out_ings:
                out += [ing.copy()]
                out_ings += [ing["simple"]]
            else:
                for i, o in enumerate(out):
                    if o["simple"] == ing["simple"] and o["unit"] == ing["unit"]:
                        if not ing["quantity"] or not o["quantity"]:
                            continue
                        out[i]["quantity"] += ing["quantity"]

        return out

    def extract_ingredients(self, text: str) -> list:
        if not text:
            return []

        unique_ingredients = list(set(ing_funnel.values()))
        found = set()

        chunks = self.nlp(text).noun_chunks
        for chunk in chunks:
            # if plural convert to singular
            chunk = I_to_singular(chunk.text)

            if re.search(rf"\b(?:{r'|'.join(unique_ingredients)})(?:s|es)?\b", chunk):
                found.add(self.funnel(chunk))

            if rgx.PROTEIN.search(chunk):
                found.add(I_label_protein(chunk))

        return [f for f in found if f]

    def read_phrase(self, phrase: str) -> object:
        if not P_filter(str(phrase)):
            return None

        phrase = html.unescape(phrase)
        phrase = self.normalize(phrase)
        phrase = P_duplicates(phrase)

        phrase = P_multi_misc_fix(phrase)
        phrase = P_multi_misc_fix(phrase)
        phrase = P_missing_multiplier_symbol_fix(phrase)
        phrase = P_quantity_dash_unit_fix(phrase)
        phrase = P_juice_zest_fix(phrase)

        values = rgx.INGREDIENT.search(phrase).groupdict()

        values["unit"] = None
        if values["quantity"]:
            values["quantity"], values["unit"] = re.search(
                rf"(?P<quantity>{rgx.Q.pattern})? ?(?P<unit>.*)?", values["quantity"]
            ).groups()
            values["quantity"] = Q_to_number(values["quantity"])

        values["unit"] = U_unify(values["unit"])
        values["quantity"], values["unit"] = Q_U_unify(
            values["quantity"], values["unit"]
        )

        values["size"] = S_unify(values["size"])

        if values["ingredient"] != values["ingredient"] or not values["ingredient"]:
            return None

        values["ingredient"] = I_to_singular(values["ingredient"])
        values["simple"] = I_label_protein(values["ingredient"])
        values["simple"] = I_simplify(values["simple"])

        if values["simple"] == "sugar":
            values["quantity"], values["unit"] = Q_U_sugar(
                values["quantity"], values["unit"]
            )

        values["simple"] = re.sub(r"\bnan\b", "naan", values["simple"])

        filtered = {c: values[c] for c in self._attributes}
        filtered["simple"] = values["simple"]
        return filtered

    def funnel(self, phrase: str) -> any:
        return ing_funnel[phrase] if phrase in ing_funnel else None

    def clean_title(self, title: str) -> str:
        title = squish_multi_bracket(title)
        title = rm_nested_bracket(title)
        # title = rm_bracket_content(title)
        title = rm_roman_numerals(title)
        title = re.sub(r" \|.+$", "", title)
        title = re.sub(r"\bRecipe\b", "", title)
        title = re.sub(r"\s+", " ", title)
        title = html.unescape(title)
        title = rm_accent(title)
        title = title.strip(" ")
        title = title.lower()
        title = re.sub(r"\bnan\b", r"\bnaan\b", title)
        return title

    def alt_title(self, title: str) -> str:
        title = squish_multi_bracket(title)
        title = (
            re.search(r"(?:\((?P<alt_title>.*)\))?$", title)
            .groupdict()
            .get("alt_title", "")
        ) or ""
        return title.lower()

    def categorize(
        self,
        title: str,
        ingredients: list[str],
        steps: list[str] = [],
        parsed_phrases: list[str] = [],
        phrases: list[str] = [],
        processed_title: str = None,
    ) -> list:
        categories = []
        # parsed_phrases = parsed_phrases or [self.read_phrase(p) for p in phrases]

        if processed_title:
            title = self.clean_title(title)
            title_nlp = processed_title
        else:
            title = self.clean_title(title)
            title_nlp = self.nlp(title)

        # alt_nlp = self.nlp(alt_title)

        roots = [token.text.lower() for token in title_nlp if token.dep_ == "ROOT"]
        # + [
        #     token.text.lower() for token in alt_nlp if token.dep_ == "ROOT"
        # ]

        root_chunks = [
            c.text for c in title_nlp.noun_chunks if any(r in c.text for r in roots)
        ]

        if any(
            re.search(r"\b(?:" + r"|".join(exceptions) + r")$", root)
            for root in root_chunks
        ):
            return ["niche"]

        for c in root_chunks:
            if is_drink(c):
                return ["drink"]

        # if any(is for root in root_chunks):
        #     return ["niche"]

        for key in ing_keys:
            for ing in ingredients:
                if key == ing:
                    categories.append(key)
                    break

        for key, regex in ing_map.items():
            for ing in ingredients:
                if ing == regex:
                    categories.append(key)
                    break

        for key, regex in root_map.items():
            match = re.search(regex, title)
            if not match:
                continue
            if any(re.search(rf"{regex}$", r) for r in root_chunks):
                categories.append(key)
                break

            # if re.search(rf"{regex}$", title) and not re.search(
            #     r"\band\b|\bwith\b|\bin\b|&", title
            # ):
            #     categories.append(key)

        for key, regex in title_map.items():
            if re.search(regex, title):
                # or re.search(regex, alt_title):
                categories.append(key)

        for key, label_f in function_map.items():
            if label_f(ingredients=ingredients):
                categories.append(key)

        if any(p in categories for p in proteins):
            categories = [c for c in categories if c != "vegetarian"]

        if not len(categories):
            categories = ["vegetarian"]

        return list(set(categories))

    def categories_to_models(self, categories_a: str) -> list[str]:
        out = []
        for category in categories_a:
            for model, categories_b in models.items():
                if category in categories_b:
                    out.append(model)

        if len(out) == 0:
            return ["other"]

        # sort models by priority (order in models.py)
        return sorted(out, key=lambda x: list(models.keys()).index(x))

    def read_batch(
        self, recipes: list[dict[str, any]], model: str = "julie"
    ) -> list[dict[str, any]]:
        return [self.read(**r, model=model) for r in recipes]

    def read(
        self,
        title: str,
        phrases: list[str],
        steps: list[str] = list,
        ing_parsed: bool = False,
        version: str = "v1",
        model: str = "julie",
    ) -> object:
        parsed_phrases = [self.read_phrase(p) for p in phrases]
        parsed_phrases = self.merge_ingredients([p for p in parsed_phrases if p])

        if ing_parsed:
            ingredients = phrases
        else:
            ingredients = [
                self.funnel(p["simple"])
                for p in parsed_phrases
                if self.funnel(p["simple"])
            ]

        categories = self.categorize(title, ingredients, steps, parsed_phrases)

        # if the only fish is anchovy, remove the fish category
        if "fatty fish" in categories:
            if not any(
                i["ingredient"] != "anchovy" and i["simple"] == "fatty fish"
                for i in parsed_phrases
            ):
                categories.remove("fatty fish")

        columns = sorted(set(ing_funnel.values()))
        if "niche" in categories:
            categories = ["niche"]

        _models = self.categories_to_models(categories)

        values = np.array([1 if c in ingredients else 0 for c in columns])
        if version == "v2" or model == "julie05":
            values = np.append(
                values, [1 if m in _models else 0 for m in models.keys()]
            )

        return {
            "ingredients": ingredients,
            "ingredients_": parsed_phrases,
            "title": title,
            "categories": categories,
            "models": _models,
            "values": values,
        }

    def read_terms(self, input_term: str, version: str = "v1") -> object:
        input_term = re.sub(r"\s+", " ", input_term)
        found_ings = self.extract_ingredients(input_term)
        title, ings, steps = elastic.search_by_query_term(
            self.es, input_term, found_ings
        )
        return self.read(title, ings, steps, ing_parsed=True, version=version)


ING_EMBEDDING_LEN = 128
TAG_EMBEDDING_LEN = 384


class TagReader:
    def __init__(
        self,
        # ing_model,
        qdrant_host: str = "qdrant.pocketsomm.dev",
        qdrant_port: int = 443,
        qdrant_https: bool = True,
    ) -> None:
        # tag_model_path = os.path.join(ROOT_DIR, "models", "tag_embedding.model")
        # self.tag_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.tag_model = None
        # self.ing_model = ing_model

        embedding_csv_path = os.path.join(
            ROOT_DIR, "data", "mean_ing_embedding_per_tag.csv"
        )
        self.__mean_ing_e_per_tag = pd.read_csv(embedding_csv_path, index_col=[0])
        self.tags = list(self.__mean_ing_e_per_tag.columns)
        self.__mean_ing_e = np.array(mean_ing_embedding)

        self.qdrant = QdrantClient(
            host=qdrant_host, port=qdrant_port, https=qdrant_https
        )
        en_core_web_sm = "en_core_web_sm"
        self.nlp = spacy.load(en_core_web_sm)

    # def generate_ing_embedding(self, ing):
    #     return self.ing_model.wv[ing] if ing in self.ing_model.wv else None

    def generate_tag_embedding(self, tag: str) -> list:
        return self.tag_model.encode(tag)

    def get_ing_embedding_of_tag(self, tag: str) -> list:
        return self.__mean_ing_e_per_tag[tag].values

    def preprocess_tags(self, tags: list[str]) -> list[str]:
        processed_tags = []
        for tag in tags:
            closest_tag = self.get_closest_tag(tag)
            if closest_tag == tag:
                processed_tags.append(closest_tag)
            else:
                tag = " ".join(
                    [tag.text.strip() for tag in self.nlp(tag) if not tag.is_stop]
                )
                closest_tags = self.get_closest_tags(tag, n=len(tag.split()))
                processed_tags += closest_tags

        return processed_tags if processed_tags else tags

    def get_ing_embedding_by_tags(self, tags: list[str]) -> list:
        embeddings = []
        for tag in self.preprocess_tags(tags):
            embedding = self.get_ing_embedding_of_tag(tag) - self.__mean_ing_e
            embeddings.append(embedding)

        embedding_sum = sum(embeddings)
        return np.add(embedding_sum, self.__mean_ing_e)

    def get_closest_tags(self, tag: str, n: int) -> object:
        results = self.qdrant.search(
            collection_name="tag",
            query_vector=self.tag_model.encode(tag),
            limit=n,
            with_payload=True,
        )

        return [r.payload["value"] for r in results]

    def get_closest_tag(self, tag: str) -> object:
        return self.qdrant.search(
            collection_name="tag",
            query_vector=self.tag_model.encode(tag),
            limit=1,
            with_payload=True,
        )[0].payload["value"]

    def read(self, tags: list[str]) -> object:
        embedding = self.get_ing_embedding_by_tags(tags)
        search_results = self.qdrant.search(
            collection_name="recipe-ing",
            query_vector=("embedding", embedding.tolist()),
            limit=5,
            with_vectors=True,
            with_payload=True,
        )

        model_list = flatten([r.payload["models"] for r in search_results])
        most_frequent = max(set(model_list), key=model_list.count)

        for r in search_results:
            if most_frequent in r.payload["models"]:
                values = r.vector["oneHot"]
                mask = values != 0
                values[mask] = 1.0
                return {"values": np.array(values), "models": [most_frequent]}
