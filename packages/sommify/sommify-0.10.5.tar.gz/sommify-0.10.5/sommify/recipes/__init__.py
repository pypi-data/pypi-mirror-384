import html
import re
from unicodedata import normalize
import numpy as np

from unidecode import unidecode

from .. import regex as rgx
from .. import utils


def _format_attribute(attr):
    # replace spaces with underscores, and make lowercase
    return attr.lower().replace(" ", "_").replace("-", "_").replace("&", "and")


flatten = lambda l: [item for sublist in l for item in sublist]


class Ingredient:
    def __init__(self, name, regex, parents, is_vague, portions=[]):
        parents = [p.lower() for p in parents]

        self.is_protein = "protein" in parents
        self.is_vegetable = "vegetables" in parents
        self.is_root_vegetable = "roots" in parents
        self.is_fruit = "fruits" in parents
        self.is_grain = "grains" in parents
        self.is_dairy = "dairy" in parents
        self.is_cheese = "cheese" in parents
        self.is_fat = "fat" in parents
        self.is_sweet = "sweeteners" in parents or "chocolate" in parents
        self.is_spice = "spices" in parents
        self.is_herb = "herbs" in parents
        self.is_liquid = "liquids" in parents or name == "milk"
        self.is_rhizome = "rhizomes" in parents
        self.is_cabbage = "cabbage" in parents

        self.name = name
        regex = rgx.one_of(regex)
        # portion = rf"(?:{rgx.PORTION})"
        # if self.is_protein:
        #     self.pattern = re.compile(rf"\b(?:{regex})(?: {portion})?$")
        if len(portions) > 0:
            portion = rf"(?:{rgx.one_of(portions)})"
            self.pattern = re.compile(rf"\b(?:{regex})(?: {portion})?$")
        elif self.is_cheese:
            portion = (
                r"(?:slices?|cubes?|wedges?|rounds?|wheels?|cheese|rind|shavings?)"
            )
            self.pattern = re.compile(rf"\b(?:{regex})(?: {portion})?$")
        elif self.is_rhizome:
            portion = r"(?:powder|rhizomes?|root|roots?|tubers?|tuber|tubers?)"
            self.pattern = re.compile(rf"\b(?:{regex})(?: {portion})?$")
        elif self.is_cabbage:
            portion = r"(?:leaf|leaves|heads?|florets?|stalks?)"
            self.pattern = re.compile(rf"\b(?:{regex})(?: {portion})?$")
        else:
            self.pattern = re.compile(rf"\b(?:{regex})$")

        self.parents = parents
        self.is_general = is_vague

    def __repr__(self):
        return f"Ingredient(name={self.name}, parents={self.parents}, is_general={self.is_general})"

    def __str__(self):
        return f"Ingredient(name={self.name}, parents={self.parents}, is_general={self.is_general})"


class IngredientFamily:
    def __init__(self, name="", vague=None, children=[]):
        self.name = name
        self.vague = vague
        self.compiled_replacements = [
            (re.compile(pattern), replacement)
            for pattern, replacement in [
                (r"\([^)]*\)", ""),  # Remove content in parentheses
                (r"\(|\)", ""),  # Remove parentheses themselves
                (r"–", "-"),  # Replace en dash with hyphen
                (r"⁄", "/"),  # Replace fraction slash
                (
                    r"half ?(?:and|-) ?half",
                    "half-and-half",
                ),  # Standardize 'half and half' variations
                (r"\.\.+", ""),  # Remove multiple periods
                (r" *\. *(?![0-9])", ". "),  # Normalize periods around spaces
                (r"(?<=[0-9]) *\. *(?=[0-9])", "."),  # Fix decimal points
                (r" '", "'"),  # Remove space before apostrophe
                (
                    r""" *<(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+> *""",
                    "",
                ),  # Remove HTML tags
                (r"(,[^,]+)?< ?a href.*", ""),  # Remove HTML tags alternative
                (r"(?<=[a-z])/[a-z]+", ""),  # Remove text after slashes in words
                (r"\b(?:5|five)[- ]?spice", "fivespice"),  # Standardize 'five spice'
                (r".*: ?", ""),  # Remove text before colon
                (r"\s+", " "),  # Remove extra spaces
                (r"(?:1 )?& frac", "1 /"),  # Fix fractional notation
                (r"dipping sauce", "sauce"),  # Simplify 'dipping sauce'
            ]
        ]

        for name, value in children:
            setattr(self, name, value)

    def get(self, name):
        # get ingredient with matching name
        for ingredient in self.get_ingredients():
            if ingredient.name == name:
                return ingredient

    def __str__(self):
        return "\n".join([i.__str__() for i in self.get_ingredients()])

    def __repr__(self):
        return self.__str__()

    # when an index is accessed, return ingredient at that index
    def __getitem__(self, index):
        return self.get_ingredients()[index]

    # when an attribute is accessed, format it
    def __getattribute__(self, name):
        name = _format_attribute(name)
        return super().__getattribute__(name)

    # when an attribute is added to the class, format it
    def __setattr__(self, name, value):
        name = _format_attribute(name)
        super().__setattr__(name, value)

    # handle len
    def __len__(self):
        return len(self.get_ingredients())

    def run_compiled_replacements(self, phrase: str) -> str:
        for pattern, replacement in self.compiled_replacements:
            phrase = pattern.sub(replacement, phrase)
        return phrase

    def get_ingredients(self):
        # recursively loop over subcategories, adding ingredients to list
        ingredients = self.ingredients.copy() if hasattr(self, "ingredients") else []
        for _, value in self.__dict__.items():
            if isinstance(value, IngredientFamily):
                ingredients.extend(value.get_ingredients())

        return ingredients

    def register_ingredient(self, name, regex, path=[], portions=[]):
        is_vague = False
        if name.startswith("_"):
            name = name[1:]
            is_vague = True

        if len(path) == 0:
            if not hasattr(self, "ingredients"):
                self.ingredients = []
            self.ingredients.append(
                Ingredient(
                    name=name,
                    regex=regex,
                    parents=path,
                    is_vague=is_vague,
                    portions=portions,
                )
            )

        else:
            # loop over path keys, creating IngredientFamily objects as needed
            current = self
            for key in path:
                if not hasattr(current, key):
                    setattr(current, key, IngredientFamily(key))
                current = getattr(current, key)

            if not hasattr(current, "ingredients"):
                current.ingredients = []

            current.ingredients.append(
                Ingredient(
                    name=name,
                    regex=regex,
                    parents=path,
                    is_vague=is_vague,
                    portions=portions,
                )
            )

    def register_subcategory(self, name, vague, children):
        setattr(self, name, IngredientFamily(name, vague, children))

    def _normalize(self, phrase: str) -> str:
        phrase = normalize("NFD", phrase)  # normalize unicode
        phrase = unidecode(phrase)  # remove accents
        phrase = phrase.lower()  # make lowercase
        phrase = self.run_compiled_replacements(phrase)
        phrase = phrase.strip()
        return phrase

    def read_phrase(self, phrase: str) -> object:
        if not utils.P_filter(str(phrase)):
            return None

        phrase = html.unescape(phrase)
        phrase = self._normalize(phrase)
        phrase = utils.P_vulgar_fractions(phrase)
        phrase = utils.P_duplicates(phrase)
        phrase = utils.P_multi_misc_fix(phrase)
        phrase = utils.P_multi_adj_fix(phrase)
        phrase = utils.P_missing_multiplier_symbol_fix(phrase)
        phrase = utils.P_quantity_dash_unit_fix(phrase)
        phrase = utils.P_juice_zest_fix(phrase)
        phrase = utils.P_product_name_fix(phrase)
        phrase = utils.P_multi_color_fix(phrase)

        values = rgx.INGREDIENT.search(phrase).groupdict()

        values["unit"] = None
        if values["quantity"]:
            values["quantity"], values["unit"] = re.search(
                rf"(?P<quantity>{rgx.Q.pattern})? ?(?P<unit>.*)?", values["quantity"]
            ).groups()
            values["quantity"] = utils.Q_to_number(values["quantity"])

        values["unit"] = utils.U_unify(values["unit"])
        values["quantity"], values["unit"] = utils.Q_U_unify(
            values["quantity"], values["unit"]
        )

        values["size"] = utils.S_unify(values["size"])

        if values["ingredient"] != values["ingredient"] or not values["ingredient"]:
            return None

        values["ingredient"] = utils.I_to_singular(values["ingredient"])

        if values["color"]:
            ingredient_str = f"{values['color']} {values['ingredient']}"
        else:
            ingredient_str = values["ingredient"]

        # loop over ingredients, checking for a match
        best_match, best_range = None, 0
        for ingredient in self.get_ingredients():
            if ingredient.pattern.search(ingredient_str):
                match = ingredient.pattern.search(ingredient_str)
                match_range = match.end() - match.start()
                if match_range > best_range:
                    best_match, best_range = ingredient, match_range

        return best_match

    def read_phrase_batch(self, phrases: list) -> list:
        total = len(phrases)
        processed = []
        i = 0
        try:
            for phrase in phrases:
                if i % 100_000 == 0 and i != 0:
                    print(f"Processed {round(i / total * 100, 2)}% ({i}/{total})")
                processed.append(self.read_phrase(phrase))
                i += 1
        # if any error occurs, return processed data and print what index the error occurred at
        except Exception:
            print(f"Error occurred at index {i}")
            return processed

        return processed


# create baseline IngredientFamily object
cookbook = IngredientFamily()

_portions = {
    "chicken": [
        r"steak",
        r"wings?",
        # r"giblets?",
        r"necks?",
        r"thighs?",
        r"legs?",
        r"drumsticks?",
        r"breasts?",
        r"back",
        r"drumm?ettes?",
        r"fillets?",
        r"feet",
        r"hindquarters?",
        r"rumps?",
        # r"gizzards?",
        r"tenders?",
        r"nuggets?",
        r"quarters?",
        r"hal(?:f|ves)",
        r"meat",
        r"pieces?",
        r"cutlet",
        r"parts?",
        r"strips?",
        r"portions?",
        r"skin",
        r"carcass",
        r"chunks?",
        r"mince",
        # r"hearts?",
        r"escalope",
        r"supreme",
        r"crowns?",
    ],
    "fish": [
        r"fillets?",
        r"steaks?",
        r"fins?",
        r"fish",
        r"cake",
        r"pie",
        r"tail",
        # these are cheap, think bout it
        r"trimmings?",
        r"sticks?",
        r"fingers?",
        r"meat",
        r"cheeks?",
        r"loin",
        r"head",
        r"balls?",
        r"carcass",
        r"medallions?",
        r"scampi",
    ],
    "pork": [
        r"knuckles?",
        r"trotters?",
        r"shanks?",
        r"legs?",
        r"hogs?",
        r"loins?",
        r"bell(?:y|ies)",
        r"fillets?",
        r"shoulders?",
        r"necks?",
        r"heads?",
        r"spare[- ]?ribs?",
        r"ribs?",
        r"meat",
        r"butt",
        r"chop",
        r"mince",
        r"hock",
        r"rind",
        r"cheek",
        r"skin",
        r"escalope",
        r"medallions?",
        r"rack",
        r"fatback",
        # r"kidney",
        r"schnitzel",
        r"breast",
        r"brisket",
        r"cutlets?",
        r"round",
        r"ears?",
    ],
    "beef": [
        r"ribs?",
        r"shin",
        r"silver[- ]?side",
        # r"kidneys?",
        r"top[- ]?side",
        r"short[- ]?rib",
        r"prime[- ]?rib",
        r"t[- ]?bone",
        r"fillet",
        r"rump",
        r"flank",
        r"steak",
        r"hump",
        r"neck",
        r"bolo",
        r"wing[- ]?rib",
        r"chuck",
        r"brisket",
        r"round",
        r"meat",
        r"roast",
        r"mince",
        r"oxtail",
        r"shoulder",
        # r"heart",
        r"sirloin",
        r"jerky",
        r"tongue",
        r"ribs?",
        r"chunks?",
        r"shanks?",
        r"medallions?",
        r"rump",
        r"chops?",
    ],
    "lamb": [
        r"neck",
        r"shoulder",
        r"chop",
        r"rack",
        r"loin",
        r"leg",
        r"shanks?",
        r"meat",
        r"mince",
        # r"kidney",
        r"rump",
        r"fillet",
        r"cutlet",
        r"belly",
        r"rib",
        r"breast",
        r"shoulder joints?",
        r"breast joints?",
        r"rump joints?" r"rib chops?",
        r"leg chops?",
        r"double blade chops?",
        r"shoulder blade chops?",
        r"shoulder chops?",
        r"blade chops?",
        r"chump chops?",
        r"neck chops?",
        r"neck fillets?",
        r"meatballs?",
        r"double cutlets?",
        r"fore shanks?",
        r"breast ribs?",
    ],
    "sausage": [
        r"links?",
        r"rings?",
        r"casings?",
        r"meat",
        r"patty",
    ],
    "general": [
        "mince",
        "meat",
        "chunk",
        "slice",
        "portion",
        "escalope",
        "medallion",
        "paste",
        "mincemeat",
        "shin",
        "cutlet",
        "chop",
        "patty",
        "joint",
    ],
}
_portions["all"] = flatten(list(_portions.values()))

_nested_dictionary = {
    "FAT": {
        "oil": [r"oil", r"oil spray", r"cooking spray", r"canola", r"rapeseed"],
        "ghee": [r"ghee"],
        "butter": [r"butter margarine", r"margarine", r"butter", r"oleo"],
        "shortening": [r"shortening", r"crisco"],
        "fat": [r"suet", r"grease", r"drippings?", r"lard", r"fat", r"schmaltz"],
    },
    "EGG": {
        "egg": [
            r"(?<!chocolate )\beggs?",
            r"egg (?:beater )?substitute",
            r"egg wash",
        ],
        "egg yolk": [
            r"egg yolks?",
            r"yolks? of (?:the |an )?egg",
            r"yolks?",
        ],
        "egg white": [
            r"egg white",
            r"egg white substitute",
            r"whites? of (?:the |an )?egg",
            r"egg glair",
            r"albumen",
        ],
    },
    "HERBS": {
        "FLOWERS": {
            "lavender": [r"lavender(?: flower| petal)?"],
            "hibiscus": [r"hibiscus(?: flower| petal)?"],
            "rose": [r"rose(?: flower| petal)?"],
            "chamomile": [r"chamomile(?: flower| petal)?"],
            "_flower": [r"flower", r"blossom", r"petal"],
        },
        "LEAVES": {
            "tea": [r"tea", r"chai", r"tea powder", r"matcha(?: powder)?"],
            "nettle": [r"nettle", r"nettle lea(?:f|ves)"],
            "mint": [r"mint leaf", r"mint"],
            "shiso": [r"shiso"],
            "basil": [r"basil leaf", r"\bbasil"],
            "cilantro": [
                r"c[ui]lantro",
                r"coriander(?: cress)?",
                r"bandhania",
            ],
            "dill": [r"dill weed", r"dill"],
            "oregano": [r"oregano"],
            "thyme": [r"thyme leaf", r"thyme leave", r"thyme"],
            "parsley": [r"parsley", r"parsley leaf", r"parsley flake"],
            "rosemary": [r"rosemary leaf", r"rosemary"],
            "fenugreek": [
                r"fenugreek",
                r"fenugreek leaf",
                r"methi",
                r"methi leaf",
                r"greek clover",
                r"kasuri methi",
            ],
            "lovage": [r"lovage"],
            "sage": [r"\bsage leaf", r"\bsage", r"sage herb"],
            "epazote": [r"epazote(?: leaf| leaves| herbs?| sprigs?| stalks?)?"],
            "tarragon": [r"tarragon leaf", r"tarragon"],
            "chive": [r"\bchive", r"\bchive stalk"],
            "garlic chive": [r"garlic chives?", r"chinese chives?"],
            "bay leaf": [r"bay leaf", r"bay leaves?", r"bay"],
            "lemon balm": [r"lemon balm"],
            "lemongrass": [
                r"lemon ?grass",
                r"citronella",
                r"lemon verbena",
                r"lemon catnip",
            ],
            "marjoram": [r"marjoram"],
            "chervil": [r"chervil"],
            "savory": [r"savory", r"savory herb"],
            "watercress": [r"watercress(?: salad)?"],
            "sorrel": [r"sorrel"],
            "arugula": [r"arug[ua]la", r"roquette", r"rocket", r"rucola"],
            "curry": [r"curry leaf", r"curry leaves"],
            #
            "_herb": [r"herbs?", r"herb mix", r"herb blend", r"bouquet garni"],
        },
        "SPROUTS": {
            # "alfalfa": [r"alfalfa sprouts?"],
            # "bean sprout": [r"bean sprouts?"],
            # "lentil sprout": [r"lentil sprouts?"],
            # "mung bean sprout": [r"mung bean sprouts?"],
            # "radish sprout": [r"radish sprouts?"],
            # "sunflower sprout": [r"sunflower sprouts?"],
            "_sprout": [r"sprouts?", r"pea shoots?"],
        },
    },
    "FUNGI": {
        "MUSHROOMS": {
            "morel mushroom": [r"\bmorels?\b"],
            "cremini mushroom": [
                r"button mushrooms?",
                r"cremini(?: mushrooms?)?",
                r"baby port[oa]bell[oa]",
                r"chestnut.*mushrooms?",
                r"baby bella(?: mushrooms?)",
                r"brown.*mushroom",
                r"crimini(?: mushrooms?)?",
            ],
            "chanterelle": [
                r"chant[ea]?relle(?: mushrooms?)?",
                r"girolle(?: mushrooms?)?",
                r"golden.*mushroom",
            ],
            "black mushroom": [r"black.*mushroom"],
            "enoki mushroom": [r"enoki", r"beech", r"shimeji"],
            "oyster mushroom": [r"oyster", r"trumpet.*mushroom"],
            "shiitake mushroom": [
                r"shiitake",
                r"chinese.*mushroom",
                r"japanese.*mushroom",
            ],
            "porcini mushroom": [r"porcini", r"bolet", r"king mushroom"],
            "champignon mushroom": [
                r"field mushroom",
                r"port[ao]bell[ao]",
                r"straw mushroom",
                r"large mushroom",
                r"champignon",
            ],
            "lion's mane": [r"lion'?s mane", r"bearded tooth", r"pom pom"],
            "maitake": [r"maitake", r"hen[- ]of[- ]the[- ]woods"],
            "_mushroom": [r"mushroom", r"mushroom cap", r"mushroom stem"],
        },
        "TRUFFLE": {
            "white truffle": [r"white truffle"],
            "black truffle": [r"black truffle", r"perigord truffle"],
            "winter truffle": [r"winter truffle"],
            "summer truffle": [r"summer truffle"],
            "burgundy truffle": [r"burgundy truffle"],
            "_truffle": [r"(?<!chocolate )truffle"],
        },
    },
    "PASTA": {
        "noodles": [r"noodles?", r"noodle nest", r"ramen"],
        "pasta": [
            r"tricolore",
            r"fusillipasta",
            r"rigatoni",
            r"rotini",
            r"ziti",
            r"rigat[ie]",
            r"macaroni elbow",
            r"fusilli lunghi",
            r"pasta shell",
            r"pasta shapes?",
            r"vermicelli",
            r"gnocchi",
            r"manicotti(?: shells?)",
            r"spaghetti",
            r"penne",
            r"pappardelle",
            r"orecchiette",
            r"tagliatelle",
            r"macaroni",
            r"linguine",
            r"farfalle",
            r"fusilli",
            r"fettuccine",
            r"capellini",
            r"lasagn[ea]",
            r"angel hair",
            r"dital[io]ni",
            r"paccheri",
            r"tort[ei]glioni",
            r"cavatelli",
            r"conchiglie",
            r"orzo",
            r"risoni",
            r"ravioli",
            r"tortell[io]ni",
            r"\bpasta",
            r"spagg?hettini",
        ],
    },
    "GRAINS": {
        "rice": [
            r"\brice(?: grains?)?",
            r"\barborio(?: grains?)?",
            r"\bbasmati(?: grains?)?",
            r"\bbaldo(?: grains?)?",
            r"carnarolli(?: grains?)?",
            r"maratelli(?: grains?)?",
            r"vialone nano",
        ],
        "couscous": [r"cous[- ]?cous(?: grains?)?"],
        "buckwheat": [r"buckwheat(?: grains?)?"],
        "quinoa": [r"quinoa(?: grains?)?"],
        "millet": [r"millet(?: grains?)?"],
        "barley": [r"barley(?: grains?)?"],
        "oat": [r"oat(?: grains?)?", r"oatmeal(?: grains?)?"],
        "bulgur": [r"bulgh?[au]r (?:wheat|grains?|berry|berries)", r"bulgh?[au]r"],
        "farro": [r"farro(?: grains?)?"],
        "amaranth": [r"amaranth(?: grains?)?"],
        "teff": [r"teff(?: grains?)?"],
        "spelt": [r"spelt(?: grains?| berry| berries)?"],
        "sorghum": [r"sorghum(?: grains?)?"],
        "wheat": [r"wheat(?: grains?| berry| berries)?"],
        "rye": [r"rye(?: grains?| berry| berries)?"],
        "hominy": [r"hominy(?: grains?)?"],
        "germ": [r"germs?"],
        "_grain": [r"grains?"],
    },
    "FLOUR": {
        "wheat flour": [
            r"whole[ -]?(?:meal|wheat) flour",
            r"graham flour",
            r"teff flour",
            r"oat flour",
            r"buckwheat flour",
            r"quinoa flour",
            r"rye flour",
            r"spelt flour",
            r"sorghum flour",
            r"chickpea flour",
            r"gram flour",
            r"masa harina",
            r"amaranth flour",
            r"barley flour",
            r"rice flour",
            r"millet flour",
            r"corn ?flour",
            r"cornmeal",
            r"indian meal",
            r"potato flour",
            r"semolina flour",
            r"semolina",
            r"cream of wheat",
            r"farina",
            r"meal",
        ],
        "polenta": [r"polenta", r"grits?"],
        "bran": [r"bran", r"bran flake"],
        "_flour": [r"flour", r"all-purpose flour"],
    },
    "SAUCES & CONDIMENTS": {
        "cassareep": [r"cassaree?p"],  # a thick black sauce made from cassava root
        "gochujang": [r"gochujang", r"kochujang"],  # a Korean chili paste
        "yuzu kosho": [r"yuzu kosho"],  # a Japanese citrus chili paste
        "ssamjang": [r"ssamjang"],
        "bechamel": [r"bechamel sauce", r"white sauce", r"bechamel", r"cream sauce"],
        "salsa sauce": [r"salsa", r"rotel tomato chilies", r"^rotel"],
        "worcestershire sauce": [
            r"worcestershire(?: sauce)?",
            r"brown sauce",
            r"steak sauce",
            r"a\.?1\.?",
            r"hp sauce",
        ],
        "salsa verde": [r"salsa verde"],
        "hummus": [r"hummus"],
        "guacamole": [r"guacamole"],
        "barbecue sauce": [
            r"barbecue sauce",
            r"bbq sauce",
            r"diana original sauce",
        ],
        "teriyaki sauce": [r"teriyaki sauce"],
        "adobo sauce": [r"chipotle pepper adobo sauce"],
        "soy sauce": [
            r"shoyu",
            r"ketjap manis?",
            r"kecap manis?",
            r"soya? sauce",
            r"tamari",
            r"tamari sauce",
            r"tamari seasoning",
            r"maggi(?: liquid)?(?: sauce| seasoning)?",
            r"knorr(?: liquid)?(?: sauce| seasoning)?",
        ],
        "hoisin sauce": [r"hoisin.*sauce"],
        "tomato sauce": [
            r"pizza sauce",
            r"tomato sauce",
            r"tomato puree",
            r"passata(?: sauce)?",
            r"marinara(?: dipping)?(?: sauce)?",
        ],
        "fish sauce": [
            r"nam pla",
            r"fish sauce",
            r"shrimp sauce",
            r"anchovy sauce",
            r"oyster sauce",
            r"seafood sauce",
            r"nuoc mam",
            r"nuoc cham",
        ],
        "fish paste": [
            r"fish paste",
            r"shrimp paste",
            r"anchovy paste",
        ],
        "enchilada sauce": [r"enchilada sauce"],
        "cranberry sauce": [r"cranberry sauce", r"berry cranberry sauce"],
        "hot sauce": [
            r"pepper.*sauce",
            r"sriracha",
            r"adobo sauce",
            r"hot sauce",
            r"tabasco(?: sauce)?",
            r"chill?[ei] sauce",
            r"buffalo sauce",
            r"habanero sauce",
        ],
        "garlic sauce": [r"garlic sauce"],
        "chili paste": [
            r"chill?i?[iey].*paste",
            r"adobo.*(?:paste|sauce)",
            r"ranchero.*sauce",
            r"sambal oelek",
            r"harissa",
            r"harissa paste",
            r"pepper paste",
            r"chipotle paste",
        ],
        "cheese sauce": [r"cheese sauce", r"alfredo sauce"],
        "curry paste": [r"curry.*paste"],
        "bean paste": [r"bean paste"],
        "tomato paste": [r"tomato.*(paste|concentrate)"],
        "grain mustard": [r"grainy? mustard"],
        "dijon mustard": [r"dijon mustard", r"dijon"],
        "mustard": [r"mustard"],
        "mayonnaise": [r"miracle whip", r"mayo", r"mayonnaise"],
        "remoulade": [r"remoulade"],
        "pesto": [r"pesto"],
        "tahini": [
            r"tahin[ai](?: sauce| paste| dressing)?",
            r"sesame (paste|dressing|sauce)",
        ],
        "ketchup": [r"ketchup", r"catsup", r"cetchup"],
        "_sauce": [r"sauce", r"dip"],
    },
    "SPICES": {
        "PEPPERCORN": {
            "white pepper": [r"(?:whole )?white (?:ground |whole )?pepper(?:corns?)?"],
            "pink pepper": [r"(?:whole )?pink (?:ground |whole )?pepper(?:corns?)?"],
            "sichuan pepper": [
                r"(?:whole )?sz?[ei]ch[uw]an (?:ground |whole )?pepper(?:corns?)?",
                r"pimi?ento berr(?:ies|y)",
                r"sansho pepper",
                r"japanese pepper",
                r"cubeb pepper",
                r"australian mountain pepper",
            ],
            "green peppercorn": [
                r"(?:whole )?green (?:ground |whole )?peppercorns?",
            ],
            "black pepper": [
                r"(?:whole )?black (?:ground |whole )?pepper(?:corns?)?",
                r"^pepper(?:corns?)?",
                r"pepper powder",
                r"ground pepper(?:corns?)?",
                r"black pepper(?:corns?)?",
                r"^pepper(?:corns?)?",
                r"grains of paradise",
            ],
        },
        "SEASONINGS": {
            "shichimi": [r"shichimi", r"togarashi", r"nanami"],
            "italian seasoning": [
                r"italian spices?(?: mix| blend)?",
                r"italian herbs?",
                r"italian.*seasoning(?: mix| blend)?",
            ],
            "greek seasoning": [
                r"greek.*seasoning(?: mix| blend)?",
                r"greek.*spices?(?: mix| blend)?",
            ],
            "herbes de provence": [
                r"herbes? de provence(?: seasoning| seasoning mix| seasoning blend| mix| blend)?",
            ],
            "sazon goya": [r"sazon goya"],
            "za'atar seasoning": [
                r"za'?atar(?: seasoning| seasoning mix| seasoning blend| mix| blend| spice mix| spice)?"
            ],
            "jerk seasoning": [r"jerk spice", r"jerk seasoning"],
            "_seasoning": [r"seasoning", r"seasoning mix", r"seasoning blend"],
        },
        "BAKING SPICES": {
            "cinnamon": [r"(cinn?amm?on|cassia)(?: stick| bark| powder)?"],
            "nutmeg": [r"nutmeg"],
            "allspice": [r"all ?spice(?: berry| berries)?"],
            "clove": [r"cloves?"],
            "mace": [r"mace"],
            "licorice": [r"licorice(?: root| stick| powder)?"],
            "anise": [
                r"anise(?: essence| extract| powder)",
                r"aniseed(?: powder)?",
                r"anise seed(?: powder)?",
                r"star anise",
            ],
            "vanilla": [
                r"vanilla essence",
                r"^vanilla",
                r"vanilla extract",
                r"vanilla pod",
                r"vanilla bean",
                r"vanilla bean paste",
                r"vanilla paste",
            ],
            "cardamom": [
                r"cardamom powder",
                r"cardamom",
                r"cardamom pods?",
                r"cardamom seeds?",
            ],
            "almond extract": [
                r"almond extract",
                r"almond essence",
                r"almond oil",
                r"almond flavoring",
                r"almond paste",
            ],
            "_baking spice": [r"baking spices?"],
        },
        "OTHER": {
            "msg": [
                r"accent seasoning",
                r"msg",
                r"monosodium glutamate",
                r"glutamate",
            ],
            "masala": [r"masala(?: powder| mix| blend| seasoning)?"],
            "ras el hanout": [
                r"moroccan spice",
                r"ras? el hanout(?: spice)?(?: mix)?",
            ],
            "sumaq": [r"suma[cq]"],
            "paprika": [r"paprika"],
            "onion powder": [
                r"onion granules?",
                r"onion powder",
                r"onion flakes?",
            ],
            "garlic powder": [
                r"garlic granules?",
                r"garlic flakes?",
                r"garlic powder",
            ],
            "salt": [
                r"\bsalt(?:.*pepper)?",
                r"\bsalt",
                r"sea-salt",
                r"salt flakes?",
                r"salt substitute",
                r"fleur de sel",
                r"salt;",
            ],
            "annatto": [
                r"annatto(?: paste)?",
                r"achiote(?: paste)?",
                r"roucou",
                r"recado rojo",
            ],  # mexican blend of spices
            "mustard powder": [r"mustard powder"],
            "coriander powder": [r"coriander powder"],
            "fivespice": [r"fivespice(?: powder| blend)?"],
            "spicy powder": [
                r"cayenne(?: pepper)?",
                r"chill?[iey] powder",
                r"(?:chipotle|habanero|poblano|pepperoncino|cayenne).*powder",
                r"chill?[eiy] flakes?",
                r"pepper flakes?",
            ],
            "saffron": [r"saffron(?: threads?| strands?| powder)?"],
            "curry powder": [r"curry.*powder", r"curry"],
            "amchur": [r"amchur", r"mango powder", r"amchoor"],
            "asafoetida": [r"asafoetida", r"hing", r"asafoetida powder"],
            "lemon pepper": [r"lemon[- ]?pepper"],
            "_spice": [r"\bspices?"],
        },
    },
    "NUTS": {
        "cashew": [r"\bcashew(?: nut)?s?"],
        "chestnut": [r"(?<!water )chest ?nuts?"],
        "walnut": [r"walnuts?(?: hal(?:f|ves))?"],
        "peanut": [r"peanuts?", r"groundnuts?"],
        "almond": [r"almonds?", r"macadamia(?: nuts?)?", r"candlenuts?"],
        "pistachio": [r"pistachio(?: nuts?)?", r"pistachios?"],
        "pecan": [r"pecan(?: nuts?)?"],
        "hazelnut": [r"hazel ?nuts?"],
        "pine nut": [r"pine ?nuts?"],
        "_nut": [r"\bnuts?", r"sacha inchi", r"acorns?", r"butternuts?"],
    },
    "SEEDS": {
        "chia": [r"chia(?: seed)?"],
        "anise": [r"anise(?: seed)?"],
        "mustard seed": [r"mustard seed"],
        "sesame": [r"sesame seeds?", r"sesame"],
        "poppy": [r"poppy seeds?", r"poppy"],
        "sunflower seed": [r"sunflower seed", r"sunflower"],
        "flaxseed": [r"flaxseed", r"linseed"],
        "ajwain": [r"ajwain", r"ajwain seeds?", r"lovage seeds?"],
        "pumpkin seed": [r"pumpkin seed", r"pepitas?"],
        "cumin": [
            r"cumin(?: powder)?",
            r"jeera(?: powder)?",
            r"nigella seed",
            r"caraway(?: seed)?",
        ],
        "_seed": [r"\bseed"],
    },
    "VEGETABLES": {
        "OTHER": {
            "eggplant": [
                r"eggplants?",
                r"aubergines?",
                r"brinjal",
                r"guinea squash",
            ],
            "asparagus": [r"asparagus spears?", r"asparagus tips?", r"asparagus"],
            "samphire": [r"samphire"],  # similar to asparagus
            "cucumber": [r"cucumbers?"],
            "tomato": [r"tomato(?:es)?"],
            "tomatillo": [r"tomatillos?", r"husk tomato(?:es|s)?"],
            "artichoke": [r"(?<!jerusalem )artichokes?(?: hearts?)?"],
            "corn": [
                r"\bmaize",
                r"ear corn",
                r"mexican corn",
                r"sweetcorn",
                r"mexicorn",
                r"corn cob",
                r"white corn",
                r"kernel",
                r"corn niblet",
                r"corn",
                r"shoepeg corn",
            ],
            "hot pepper": [
                r"piri piri",
                r"roquito(?: pepper)?",
                r"chipotle chile",
                r"chill?[iey](?: pepper)?",
                r"hot pepper",
                r"jalapeno(?: pepper)?",
                r"serrano pepper",
                r"poblano(?: pepper)?",
                r"scotch bonnet(?: pepper)?",
                r"habanero(?: pepper)?",
                r"aji (?:dulce|amarillo|panca)(?: pepper)?",
                r"peppadew(?: pepper)?",
                r"chipotle(?: pepper)?",
                r"pepperoncin[io](?: pepper)?",
                r"italian pepper",
                r"espelette pepper",
                r"banana pepper",
                r"anaheim chili",
                r"pimi?ento(?: pepper)?",
                r"\bchile",
                r"\bchilly",
                r"\bchilis?",
                r"cherry pepper",
                r"romano pepper",
                r"padron pepper",
                r"new mexico pepper",
                r"locoto(?: pepper)?",
                r"lime pepper",
                r"thai pepper",
                r"ancho pepper",
                r"ancho chill?[eiy]",
                r"[^^]pepper",
            ],
            "bell pepper": [
                r"piquillo peppers?",
                r"green peppers?",
                r"yellow pepperw?",
                r"capsicum",
                r"bell peppers?",
                r"sweet peppers?",
                r"cubanelle peppers?",
                r"red peppers?",
                r"orange peppers?",
            ],
            "okra": [
                r"okra",
                # r"ladyfinger" # this needs to be solved in the future
            ],
        },
        "SQUASH": {
            "pumpkin": [r"pumpkin", r"jack-o-lantern", r"jack o lantern"],
            "zucchini": [r"zucchinis?", r"courgettes?"],
            "pattypan squash": [r"pattypan squash", r"pattypan"],
            "acorn squash": [r"acorn squash", r"acorn pumpkin", r"pepper squash"],
            "butternut squash": [r"butternut squash", r"butternut pumpkin"],
            "_squash": [r"squash", r"summer squash", r"winter squash", r"chayote"],
        },
        "LEGUMES": {
            "sprout": [r"\bsprouts?"],
            "lentil": [r"\blentil(?:s?| bean)"],
            "pea": [r"^snow", r"\bpea(?:s?| bean)", r"petit pois", r"mangetout"],
            "dal": [
                r"\bchann?a\b",
                r"\bur[ai]d\b",
                r"\btoor\b",
                r"\bdhal",
                r"\bdal",
                r"\bpulse",
            ],
            "edamame": [r"\bsoy beans?", r"\bedamame(?:s?| bean)"],
            "chickpea": [r"\bchickpeas?", r"\bbengal\b", r"\bgarbanzo\b"],
            "bean": [
                r"\brajma\b",
                r"\bbeans?",
                r"bean kidney",
                r"\bcannellini(?:s?| bean)",
            ],
        },
        "ROOTS": {
            "OTHER": {
                "wasabi": [r"wasabi(?: paste|\*| powder)?"],
                "horseradish": [r"horseradish"],
                "radish": [r"radish(?:es)?"],
                "burdock": [r"burdock"],
                "carrot": [r"carrot"],
                "daikon": [r"daikon", r"daikon radish(?:es)?"],
                "parsnip": [r"parsnip"],
                "turnip": [r"turnip", r"swede", r"rutabaga"],
                "beet": [r"beet", r"beetroot"],
                "celery": [r"celery(?: sticks?| roots?| hearts?| ribs?)?", r"celeriac"],
                "fennel": [r"fennel(?: bulb| root)?"],
            },
            "TUBERS": {
                "sunchoke": [r"sunchoke", r"jerusalem artichoke"],
                "bamboo shoot": [r"bamboo shoot", r"bamboo"],
                "oca": [r"oca"],
                "potato": [
                    r"potato",
                    r"spud",
                    r"french fry",
                    r"tater",
                    r"tater tots?",
                    r"potato flakes?",
                    r"hash brown",
                ],
            },
            "TUBEROUS": {
                "jicama": [r"jicama", r"yam bean"],
                "cassava": [r"cassava", r"yucc?a"],
                "sweet potato": [
                    r"sweet potato",
                    r"kumara",
                    r"batata",
                    r"camote",
                    r"boniato",
                ],
                "yam": [r"yam"],
                "yacon": [r"yacon"],
                "ube": [r"ube"],
            },
            "CORMS": {
                "taro": [r"taro", r"dasheen", r"malanga"],
                "eddoe": [r"eddoe"],
                "water chestnut": [r"water chestnut"],
                "konjac": [r"konjac"],
            },
            "RHIZOMES": {
                "ginger": [
                    r"ginger ?(?:root|paste|powder)",
                    r"root ginger",
                    r"ginger",
                ],
                "gingseng": [r"gings?eng"],
                "turmeric": [r"turmeric"],
                "galangal": [r"galangal"],
                "arrowroot": [r"arrowroot"],
            },
            "ALLIUM": {
                "leek": [r"leeks?", r"leek stalks?"],
                "ramp": [r"ramps?", r"wild leeks?"],
                "scallion": [
                    r"green onions?",
                    r"spring onions?",
                    r"scallions?",
                    r"onion tops?",
                    r"scallion tops?",
                ],
                "pearl onion": [
                    r"pearl onions?",
                    r"baby onions?",
                    r"pickling onions?",
                    r"cocktail onions?",
                ],
                "wild garlic": [
                    r"vineale",
                    r"crow garlic",
                    r"buckrams?",
                    r"wild garlic",
                    r"ramsons?",
                    r"bear'?s? (?:garlic|leek|onion)",
                    r"cowleeks?",
                    r"ramps?",
                ],
                "garlic": [
                    r"garlics?",
                    r"garlic cloves?",
                    r"garlic bulbs?",
                    r"garlic heads?",
                    r"garlic paste",
                ],
                "shallot": [r"shallots?", r"eschal?lots?"],
                "onion": [r"\bonions?", r"onion rings?"],
            },
            #
            "_root vegetable": [
                r"root vegetables?",
                r"root veggies?",
                r"root veg",
            ],
        },
        "LEAVES": {
            "BEET": {
                "chard": [r"(?:swiss )?chard"],
                "spinach": [r"spinach(?: lea(?:f|ves))?"],
                #
                "_beet greens": [r"beet ?greens?"],
            },
            "LETTUCE": {
                "romaine lettuce": [
                    r"romaine(?: lettuce| lettuce heart)?",
                    r"cos(?: lettuce)?",
                    r"co lettuce",
                ],
                "iceberg lettuce": [r"iceberg(?: lettuce)?", r"crisphead(?: lettuce)?"],
                "butter lettuce": [
                    r"butter lettuce",
                    r"boston lettuce",
                    r"bibb(?: lettuce)?",
                ],
                #
                "_lettuce": [
                    r"(?:head |heart |leaf |leaves )?lettuce",
                    r"lettuce(?: head| heart| leaf| leaves)?",
                ],
            },
            "CHICORY": {
                "ENDIVE": {
                    "escarole": [r"escaroles?"],
                    "puntarelle": [r"puntarelles?"],
                    "belgian endive": [r"belgian endives?", r"witloofs?"],
                    "_endive": [r"endives?", r"frisee"],
                },
                "OTHER": {
                    "radicchio": [r"radicchio"],
                },
                "_chicory": [r"chicory"],
            },
            "CABBAGE": {
                "broccoli": [
                    r"broccoli",
                    r"broccolini",
                    r"broccoli (rabe|florets?)",
                ],
                "cauliflower": [r"cauliflower"],
                "romanesco": [r"romanesco", r"romanesco broccoli"],
                "red cabbage": [r"red cabbage", r"purple cabbage", r"january king"],
                "savoy cabbage": [r"savoy cabbage"],
                "napa cabbage": [
                    r"napp?a(?: cabbage| leaf)?",
                    r"chinese(?: cabbage| leaf)",
                    r"wombok(?: cabbage| leaf)?",
                ],
                "bok choy": [r"bok cho[iy]", r"pak cho[yi]"],
                "kale": [r"\bkale", r"cavolo nero"],
                "collard": [r"collard greens?", r"collards?"],
                "brussels sprout": [r"brussels? sprouts?"],
                "kohlrabi": [r"kohlrabis?", r"german turnips?", r"turnip cabbage"],
                #
                "kimchi": [r"kimchi"],
                "sauerkraut": [r"sauer ?kraut"],
                "_cabbage": [r"cabbage", r"kraut"],
            },
            #
            "_greens": [r"greens?", r"salad", r"microgreens?"],
        },
        #
        "_vegetable": [r"vegetables?", r"veg", r"^veggies?"],
    },
    "FRUITS": {
        "SAVORY": {
            "avocado": [r"avocado(?: pears?)?", r"alligator pears?"],
            "olive": [r"olives?", r"olive fruit"],
            "caper": [r"capers?", r"caper berr(?:y|ies)"],
        },
        "BERRY": {
            "blueberry": [r"blueberr(?:ies|y)?"],
            "strawberry": [r"strawberr(?:ies|y)?"],
            "raspberry": [r"raspberr(?:ies|y)?"],
            "blackberry": [r"blackberr(?:ies|y)?"],
            "gooseberry": [r"gooseberr(?:ies|y)?"],
            "elderberry": [r"elderberr(?:ies|y)?"],
            "cranberry": [r"cranberr(?:ies|y)?"],
            "lingonberry": [r"lingon ?berr(?:ies|y)?"],
            "huckleberry": [r"huckleberr(?:ies|y)?"],
            "currant": [r"redcurrant", r"currant", r"currant ?berr(?:y|ies)"],
            #
            "_berry": [
                r"berr(?:ies|y)",
                r"olallieberr(?:y|ies)",
                r"cloudberr(?:y|ies)",
                r"barberr(?:y|ies)",
            ],
        },
        "MELONS": {
            "cantaloupe": [r"cantaloupe", r"muskmelon", r"rockmelon"],
            "honeydew melon": [r"honeydew", r"honeydew melon"],
            "watermelon": [r"watermelon"],
            #
            "_melon": [r"melon"],
        },
        "TROPICAL": {
            "jackfruit": [r"jackfruit", r"jakfruit"],
            "guava": [r"guava"],
            "banana": [r"bananas?", r"plantains?"],
            "lychee": [r"lychee", r"litchi"],
            "kiwi": [r"kiwi fruit", r"kiwi", r"chineese gooseberry"],
            "mango": [r"mango(?:es)?"],
            "papaya": [r"papayas?"],
            "passion fruit": [r"passion ?fruits?"],
            "pineapple": [
                r"pineapple rings?",
                r"pineapple",
                r"pineapple tidbits?",
                r"pineapple chunks?",
                r"ananas",
            ],
            "coconut": [
                r"coconut",
                r"coconut meat",
                r"coconut flakes?",
                #
                r"cream of coconut",
                r"coconut extract",
                r"cream coconut",
            ],
            "heart of palm": [
                r"hearts? of palm",
                r"palm hearts?",
                r"palm cores?",
                r"palmito",
                r"chonta",
            ],
            "dragonfruit": [r"dragonfruit", r"pitaya"],
            "starfruit": [r"starfruit", r"carambola"],
            "tamarind": [r"tamarindo?( pulp| paste)?"],
            #
            "_tropical fruit": [r"tropical fruits?"],
        },
        "APPLES & PEARS": {
            "apple": [r"apples?", r"apple ?sauce"],
            "pear": [r"pears?"],
            "quince": [r"quinces?"],
        },
        "CITRUS": {
            "lemon": [r"lemon", r"citron"],
            "lime": [r"lime"],
            "tangerine": [r"tangerine", r"clementine", r"mandarine?(?: orange)?"],
            "orange": [r"orange", r"orange sections?"],
            "grapefruit": [r"grapefruit"],
            "kumquat": [r"kumquat"],
            #
            "_citrus": [r"citrus", r"citrus fruit"],
            "ZEST": {
                "lime zest": [r"lime(?:'s)? (zest|rind|peel)"],
                "orange zest": [r"orange(?:'s)? (zest|rind|peel)"],
                "grapefruit zest": [r"grapefruit(?:'s)? (zest|rind|peel)"],
                "tangerine zest": [r"tangerine(?:'s)? (zest|rind|peel)"],
                "lemon zest": [r"lemon(?:'s)? (zest|rind|peel)", r"zest"],
            },
            "JUICE": {
                "lemon juice": [
                    r"lemon juice",
                    r"lemonade concentrate",
                    r"lemon extract",
                ],
                "lime juice": [r"lime juice", r"limeade", r"limeade concentrate"],
                "orange juice": [
                    r"orange juice",
                    r"orange juice concentrate",
                    r"oj",
                    r"orange extract",
                ],
                "grapefruit juice": [r"grapefruit juice"],
            },
        },
        "OTHER": {
            "date": [r"dates?"],
            "fig": [r"figs?"],
            "grape": [r"grapes?"],
            "acai": [r"acai"],
            "ackee": [r"ackee"],
            "cactus": [r"cactus", r"prickly pear"],
            "plum": [r"plums?", r"prunes?"],
            "pomegranate": [r"pomegranates?"],
            "cherry": [r"cherr(?:ies|y)"],
            "rhubarb": [r"rhubarb"],
            "peach": [r"peach(?:es)?", r"nectarines?"],
            "apricot": [r"apricots?"],
            "persimmon": [r"persimmons?", r"kaki"],
        },
        #
        "_fruit": [r"fruits?", r"fruit salad"],
    },
    "DAIRY": {
        "CREAM": {
            "light cream": [
                r"light cream",
                r"nonfat cream",
                r"half cream",
                r"single cream",
                r"half and half",
                r"half-and-half",
                r"table cream",
                r"coffee cream",
                r"creamer",
            ],
            "whipped cream": [r"cool whip", r"whipped cream"],
            "sour cream": [
                r"creme fraiche",
                r"sour(?:ed)? cream",
                r"schmand",
                r"mexican cream",
                r"mexican crema",
            ],
            "clotted cream": [r"clotted cream", r"devonshire cream"],
            "ice cream": [r"ice cream"],
            "heavy cream": [
                r"double cream",
                r"whipping cream",
                r"thick cream",
                r"3[0-8] ?% ?cream",
                r"(?<!ice )cream",
            ],
        },
        "CHEESE": {
            "HARD CHEESE": {
                "manchego": [r"manchego(?: cheese)?"],
                "cantal": [r"cantal(?: cheese)?"],
                "parmesan": [
                    r"parmesan cheese",
                    r"parmesan",
                    r"grana? padano",
                    r"parmigiano",
                    r"parmigiano regg?iano",
                    r"regg?iano",
                ],
            },
            "SEMI-HARD CHEESE": {
                "gloucester": [r"gloucester(?: cheese)?"],
            },
            "SEMI-SOFT CHEESE": {
                "taleggio": [r"tall?egg?io(?: cheese)?"],
            },
            "SOFT CHEESE": {
                "munster": [r"munster(?: cheese)?"],
                "livarot": [r"livarot(?: cheese)?"],
                "reblochon": [r"reblochon(?: cheese)?"],
                "epoisses": [r"epoisse?s?(?: cheese)?"],
                "chaource": [r"chaource(?: cheese)?"],
                "brie": [
                    r"brie(?: cheese)?",
                    r"camembert(?: cheese)?",
                ],
            },
            "BLUE CHEESE": {
                "gorgonzola": [r"gorgonzola(?: cheese)?"],
                "roquefort": [r"roquefort(?: cheese)?"],
                "stilton": [r"stilton(?: cheese)?"],
                "danish blue": [r"danish blue(?: cheese)?"],
                "bleu": [r"bleu(?: cheese)?"],
                "fourme d'ambert": [r"fourme d'ambert(?: cheese)?"],
                "cabrales": [r"cabrales(?: cheese)?"],
                "_blue cheese": [
                    r"blue cheese",
                    r"blue cheese crumble",
                ],
            },
            "FRESH CHEESE": {
                "mozzarella": [
                    r"mozzarella cheese",
                    r"mozzarella",
                    r"stracciatella",
                    r"stracciatella cheese",
                    r"fior ?di ?latte",
                    r"burrata",
                    r"bocconcini",
                ],
                "stracchino": [r"stracchino(?: cheese)?", r"crescenza", r"robiola"],
                "ricotta": [r"ricotta"],
                "mascarpone": [r"mascarpone"],
                "cottage cheese": [
                    r"cottage cheese",
                    r"cottage",
                    r"farmers? cheese",
                    r"pot cheese",
                    r"curd cheese",
                    r"curd",
                    r"quark",
                    r"t[vw][aeo]ro[gh]",
                ],
                "mexican cheese": [
                    r"queso fresco",
                    r"mexican cheese(?: blend)?",
                    r"asadero",
                    r"panela",
                    r"queso blanco",
                    r"queijo",
                    r"queijo fresco",
                ],
                "cream cheese": [r"cream cheese", r"neufchatel", r"fromage frais"],
            },
            "OTHER": {
                "pecorino": [r"pecorino", r"romano"],
                "comte": [r"comte"],
                "monterey jack": [
                    r"monterey jack(?: cheese)?(?: blend)?",
                    r"pepper ?jack(?: cheese)?(?: blend)?",
                ],
                "feta": [r"\bfeta"],
                "gruyere": [r"gruyere(?: cheese)?"],
                "swiss cheese": [r"swiss cheese", r"emmenth?al(?:er)?"],
                "cheddar": [
                    r"cheddar cheese",
                    r"cheddar(?: cheese(?: blend| round| mix)?)?",
                    r"caerphilly(?: cheese(?: blend| round| mix)?)?",
                ],
                "paneer": [r"pan(?:ee|i)r(?: cheese)?"],
                "halloumi": [
                    r"halloumi(?: cheese)?",
                    r"hellim(?: cheese)?",
                    r"hallumi(?: cheese)?",
                    r"cypriot cheese",
                ],
                "goat cheese": [
                    r"goat'?s? cheese(?: blend| round| mix)?",
                    r"chevre",
                    r"chevre cheese",
                    r"chevre log",
                    r"chevre roll",
                    r"humboldt fog",
                    r"crott?in de chavignol",
                ],
                #
                "_cheese": [
                    r"fontina",
                    r"gouda",
                    r"cheese(?: (?:blend|rolls?|mix|rounds?|wedges?|slices?|food))?",
                    r"provolone",
                    r"asiago",
                    r"ei?dam",
                    r"colby",
                    r"havarti",
                    r"jarlsberg",
                    r"boursin",
                    r"langres?",
                    r"landj(?:ae|a)ger",
                    r"chaume",
                    r"cacic?ocavallo",
                    r"selles? sur cher",
                    r"beaufort",
                ],
            },
        },
        "MILK & YOGHURT": {
            "milk": [r"\bmilk", r"soymilk"],
            "yoghurt": [
                r"sour(?:ed)? milk",
                r"buttermilk",
                r"yogh?o?urt",
                r"yoghurt",
                r"kefir",
                r"cultured milk",
                r"labneh",
            ],
            "milk powder": [
                r"milk powder",
                r"powdered milk",
                r"dried milk",
                r"dehydrated milk",
            ],
        },
    },
    "BAKING": {
        "OTHER": {
            "sorbet": [r"sorbet"],
            "meringue": [r"meringue"],
            "nut butter": [r"(?:nut|cashew|almond).*butter"],
            "nutella": [r"nutella", r"nougat"],
            "butterscotch": [r"butterscotch"],
            "caramel": [
                r"caramel",
                r"toffee",
                r"dulce de leche",
                r"caramel sauce",
                r"caramel topping",
            ],
            "custard": [r"custard", r"creme anglaise", r"custard powder"],
            "icing": [r"icing", r"frosting", r"buttercream"],
            "sprinkle": [r"sprinkle"],
            "marzipan": [r"marzipan(?: chunks?)?"],
            "baking powder": [r"baking powder", r"baking powder mix"],
            "baking soda": [
                r"baking soda",
                r"sodium bicarbonate",
                r"bicarbonate of soda",
            ],
            "cream of tartar": [
                r"cream tartar",
                r"cream of tartar",
                r"potassium bitartrate",
            ],
            "maraschino cherry": [r"glace cherry"],
            "english pudding": [r"english pudding", r"christmas pudding"],
            "yorkshire pudding": [r"yorkshire pudding"],
            "pudding": [r"pudding", r"pudding mix"],
            "baking mix": [
                r"batter",
                r"baking (mix|dough)",
                r"bread (mix|dough)",
                r"cornbread (mix|dough)",
                r"pancake (mix|dough)",
                r"biscuit (mix|dough)",
                r"muffin (mix|dough)",
                r"cake (mix|dough)",
                r"bisquick",
            ],
            "pizza dough": [r"pizza dough", r"pizza base", r"pizza crust"],
            "pie crust": [
                r"pie dough",
                r"pie shell",
                r"crust pie",
                r"pie crust",
                r"pastry shell",
                r"pastry dough",
                r"pastry",
                r"pastry crust",
                r"cracker crust",
                r"cracker crumb",
                r"shortcrust pastry",
            ],
            "wafer": [r"wafers?"],
            "sponge cake": [r"sponge cake", r"genoise", r"angel food cake"],
            "cake": [r"pound cake", r"madeira cake", r"cake"],
            "food coloring": [r"colou?ring", r"colou?ring paste", r"food dye"],
            "rice paper": [
                r"rice paper",
                r"spring roll wrapper",
                r"spring wrapper",
                r"egg roll wrap",
            ],
            "wonton wrapper": [r"wonton wrapper"],
            "puff pastry": [r"puff pastry"],
            "phyllo pastry": [r"(phyllo|filo)(?: pastry| dough)?"],
        },
        "BREADS & ROLLS": {
            "pretzel": [r"pretzel", r"pretzel roll"],
            "roll": [
                r"roll",
                r"bun",
                r"^french",
                r"^crescent",
                r"^kaiser",
                r"hoagie",
                r"crescent dinner",
                r"french baguette",
                r"baguette",
                r"brioche",
                r"croissants?",
                r"challah",
                r"bara",
            ],
            "toast": [r"toast", r"toast bread"],
            "bread": [r"bread", r"ciabatta", r"english muffin", r"sourdough"],
            "cookie": [r"cookies?", r"gingersnap", r"oreos?"],
            "ladyfinger": [
                r"ladyfingers?",
                r"ladyfinger biscuits?",
                r"savoiardi",
                r"sponge fingers?",
                r"sponge biscuits?",
            ],
            "biscuit": [r"biscuits?"],
            "cracker": [r"cracker", r"matzo"],
            "tortilla": [r"tortilla", r"egg wraps?", r"tostadas?", r"taco shells?"],
            "flatbread": [
                r"naan",
                r"chapati",
                r"roti",
                r"flatbread",
                r"lavash",
                r"pita breads?",
                r"pitas?",
                r"pita pockets?",
                r"arepas?",
                r"arepa bread",
                r"injera",
            ],
        },
        "SWEETENERS": {
            "sugar": [
                r"sugar substitute",
                r"sugar blend",
                r"jaggery",
                r"sweetener",
                r"splenda",
                r"splenda blend",
                r"splenda granular",
                r"sugar",
            ],
            "glucose": [r"glucose", r"glucose syrup"],
            "stevia": [r"stevia"],
            "molasses": [r"molasses", r"molass", r"treacle"],
            "syrup": [r"syrup", r"agave nectar", r"sirup", r"stroop"],
            "honey": [r"honey", r"miele?", r"honeycomb"],
        },
        "CHOCOLATE": {
            "cocoa": [r"(?:cacao|cocoa)(?: nib| powder)?"],
            "coffee": [
                r"black cofee",
                r"espresso",
                r"coffee",
                r"espresso powder",
                r"coffee granule",
                r"coffee powder",
                r"\bcoffee beans?\b",
                r"espresso bean",
            ],
            "dark chocolate": [
                r"bitter chocolate",
                r"black chocolate",
                r"dark chocolate",
                r"bittersweet chocolate",
                r"semisweet chocolate",
            ],
            "white chocolate": [r"white chocolate", r"white baking chocolate"],
            "chocolate": [
                r"chocolate shavings?",
                r"chocolate bars?",
                r"chocolate baking squares?",
                r"chocolate",
                r"chocolate squares?",
                r"chocolate chips?",
                r"chocolate morsels?",
                r"chocolate curls?",
                r"chocolate sauce",
                r"chocolate buttons?",
                r"ganache",
            ],
        },
    },
    "LIQUIDS": {
        "COCKTAILS": {
            "sweet sour mix": [r"^mix", r"sour mix"],
            "grenadine": [r"grenadine"],
        },
        "OTHER": {
            "flower water": [r"flower ?water", r"rose ?water", r"blossom ?water"],
            "sparkling water": [
                r"sparkling water",
                r"carbonated water",
                r"seltzer water",
                r"club soda",
                r"soda water",
                r"mineral water",
                r"tonic water",
            ],
            "sugary soda": [
                r"soda pop",
                r"soda",
                r"pop",
                r"cola",
                r"sprite",
                r"fanta",
                r"pepsi",
                r"coke",
                r"lemonade",
            ],
            "_water": [
                r"water",
            ],
        },
        "STOCKS & SOUPS": {
            "chicken stock": [
                r"chicken (?:stock|stock powder|broth|bouillon|granule|juice|consomme|veloute|base|soup base)(?: powder)?"
            ],
            "vegetable stock": [
                r"(?:vegetable|veggie|veg) stock",
                r"(?:vegetable|veggie|veg) stock powder",
                r"(?:vegetable|veggie|veg) broth",
                r"(?:vegetable|veggie|veg) bouillon",
                r"(?:vegetable|veggie|veg) bouillon powder",
                r"(?:vegetable|veggie|veg) granule",
                r"(?:vegetable|veggie|veg) juice",
                r"v8(?: vegetable| veggie| veg)? juice",
                r"v8",
            ],
            "beef stock": [
                r"beef (?:stock|stock powder|broth|bouillon|granule|juice|consomme|veloute|base|soup base)(?: powder)?"
            ],
            "fish stock": [
                r"dashi",
                r"bonito stock",
                r"(?:fish|seafood|crab|mussel) (?:stock|stock powder|broth|bouillon|granule|juice|consomme|veloute)(?: powder)?",
            ],
            "pork stock": [
                r"pork (?:stock|stock powder|broth|bouillon|granule|juice|consomme|veloute)(?: powder)?"
            ],
            "bouillon cube": [r"bouillon cube", r"bouillon granule", r"stock cube"],
            "stock": [
                r"(?:stock|stock powder|broth|bouillon|granule|consomme|veloute)(?: powder)?"
            ],
            "chicken soup": [r"chicken soup"],
            "mushroom soup": [r"mushroom soup"],
            "onion soup": [r"onion soup"],
            "tomato soup": [r"tomato soup"],
            "vegetable soup": [r"potato soup", r"vegetable soup", r"celery soup"],
            "soup mix": [r"soup mix"],
            "soup": [r"soup", r"bisque", r"chowder", r"stew"],
        },
        "ALCOHOL": {
            "irish cream": [r"irish cream", r"bailey's"],
            "beer": [r"\bbeer", r"\bale", r"\bstout", r"lager", r"guinness"],
            "whiskey": [r"whiske?y", r"scotch"],
            "vodka": [r"\bvodka"],
            "cider": [r"c[iy]der"],
            "citrus liqueur": [r"limoncello", r"orange liqueur", r"margarita mix"],
            "fruit liqueur": [r"amarett[oi]", r"curacao"],
            "liqueur": [
                r"rumchata",
                r"\brum",
                r"spirit",
                r"rum extract",
                r"liqueur",
                r"liquor",
                r"cachaca",
                r"calvados?",
                r"creme de cacao",
                r"frangelico",
                r"rum",
                r"amarula cream liqueur",
                r"ouzo",
                r"kirsch",
                r"bourbon",
                r"brandy",
                r"gin",
                r"kahlua",
                r"grand marnier",
                r"cognac",
                r"triple sec",
                r"vodka",
                r"tequila",
                r"brandy",
                r"bitters?",
                r"cointreau",
                r"schnapps?",
                r"cachaca",
                r"eggnog",
                r"campari",
                r"bourbon",
                r"galliano",
                r"pernod",
                r"creme the menthe",
                r"drambuie",
                r"creme de cassis",
                r"chambord",
                r"tia maria",
                r"cordial",
                r"armagnac",
            ],
            "fortified wine": [
                r"marsala(?: wine)?",
                r"vin santo",
                r"m[ea]deira(?: wine)?",
                r"port wine",
                r"mistell?a wine",
                r"\bport",
                r"vermouth",
                r"sherry wine",
                r"sherry",
            ],
            "rice wine": [
                r"shaoxing wine",
                r"rice wine",
                r"cooking wine",
                r"^sake",
                r"chinese wine",
                r"mirin",
            ],
            "red wine": [r"\bred wine", r"merlot"],
            "white wine": [
                r"white wine",
                r"prosecco",
                r"champagne",
                r"wine",
                r"vinho",
                r"vin(?: jaune| blanc)?",
            ],
        },
        "_liquid": [r"liquid", r"fluid", r"juice", r"beverage"],
    },
    "VINEGAR & ACIDS": {
        "vinaigrette": [r"vinaigrette"],
        "wine vinegar": [r"wine vinegar"],
        "cider vinegar": [r"c[iy]der vinegar"],
        "balsamic vinegar": [r"balsamic vinegar"],
        "rice vinegar": [r"rice vinegar"],
        "pickle juice": [r"pickle juice", r"jalapeno juice", r"pickling juice"],
        "vinegar": [r"vinegar"],
    },
    "SEAWEED": {
        "GREEN SEAWEED": {
            "umibudo": [r"umi ?budo", r"sea grapes?", r"green caviar"],
            "sea lettuce": [r"sea lettuce", r"green laver"],
        },
        "BROWN SEAWEED": {
            "wakame": [r"wakame(?: seaweed)?"],
            "arame": [r"arame(?: seaweed)?"],
            "hiijiki": [r"hiijiki(?: seaweed)?"],
            "kombu": [r"kombu(?: seaweed)?", r"konbu", r"kelp"],
        },
        "RED SEAWEED": {
            "dulse": [r"dulse(?: seaweed)?", r"dillisk"],
            "nori": [r"nori(?: seaweed)?", r"laver"],
            "carrageenan": [r"carrageenan"],
        },
        "_seaweed": [r"seaweed", r"algae"],
    },
    "NICHE": {
        "jam": [
            r"jam",
            r"jelly",
            r"preserves?",
            r"fruit spread",
            r"marm[ea]lade",
            r"confiture",
        ],
        "puree": [r"puree"],
        "chutney": [r"chutney(?: relish| sauce)?", r"piccalilli"],
        "crouton": [r"croutons?"],
        "vegemite": [r"vegemite", r"marmite"],
        "granola": [r"granola", r"granola cereal"],
        "corn flakes": [r"corn ?flakes?( crumbs?| cereal)?"],
        "marshmallow": [r"marshmallows?", r"marshmallow fluff"],
        "stuffing": [r"stuffing mix", r"stuffing"],
        "filling": [r"filling"],
        "topping": [r"topping"],
        "dressing": [r"dressing(?: mix)?"],
        "miso": [r"\bmiso", r"soybean paste", r"miso paste"],
        "yeast": [r"yeast"],
        "gravy": [r"\bgravy", r"gravy mix"],
        "bone": [r"\bbones?"],
        "liquid smoke": [r"liquid smoke"],
        "pickle": [
            r"pickle",
            r"gherkin",
            r"pickled cucumber",
            r"cornichon",
            r"relish",
        ],
        "coleslaw": [r"coleslaw", r"coleslaw mix"],
        "pico de gallo": [r"pico de gallo"],
        "tortilla chip": [r"tortilla chip", r"corn chip"],
        "breadcrumb": [r"bread ?crumbs?", r"panko"],
        "raisin": [r"sultanas?", r"raisins?"],
        "cream of tartar": [r"cream tartar", r"potassium bitartrate"],
        "ice": [r"ice cube", r"\bice"],
    },
    "TOOLS": {
        "parchment paper": [r"parchment paper", r"baking paper"],
        "toothpick": [r"toothpick"],
        "foil": [r"foil", r"aluminum foil"],
        "skewer": [r"skewer"],
    },
    "THICKENING AGENTS": {
        "gelatin": [r"gelatine?(?: powder)?", r"agar agar(?: powder)?"],
        "xanthan gum": [r"xanthan gum"],
        "starch": [
            r"starch",
            r"cornstarch",
            r"pectin",
        ],
        "tapioca": [r"tapioca"],
        "_thickening agent": [r"thickening agent", r"thickener"],
    },
    "PROTEIN": {
        "SEAFOOD": {
            "FISH": {
                "LEAN FISH": {
                    "grouper": [r"grouper"],
                    "sea bream": [r"sea bream"],
                    "carp": [r"carp"],
                    "bonita": [r"bonita"],
                    "bass": [r"bass", r"branzino"],
                    "skate": [r"skate"],
                    "squeteague": [r"squeteague"],
                    "catfish": [r"catfish"],
                    "flounder": [r"flounder"],
                    "tilefish": [r"tilefish"],
                    "cod": [r"cod"],
                    "skrei": [r"skrei"],
                    "hake": [r"hake"],
                    "hoki": [r"hoki"],
                    "sole": [r"sole"],
                    "snapper": [r"snapper"],
                    "perch": [r"perch"],
                    "haddock": [r"haddock"],
                    "halibut": [r"halibut"],
                    "greenland turbot": [r"greenland turbot"],
                    "pike": [r"pike"],
                    "tilapia": [r"tilapia"],
                    "swai": [r"swai"],
                    "whitefish": [r"whitefish"],
                    "mahi mahi": [r"mahi[- ]?mahi"],
                    "barramundi": [r"barramundi"],
                    "char": [r"(?<!arctic )char"],
                    "trout": [r"trout"],
                    "pollock": [r"pollock"],
                    "cobia": [r"cobia"],
                    "croaker": [r"croaker"],
                    "mullet": [r"mullet"],
                    "rockfish": [r"rockfish"],
                    "whiting": [r"whiting"],
                    "saury": [r"saury"],
                    "plaice": [r"plaice"],
                    "john dory": [r"john dory"],
                    "grenadier": [r"grenadier"],
                    "kingklip": [r"kingklip"],
                    "sanddab": [r"sanddab"],
                    "sandperch": [r"sandperch"],
                    "brill": [r"brill"],
                    #
                    "_lean fish": [r"lean fish"],
                },
                "FATTY FISH": {
                    "herring": [r"herring"],
                    "eel": [r"eel"],
                    "trout": [r"trout"],
                    "arctic char": [r"arctic char"],
                    "butterfish": [r"butterfish"],
                    "mackerel": [r"mackerel"],
                    "anchovy": [r"^anchov(?:y|ies)"],
                    "sardine": [r"sardines?"],
                    "swordfish": [r"swordfish"],
                    "shark": [r"shark"],
                    "monkfish": [r"monk[- ]?fish"],
                    "bluefish": [r"bluefish"],
                    "wahoo": [r"wahoo"],
                    "turbot": [r"(?<!greenland )turbot"],
                    #
                    "salmon": [r"salmon"],
                    "yellowtail": [r"yellowtail(?: tuna)?", r"hamachi", r"amberjack"],
                    "tuna": [r"tuna"],
                    #
                    "_fatty fish": [r"fatty fish", r"oily fish"],
                },
                "_fish": [r"fish"],
                # what portions there can be for ALL fish (e.g. fillet, steak, etc.)
                "_portions": [
                    r"steaks?",
                    r"collars?",
                    r"tails?",
                    r"belly",
                    r"fillets?",
                    r"steaks?",
                    r"fins?",
                    r"fish",
                    r"cakes?",
                    r"pies?",
                    r"tails?",
                    # these are cheap, think bout it
                    r"trimmings?",
                    r"sticks?",
                    r"fingers?",
                    r"meat",
                    r"cheeks?",
                    r"loin",
                    r"head",
                    r"balls?",
                    r"carcass",
                    r"medallions?",
                    r"scampi",
                ],
            },
            "SHELLFISH": {
                "CRUSTACEANS": {
                    "lobster": [r"lobsters?", r"lobsterette?s?"],
                    "langoustine": [r"langoustines?"],
                    "crab": [r"crabs?", r"crabmeat", r"crabmeat blend"],
                    "shrimp": [
                        r"shrimps?",
                        r"prawns?",
                        r"scampi",
                        r"carabineros?",
                    ],
                    "crawfish": [r"cra[wy][ -]?(?:fish|daddy|dad)"],
                    #
                    "_crustacean": [r"crustaceans?"],
                },
                "MOLLUSKS": {
                    "clam": [r"clams?"],
                    "oyster": [r"oysters?"],
                    "mussel": [r"mussels?"],
                    "scallop": [r"scallops?"],
                    "cockle": [r"cockles?"],
                    "abalone": [r"abalones?"],
                    "conch": [r"conch(?:es)?"],
                    "whelk": [r"whelks?"],
                    "periwinkle": [r"periwinkles?"],
                    "snail": [r"snails?", r"escargots?"],
                    "limpet": [r"limpets?"],
                    "sea urchin": [r"sea urchins?", r"uni"],
                    #
                    "_mollusk": [r"mollusks?"],
                },
                "ECHINODERMS": {
                    "sea cucumber": [r"sea cucumbers?"],
                    "sea urchin": [r"sea urchins?", r"uni"],
                    "sea lily": [
                        r"sea lilies?",
                        r"comatulid",
                        r"sea lily",
                        r"crinoids?",
                    ],
                    "starfish": [r"starfish"],
                    "sand dollar": [r"sand dollars?"],
                    "brittle star": [r"brittle stars?"],
                    #
                    "_echinoderm": [r"echinoderms?", r"echinodermata"],
                },
                #
                "_shellfish": [r"shellfish"],
            },
            "CEPHALOPODS": {
                "squid": [r"squid"],
                "octopus": [r"octopus"],
                "calamari": [r"calamari"],
                "cuttlefish": [r"cuttle[- ]?fish"],
            },
            "OTHER": {
                "roe": [r"roe", r"caviar", r"tobiko", r"ikura"],
                "bonito flakes": [r"bonito flakes", r"katsuobushi"],
                "furikake": [r"furikake"],
                "_seafood": [r"seafood"],
            },
        },
        "MEAT": {
            "WHITE MEAT": {
                "POULTRY": {
                    "chicken": [
                        r"chickens?",
                        r"hens?",
                        r"poussins?",
                        r"capons?",
                        r"roosters?",
                    ],
                    "turkey": [r"turkeys?"],
                    "_portions": _portions["chicken"],
                },
                "OTHER": {
                    "alligator": [r"alligators?"],
                    "crocodile": [r"crocodiles?"],
                    "rabbit": [r"rabbits?", r"bunn(?:y|ies)", r"hares?"],
                    "squirrel": [r"squirrels?"],
                    "frog": [r"frogs?", r"frog legs?"],
                    "_portions": _portions["all"],
                },
                "_portions": _portions["general"],
            },
            "HAM & BACON": {
                "ham": [
                    r"mortadellas?",
                    r"\bhams?",
                    r"pancetta(?: (?:di )?cubetti)?",
                    r"prosciutto",
                    r"jamon(?: iberico)?",
                    r"jambon",
                    r"capicola",
                    r"culatello",
                    r"gammon",
                    r"serrano",
                    r"bresaola",
                    r"lomo",
                ],
                "bacon": [
                    r"bacon bits?",
                    r"bacon",
                    r"lardons?",
                    r"lardo(?: bacon)?",
                    r"rashers?",
                    r"speck",
                    r"guanciale",
                    r"szalonna",
                    r"lap yuk",
                ],
            },
            "RED MEAT": {
                "CATTLE": {
                    "bison": [r"bison"],
                    "buffalo": [r"buffalo"],
                    "beef": [
                        r"beef",
                        #
                        r"simms?",
                        r"jerky",
                        r"short[- ]?rib",
                        r"prime[- ]?rib",
                        r"new york strip",
                        r"cow",
                        r"entrec[oô]te",
                        r"fill?et mignon",
                        r"loin",
                        r"tenderloin",
                        r"sirloin",
                        r"wagyu",
                        r"marrow",
                        r"rib[ \-]?eye",
                        r"oxtail",
                        r"steak",
                        r"^ground meat",
                        r"^minced? ?meat",
                        r"^stew meat",
                        r"^meat",
                        r"^roast",
                        r"^chuck",
                        r"hamburger",
                        r"^round",
                    ],
                    "pastrami": [r"pastrami"],
                    "_portions": _portions["beef"],
                },
                "LAMB": {
                    "lamb": [r"lamb", r"mutton", r"hogget"],
                    "_portions": _portions["lamb"],
                },
                "PORK": {
                    "pork": [
                        r"pork",
                        r"pig",
                        r"swine",
                        r"hog",
                        r"^ribs?",
                        r"chicharron",
                    ],
                    "_portions": _portions["pork"],
                },
                "OTHER": {
                    "veal": [r"veal"],
                    "_portions": _portions["beef"],
                },
            },
            "GAME": {
                "WINGED GAME": {
                    "pigeon": [r"pigeon", r"squab"],
                    "quail": [r"quail"],
                    "partridge": [r"partridge"],
                    "crane": [r"cranes?"],
                    "goose": [r"gooses?"],
                    "duck": [r"ducks?"],
                    "pheasant": [r"pheasants?"],
                    "grouse": [r"grouses?"],
                    "guinea fowl": [r"guinea fowls?"],
                    "woodcock": [r"woodcocks?"],
                    "teal": [r"teals?"],
                    "snipe": [r"snipes?"],
                    "thrush": [r"thrushs?"],
                    "starling": [r"starlings?"],
                    "lapwing": [r"lapwings?"],
                    "_portions": _portions["chicken"],
                },
                "BIG GAME": {
                    "goat": [r"goats?"],
                    "venison": [
                        r"venisons?",
                        r"deers?",
                        r"elks?",
                        r"mooses?",
                        r"caribous?",
                        r"antelopes?",
                        r"pronghorns?",
                        r"reindeers?",
                    ],
                    "boar": [r"boars?"],
                    "kangaroo": [r"kangaroos?"],
                    "bear": [r"bears?"],
                    "ostrich": [r"ostrich"],
                    "emu": [r"emu"],
                    "_portions": _portions["all"],
                },
            },
            "SAUSAGE": {
                "salami": [
                    r"coppas?",
                    r"cap[io]collos?",
                    r"porco( \w+)?",
                    r"salamis?",
                    r"pepperonis?",
                    r"longanizas?",
                    r"longganisas?",
                    r"soppressatas?",
                    r"saucissons?(?: sec)?",
                    r"finocchionas?",
                ],
                "liver sausage": [
                    r"liverwurst",
                    r"braunschweiger",
                    r"liver sausage",
                    r"liver pate",
                ],
                "blood sausage": [
                    r"black[- ]?pudding",
                    r"white[- ]?pudding",
                    r"morcilla",
                ],
                "sausage": [
                    r"bangers?",
                    r"sausage(?:s|meat)?",
                    r"chorizos?",
                    r"chorizo picante",
                    r"'?ndujas?(?: paste)?",
                    r"kielbasas?",
                    r"wei(?:ss|sz) ?wursts?",
                    r"bratwursts?",
                    r"sai[- ]?ua",
                    r"sai kok",
                    r"chipolatas?",
                    r"boudins?",
                    r"salchichas?",
                    r"dogs?",
                    r"frankfurters?",
                    r"alheira",
                    r"spianatas?",
                ],
                "processed meat": [
                    r"spam",
                    r"luncheon meat",
                    r"luncheon loaf",
                    r"lunch ?meat",
                    r"leberkase",
                    r"potted meat",
                    r"meatloaf",
                ],
                "_portions": _portions["sausage"],
            },
            "INNARDS": {
                "liver": [r"livers?"],
                "kidney": [r"kidneys?"],
                "heart": [r"hearts?"],
                "tongue": [r"tongues?"],
                "sweetbread": [r"sweetbreads?"],
                "tripe": [r"tripes?"],
                "brain": [r"brains?"],
                # "head": [r"head"],
                # "ear": [r"ears?"],
                "snout": [r"snouts?"],
                "gizzard": [r"gizzards?"],
                "testicle": [r"testicles?"],
            },
        },
        "OTHER": {
            "tofu": [r"tofu"],
            "tempeh": [r"tempeh"],
            "seitan": [r"seitan"],
            "quorn": [r"quorn"],
            "mock meat": [r"mock meat"],
        },
    },
}


# a function that yields all the deepest keys in a dictionary and a list of the keys that lead to them
def _get_deepest_keys(d, path=[], portions=None):
    if portions is None:
        portions = []  # Initialize portions for the root call

    if isinstance(d, dict):
        current_portions = portions.copy()  # Copy the parent's portions for this branch
        if "_portions" in d:
            current_portions.extend(d["_portions"])

        for k, v in d.items():
            if k == "_portions":
                continue
            else:
                yield from _get_deepest_keys(v, path + [k], current_portions)
    else:
        yield d, path[:-1], path[-1], portions  # Use the portions from this path only


for regex, path, ingredient, portions in _get_deepest_keys(_nested_dictionary):
    cookbook.register_ingredient(ingredient, regex, path, portions)

# we need to convert parents in the following manner
# first (from left) category stays the same - each following category gets it's parent categories as a suffix
# example: ["PROTEIN", "MEAT", "CATTLE"] -> ["protein", "protein_meat", "protein_meat_cattle"]
_compound_parents = lambda parents: [
    "_".join(parents[: i + 1]).upper() for i in range(len(parents))
]
_ing_to_labels = {
    i.name: [
        i.name,
        *_compound_parents([p for p in i.parents if "other" not in p.lower()]),
    ]
    for i in cookbook
}
_labels = sorted(list(set(flatten(_ing_to_labels.values()))))
_label_to_idx = {label: idx for idx, label in enumerate(_labels)}
# now create the final mapping - each ingredient (keys) will have as values all the indices of the labels that are in its path
_ing_to_indices = {
    ing: [_label_to_idx[label] for label in labels]
    for ing, labels in _ing_to_labels.items()
}


def batched_create_vectors(ingredients_list):
    """
    Create binary feature vectors for multiple recipes at once.

    Args:
        ingredients_list: List of lists of Ingredient objects, one list per recipe

    Returns:
        numpy.ndarray: Array of binary vectors, one per recipe
    """
    # Pre-allocate the result array for speed
    result = np.zeros((len(ingredients_list), len(_labels)), dtype=int)

    # Process each recipe in the batch
    for idx, ingredients in enumerate(ingredients_list):
        # Filter out None values
        ingredients = [i for i in ingredients if i]
        if not ingredients:
            continue

        # Get all indices that should be 1 for this recipe
        all_indices = []
        for ingredient in ingredients:
            if ingredient.name in _ing_to_indices:
                all_indices.extend(_ing_to_indices[ingredient.name])

        # Set the corresponding indices to 1
        if all_indices:
            result[idx, all_indices] = 1

    return result


class Recipe:
    def __init__(self, phrases=None, ingredients=None, experimental=False):
        self.phrases = phrases
        if ingredients:
            self.ingredients = ingredients
        else:
            self.ingredients = cookbook.read_phrase_batch(phrases)

        # drop any None values
        self.ingredients = [i for i in self.ingredients if i]

        if experimental:
            self.vector = self._create_vector_experimental()
        else:
            self.vector = self._create_vector()

        charcs = ["cheese", "ham", "salami", "sausage", "bacon"]
        ing_is_charc = lambda x: any(
            [c == x.name.lower() or c in x.parents for c in charcs]
        )

        if len(self.ingredients) == 1 and ing_is_charc(self.ingredients[0]):
            self.is_charc = True
        else:
            self.is_charc = False

    def _create_vector(self):
        # collect all indices that should be 1
        indices = flatten(
            [_ing_to_indices[ingredient.name] for ingredient in self.ingredients]
        )
        vector = np.zeros(len(_labels), dtype=int)
        vector[indices] = 1
        return vector

    def _create_vector_experimental(self):
        dictionary = {
            i.name: [i.name, *[p for p in i.parents if "other" not in p.lower()]]
            for i in cookbook
        }
        ings = sorted(list(set(flatten(dictionary.values()))))
        x_cols = ["recipe_" + i for i in ings]

        vector = {col: 0 for col in x_cols}
        for ingredient in self.ingredients:
            if ingredient:
                for name in [ingredient.name, *ingredient.parents]:
                    col_name = "recipe_" + name
                    if col_name in vector:
                        vector[col_name] = 1

        # return as numpy array
        return np.array([vector[col] for col in x_cols])


def _calculate_bounds(phrases_list: list[list[str]]):
    bounds = []
    i = 0
    for phrases in phrases_list:
        bounds.append((i, i + len(phrases)))
        i += len(phrases)

    return bounds


def batch_recipes(phrases_list: list[list[str]]):
    # create dict that maps ingredients/categories to vector indices
    dictionary = {
        i.name: [i.name, *[p for p in i.parents if "other" not in p.lower()]]
        for i in cookbook
    }
    flatten = lambda l: [item for sublist in l for item in sublist]
    ings = sorted(list(set(flatten(dictionary.values()))))
    i_to_idx = {ing: idx for idx, ing in enumerate(ings)}

    # create bounds for each recipe
    bounds = _calculate_bounds(phrases_list)

    # flatten list of phrases
    phrases_list = flatten(phrases_list)

    # create Ingredient objects
    ingredients = cookbook.read_phrase_batch(phrases_list)

    # squish ingredients back into list of lists using bounds
    recipes = []
    for start, end in bounds:
        recipes.append(ingredients[start:end])

    # create binary vectors for each recipe using the Ingredient objects
    vectors = []
    for recipe in recipes:
        vector = {i: 0 for i in range(len(ings))}
        for ingredient in recipe:
            if ingredient:
                for name in [ingredient.name, *ingredient.parents]:
                    idx = i_to_idx[name]
                    vector[idx] = 1
        vectors.append(np.array([vector[i] for i in range(len(ings))]))

    return vectors


def is_text_embedding_available():
    """Check if sentence-transformers is available without importing it directly."""
    try:
        import importlib.util

        return importlib.util.find_spec("sentence_transformers") is not None
    except ImportError:
        return False
