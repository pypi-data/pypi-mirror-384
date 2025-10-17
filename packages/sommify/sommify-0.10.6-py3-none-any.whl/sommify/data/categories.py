# from utils import with_plural, to_regex
import re

from ..utils import to_regex, with_plural

# from data.ingredient_categories import fruits, vegetables, legumes, herbs
from .ingredient_categories import VEG_FLOWER, is_fruit, vegetables

# from data.ingredients import dictionary as ing_dict
from .ingredients import dictionary as ing_dict

# from data.meat import dictionary as meat_dict
from .meat import dictionary as meat_dict

proteins = list(meat_dict.keys())
pasta = ing_dict["pasta"]

drink_list = with_plural(
    [
        "slushy",
        "slushie",
        "colada",
        "old fashioned",
        "bitter",
        "whiskey",
        "liqueur",
        "cider",
        "cappuccino",
        "frappuccino",
        "coffee",
        "espresso",
        "cocktail",
        "beer",
        "wine",
        "rootbeer",
        "drink",
        "juice",
        "tea",
        "milk",
        "moccha",
        "shake",
        "milkshake",
        "smoothie",
        "cocoa",
        "margarita",
        "mojito",
        "smoothie",
        "gin",
        "lemonade",
        "martini",
        "soda",
        "punch",
        "fizzy",
        "ouzo",
        "mocha",
        "latte",
        "frappe",
        "limeade",
        "cafe",
        "irish cream",
        "café",
        "frappé",
        "cordial",
        "chai",
        "lassi",
        "sangria",
        "sangría",
        "sangaree",
        "sangarita",
        "aqua thunder",
        "limoncello",
        "tequini",
        "cactus bite",
        "the yellow jacket",
        "caribbean twist",
        "brazillian sunset",
        "bora bora",
        "blue hawaiian",
        "blue lagoon",
    ]
)
soup_list = with_plural(
    [
        "minestrone",
        "soup",
        "chowder",
        "bouillabaisse",
        "gazpacho",
        "gumbo",
        "bisque",
        "borscht",
        "bortsch",
        "bortscht",
        "bortsht",
        "borsht",
        "bouillon",
        "broth",
        "consomme",
        "consommé",
        "velouté",
        "veloute",
        "vichyssoise",
        "skink",
        "laksa",
        "ramen",
        "pho",
        # "miso",
        "mulligatawny",
        "goulash",
        "stew",
        "bourguignon",
        "rogan josh",
    ]
)
niche_list = with_plural(
    [
        "vinaigrette",
        "horseradish",
        "compote",
        "sauce",
        "marinade",
        "dip",
        "jam",
        "jelly",
        "queso",
        "cheese",
        "jus",
        "dressing",
        "bread",
        "cornbread",
        "spread",
        "preserve",
        "stock",
        "bouillon",
        "salsa",
        "gravy",
        "catsup",
        "ketchup",
        "relish",
        "chutney",
        "pesto",
        "syrup",
        "salsa",
        "sambal",
        "mayonnaise",
        "aioli",
        "mustard",
        "chimichurri",
        "marmalade",
        "marmelade",
        # "bar",
        "demi-glace",
    ]
)
dessert_list = with_plural(
    [
        "apple pie",
        "semifreddo",
        "waffle",
        "crepe",
        "pudding",
        "french toast",
        "torta",
        "tiramisu",
        "sundae",
        "madeleine",
        "ice cream",
        "cookie",
        r"muffin",
        r"bar",
        r"cupcake",
        r"brownie",
        r"cheesecake",
        r"pancake",
        "tart",
        "rugelach",
        "chiffon cake",
        r"biscuit",
        r"scone",
        "sorbet",
        "biscotti",
        "galette",
        "granola",
        "buttercream",
        r"doughnut",
        "crumble",
        "shortbread",
        r"mousse",
        "baklava",
        "donut",
    ]
)
sandwich_list = with_plural(
    [
        "panini",
        "sandwich",
        "burrito",
        "burger",
        "taco",
        "bruschetta",
        "baguette",
        "wrap",
        r"hot ?dog",
        "enchilada",
        "ciabatta",
    ]
)
exceptions = [
    "stock",
    "broth",
    "bouillon",
    "beefsteak",
    r"icecream",
    r"ice cream",
    r"gelato",
    r"sorbet",
    r"sherbet",
    r"frozen yogurt",
    r"custard",
    r"frozen dairy dessert",
    r"frozen dessert",
    r"ice milk",
    r"soft serve",
    r"ice pop",
    r"ice lolly",
    r"popsicle",
    r"italian ice",
    r"kulfi",
    r"ice",
]

title_map = {
    "seafood": to_regex(["ceviche"]),
    "sandwich": to_regex(sandwich_list),
    "pasta": to_regex(pasta + ["pasta", "alfredo"]),
    "sausage": to_regex(["sausage", "sausages", "chorizo"]),
    "casserole": to_regex(["casserole"]),
    # "dessert": to_regex(dessert_list),
    "soup": to_regex(soup_list),
    "pizza": to_regex([r"pizza$", r"calzone$", r"buffalina$", r"margherita$"]),
}

ing_keys = proteins + ["pasta"]

ing_map = {"spicy food": "spicy pepper", "lean fish": "seafood"}

root_map = {
    "sandwich": to_regex(sandwich_list),
    "vegetarian": to_regex(
        vegetables.VEG_DEFAULT
        + [r"mushrooms?", r"portobells?", r"brussels? sprouts?", r"tofu", r"beans?"]
    ),
    "salad": to_regex(["(?<!fruit )salad"]),
    "pasta": to_regex(pasta + ["pasta", "alfredo"]),
    "niche": to_regex(niche_list),
    "soup": to_regex(soup_list),
    "drink": rf"{to_regex(drink_list)}$",
    "pizza": to_regex(["pizza", "calzone", "buffalina", "margherita"]),
    "sushi": to_regex(
        ["nigiri", "sashimi", "chirashi", "oshizushi", "temaki", "uramaki", "sushi"]
    ),
    "mushroom": to_regex(
        [
            "mushroom",
            "portobello",
            "portabella",
            "crimini",
            "shiitake",
            "porcini",
            "morel",
            "chanterelle",
        ]
    ),
}


def is_dessert(title="", ingredients=[], phrases=[]):
    def is_dessert_ing(name=""):
        key_list = [
            "syrup",
            "molasses",
            "chocolate",
            "caramel",
            r"nut$",
            "cocoa",
            "sugar",
            "milk",
            "cinnamon",
            "vanilla",
            "honey",
            "mascarpone",
            "ricotta",
        ]
        # if name == "sugar" and quantity and quantity > 50:
        #     return True
        if is_fruit(name):
            return True

        if re.search(rf"\b(?:{r'|'.join(key_list)})\b", name):
            return True
        return False

    def is_non_dessert_ing(name):
        key_list = (
            # [h for h in herbs if not re.search(herb_exceptions, h)]
            proteins
            + VEG_FLOWER
            + [
                "pepper",
                "garlic",
                "onion",
                "shallot",
                "spinach",
                "mustard",
                "cilantro",
                "coriander",
                "cauliflower",
                "cumin",
                "sauerkraut",
                "ketchup",
                "horseradish",
                "potato",  # temporary solution
            ]
            + [
                "monterey jack cheese",
                "mexican cheese",
                "feta cheese",
                "mozzarella cheese",
                "pecorino cheese",
                "gruyere cheese",
                "pepper jack cheese",
                "cheddar cheese",
                "parmesan cheese",
                "halloumi cheese",
                "paneer cheese",
                "brie cheese",
            ]
        )
        if re.search(rf"\b(?:{r'|'.join(key_list)})\b", name):
            return True
        return False

    if all(not ing or not is_dessert_ing(ing) for ing in ingredients):
        return False

    if any(ing and is_non_dessert_ing(ing) for ing in ingredients):
        return False

    return True


function_map = {"dessert": is_dessert}


models = {
    "fish": [
        "seafood",
        "tuna",
        "lean fish",
        "salmon",
        "crustacean",
        "fatty fish",
        "other seafood",
        "octopus",
    ],
    "white-meat": [
        "poultry",
    ],
    "red-meat": [
        "game bird",
        "beef",
        "pork",
        "sausage",
        "game",
        "lamb",
        "bacon",
        "liver",
    ],
    "sweets": [
        "dessert",
    ],
    "other": [
        "soup",
        "spicy food",
        "niche",
        "ham",
        "sandwich",
        "pizza",
        "pasta",
        "casserole",
        "vegetarian",
        "salad",
    ],
}
