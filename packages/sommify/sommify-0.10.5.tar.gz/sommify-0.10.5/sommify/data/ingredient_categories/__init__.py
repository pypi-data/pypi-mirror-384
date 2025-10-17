import re

from .drinks import *
from .fruit import *
from .nuts import *
from .vegetables import *


def ing_ends_with(ingredient, suffixes):
    return any(re.search(rf"{r}$", ingredient, flags=re.IGNORECASE) for r in suffixes)


def is_fruit_stone(ingredient):
    return ing_ends_with(ingredient, FRUIT_STONE)


def is_fruit_berry(ingredient):
    return ing_ends_with(ingredient, FRUIT_BERRY)


def is_fruit_melon(ingredient):
    return ing_ends_with(ingredient, FRUIT_MELON)


def is_fruit_citrus(ingredient):
    return ing_ends_with(ingredient, FRUIT_CITRUS)


def is_fruit_tropical(ingredient):
    return ing_ends_with(ingredient, FRUIT_TROPICAL)


def is_fruit(ingredient):
    return ing_ends_with(ingredient, FRUIT_DEFAULT)


def is_nut(ingredient):
    return ing_ends_with(ingredient, NUTS)


def is_vegetable_root(ingredient):
    return ing_ends_with(ingredient, VEG_ROOT)


def is_vegetable(ingredient):
    return ing_ends_with(ingredient, VEG_DEFAULT)


def is_vegetable_green(ingredient):
    return ing_ends_with(ingredient, VEG_GREEN)


def is_drink(title=""):
    return ing_ends_with(title, DRINKS)


TAG_VEGETABLES = "vegetables"
TAG_GREENS = "greens"
TAG_FRUIT = "fruits"
TAG_FRUIT_TROPICAL = "tropical fruits"
TAG_NUTS = "nuts"
TAG_BERRY = "berries"
TAG_VEGETARIAN = "vegetarian"
TAG_VEGAN = "vegan"


def tag_ingredients(ingredients=[]):
    """
    Given a list of ingredients, return a list of tags.
    """
    tags = []

    labellers = [
        (is_vegetable, TAG_VEGETABLES),
        (is_vegetable_green, TAG_GREENS),
        (is_fruit, TAG_FRUIT),
        (is_nut, TAG_NUTS),
        (is_fruit_tropical, TAG_FRUIT_TROPICAL),
        (is_fruit_berry, TAG_BERRY),
    ]

    for labeller, tag in labellers:
        for ing in ingredients:
            if labeller(ing):
                tags.append(tag)
                break

    return list(set(tags))


def tag_title(title=""):
    """
    Given a title, return a list of tags.
    """
    tags = []

    if re.search(r"\b(?:greens|vegs?|veggies?|vegetables?)\b", title):
        tags.append(TAG_VEGETABLES)
    if re.search(r"\b\fruit[sy]?\b", title):
        tags.append(TAG_FRUIT)
    if re.search(r"\b(?:nuts?|nutty)\b", title):
        tags.append(TAG_NUTS)
    if re.search(r"\b(?:berries?|berry)\b", title):
        tags.append(TAG_BERRY)
    if re.search(r"\bvegetarian\b", title):
        tags.append(TAG_VEGETARIAN)
    if re.search(r"\bvegan\b", title):
        tags.append(TAG_VEGAN)
    if re.search(r"\b(?:tropical|tutti.?frutti|exotic fruits?)\b", title):
        tags.append(TAG_FRUIT_TROPICAL)

    return list(set(tags))


def tag_recipe(title="", ingredients=[]):
    """
    Given a title and a list of ingredients, return a list of tags.
    """
    tags = []

    tags.extend(tag_title(title))
    tags.extend(tag_ingredients(ingredients))

    return list(set(tags))
