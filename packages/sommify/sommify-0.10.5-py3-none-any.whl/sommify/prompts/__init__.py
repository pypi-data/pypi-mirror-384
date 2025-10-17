import re

from nltk import ngrams
from thefuzz import fuzz, process
from unidecode import unidecode

from ..data.cuisine import ent_to_cui, iso_to_cui
from ..data.ingredient_funnel import dictionary as ing_funnel
from ..data.ingredients import dictionary as ing_dict
from ..regex import PROTEIN
from ..utils import I_label_protein, I_simplify, I_to_singular
from .data import default, ent_to_iso

DEFAULT_THRESHOLD = 92

unique_ingredients = list(set(ing_funnel.values()))

flatten = lambda l: [item for sublist in l for item in sublist]

ing_ptrn = r"|".join(flatten(ing_dict.values()) + unique_ingredients)
ing_ptrn = rf"\b(?:{ing_ptrn})\b"


def funnel(phrase: str) -> any:
    return ing_funnel[phrase] if phrase in ing_funnel else None


def extract_cooking_methods(text: str, nlp) -> list:
    """
    Extracts cooking methods from text. Returns a list of cooking methods. If no cooking methods are found, returns an empty list.
    """
    normalize = lambda t: unidecode(
        re.sub(r"\b(stir|pan).?fr(?:ied|y)\b", r"\1fry", t.lower())
    )
    tokens = nlp(normalize(text))

    cooking_methods = [
        "saute",
        "bake",
        "roast",
        "grill",
        "fry",
        "broil",
        "poach",
        "steam",
        "simmer",
        "stew",
        "braise",
        "blanch",
        "boil",
        "sear",
        "panfry",
        "marinate",
        "stirfry",
    ]

    return [t.lemma_ for t in tokens if t.lemma_ in cooking_methods]


def extract_ingredients(text: str, nlp) -> list:
    """
    Extracts ingredients from text. Returns a list of ingredients. If no ingredients are found, returns an empty list.
    """
    if not text:
        return []

    es_dict = {"ingredients": [], "phrases": [], "steps": []}
    es_dict["phrases"].extend(re.findall(ing_ptrn.replace("$", ""), text))

    chunks = nlp(text).noun_chunks
    for chunk in chunks:
        # if plural convert to singular
        chunk = I_to_singular(chunk.text)

        if re.search(ing_ptrn, chunk):
            simplified = I_simplify(chunk)
            if simplified in unique_ingredients:
                es_dict["ingredients"].append(funnel(simplified))

        if re.search(PROTEIN, chunk):
            es_dict["ingredients"].append(I_label_protein(chunk))

    es_dict["ingredients"] = list(set(es_dict["ingredients"]))
    es_dict["phrases"] = list(set(es_dict["phrases"]))
    es_dict["steps"] = list(set(es_dict["steps"]))
    return es_dict


def extract_cuisine(text: str, nlp) -> list:
    """
    Extracts cuisine from text. Returns a list of cuisines. If no cuisine is found, returns an empty list.
    """
    cuisines = []
    ents = [t.text for t in nlp(text).ents]

    for ent in ents:
        if ent in ent_to_iso:
            iso = ent_to_iso[ent]
            if type(iso) is list:
                # print(ent)
                # isos.extend(ent_to_iso[word])
                for key, value in ent_to_cui.items():
                    if re.match(key, ent):
                        cuisines.append(value)
            else:
                cuisines.extend(iso_to_cui[iso])

    return cuisines


def extract_mentions_naive(
    prompt,
    region_pool=default.region_pool,
    subregion_pool=default.subregion_pool,
    grape_pool=default.grape_pool,
    threshold=DEFAULT_THRESHOLD,
):
    """
    Given a prompt, extract mentions of countries (iso), regions, subregions, and grapes.
    Naive approach, fuzzy string matching.
    """

    prompt = prompt.lower()

    isos = []
    regions = []
    subregions = []
    grapes = []

    combined_pool = list(ent_to_iso.keys()) + subregion_pool + region_pool + grape_pool
    # remove accents from combined pool
    # combined_pool = [unidecode(ent) for ent in combined_pool]

    # split text to list of sentences split by punctuation
    subsentences = re.split(r"[^\w\s]+", prompt)

    for ent in combined_pool:
        for ss in subsentences:
            for ngram in ngrams(
                ss.split(),
                n=len(ent.split()),
            ):
                score = fuzz.QRatio(" ".join(ngram), unidecode(ent))

                if score >= threshold:
                    if ent in subregion_pool:
                        subregions.append(ent)
                    elif ent in region_pool:
                        regions.append(ent)
                    elif ent in grape_pool:
                        grapes.append(ent)
                    else:
                        if isinstance(ent_to_iso[ent], list):
                            isos.extend(ent_to_iso[ent])
                        else:
                            isos.append(ent_to_iso[ent])

                    prompt = prompt.replace(" ".join(ngram), "")

    # also extract years between 1900 and 2100 (inclusive)
    years = re.findall(r"\b((?:19|20)\d{2})\b", prompt)
    years = [int(y) for y in years]

    dedupe = lambda l: list(set(l))

    return {
        "countries": dedupe(isos),
        "regions": dedupe(regions),
        "subregions": dedupe(subregions),
        "grapes": dedupe(grapes),
        "years": dedupe(years),
    }


def country_entity_to_iso(entity, threshold=DEFAULT_THRESHOLD):
    """
    Given a country entity, return the iso code.
    """
    # fuzzy search for closest
    closest_match = process.extractOne(entity, ent_to_iso.keys())
    if closest_match[1] >= threshold:
        return ent_to_iso[closest_match[0]]
    else:
        return None


def region_entity_to_closest(
    entity,
    region_pool=default.region_pool,
    subregion_pool=default.subregion_pool,
    threshold=DEFAULT_THRESHOLD,
):
    """
    Given a region entity, return the closest match.
    """
    # fuzzy search for closest
    closest_match = process.extractOne(entity, region_pool + subregion_pool)
    if closest_match[1] >= threshold:
        return closest_match[0]
    else:
        return None
