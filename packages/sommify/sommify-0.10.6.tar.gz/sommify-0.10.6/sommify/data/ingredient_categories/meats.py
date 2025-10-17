import re

from ...utils import one_of


def flatten(t):
    return [item for sublist in t for item in sublist]


portions = {
    "chicken": [
        r"wings?",
        r"giblets?",
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
        r"gizzards?",
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
        r"hearts?",
        r"escalope",
        r"supreme",
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
        r"trotters?",
        r"shank",
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
        r"kidney",
        r"schnitzel",
        r"breast",
        r"brisket",
        r"cutlets?",
    ],
    "beef": [
        r"shin",
        r"silver[- ]?side",
        r"kidneys?",
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
        r"mince",
        r"oxtail",
        r"shoulder",
        r"heart",
        r"sirloin",
        r"jerky",
        r"tongue",
        r"ribs?",
        r"chunks?",
        r"shank",
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
        r"shank",
        r"meat",
        r"mince",
        r"kidney",
        r"rump",
        r"fillet",
        r"cutlet",
        r"belly",
        r"rib",
        r"breast",
    ],
    "sausage": [r"links?", r"rings?", r"casings?", r"meat", r"patty"],
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
portions["all"] = flatten(list(portions.values()))
portions["any"] = [""]
portions["none"] = [r"$"]

RE_PORTION = re.compile(
    r"(?P<portion>" + "|".join(portions["all"]) + r")", re.IGNORECASE
)


MEAT_SAUSAGES = [
    r"sausage(?:s|meat)?",
    r"chorizos?",
    r"kielbasas?",
    r"bratwursts?",
    r"longaniza",
    r"sai[- ]?ua",
    r"longganisas?",
    r"lau[- ]?lau",
    r"chipolatas?",
    r"boudins?",
    r"bangers?",
    r"salpicao",
    r"salchich(?:a|on)s?",
]
MEAT_LIVER = [r"livers?", r"liverwurst", r"foie[- ]?gras", r"pate"]
MEAT_POULTRY = [r"chicken", "turkey", "rabbit", "hen"]
MEAT_LAMB = ["lamb", "mutton", "goat"]
MEAT_GAME_BIRD = ["pigeon", "pheasant", "quail", "duck", "goose"]
MEAT_GAME = ["venison", "deer", r"boar", r"game", r"bear", r"kangaroo"]
MEAT_PORK = ["pork", "veal", r"meatballs?"]
MEAT_TUNA = [r"tuna"]
MEAT_SALMON = [r"\bsalmon\b"]
MEAT_FATTY_FISH = [
    "herring",
    "eel",
    "trout",
    "arctic char",
    "butterfish",
    "mackerel",
    r"^anchov(?:y|ies)$",
    "sardine",
    "swordfish",
    "shark",
    r"monk[- ]?fish",
    "bluefish",
    "wahoo",
    r"(?<!greenland )turbot",
]
MEAT_LEAN_FISH = [
    "carp",
    "bonita",
    "bass",
    "squeteague",
    "catfish",
    "flounder",
    "cod",
    "skrei",
    "hake",
    "hoki",
    "sole",
    "snapper",
    "perch",
    "haddock",
    "halibut",
    r"greenland turbot",
    "pike",
    "tilapia",
    "swai",
    "whitefish",
    r"mahi[ -]?mahi",
    "greenland turbot",
    "barramundi",
    "char",
    "trout",
    "pollock",
    "cobia",
    "croaker",
    "mullet",
    "rockfish",
    "whiting",
    "saury",
    "plaice",
    "grenadier",
    "kingklip",
    "sanddab",
    "sandperch",
]
MEAT_OCTOPUS = [r"octopus", r"squid", r"calamari", r"cuttle[- ]?fish"]
MEAT_CRUSTACEAN = [
    "lobster",
    r"cra[wy][- ]?fish",
    "prawn",
    "shrimp",
    r"cra[wy][- ]?daddy",
    "krill",
    "crab",
    r"lobsterette?",
    r"langoustine",
    r"shell[- ]?fish",
]
MEAT_OTHER_SEAFOOD = [
    r"clams?",
    r"mussels?",
    r"scallops?",
    r"oysters?",
    r"cockles?",
    r"snails?",
    r"escargots?",
    r"caviar",
    r"\broe\b",
    r"barnacles?",
]
MEAT_HAM = [
    r"mortadella",
    r"\bham$",
    r"pancetta(?: (?:di )?cubetti)?",
    "prosciutto",
    r"jamon(?: iberico)?",
    "jambon",
    "capicola",
    "culatello",
    "gammon",
    "serrano",
    "bresaola",
    "lomo",
]
MEAT_BEEF = [
    "new york strip",
    "cow",
    r"fill?et mignon",
    "loin",
    "tenderloin",
    "sirloin",
    r"beef[^s]",
    "wagyu",
    r"rib[ \-]eye",
    r"beef$",
    "steak",
    "ground meat",
    "mincemeat",
    "stew meat",
    "minced meat",
    "meat",
    r"roast$",
    r"^chuck$",
    r"hamburger$",
]
MEAT_BACON = [
    r"bacon bits?",
    r"bacon$",
    r"lardons?",
    r"rashers?",
    r"speck",
    r"guanciale",
    r"szalonna",
    r"lap yuk",
]

MEAT = [
    *MEAT_SAUSAGES,
    *MEAT_LIVER,
    *MEAT_POULTRY,
    *MEAT_LAMB,
    *MEAT_GAME_BIRD,
    *MEAT_GAME,
    *MEAT_PORK,
    *MEAT_TUNA,
    *MEAT_SALMON,
    *MEAT_FATTY_FISH,
    *MEAT_LEAN_FISH,
    *MEAT_OCTOPUS,
    *MEAT_CRUSTACEAN,
    *MEAT_OTHER_SEAFOOD,
    *MEAT_HAM,
    *MEAT_BEEF,
    *MEAT_BACON,
]

RE_SAUSAGE = rf"(?:{one_of(MEAT_SAUSAGES)})(?: {RE_PORTION})?$"
RE_LIVER = rf"(?:{one_of(MEAT_LIVER)})(?: {RE_PORTION})?$"
RE_POULTRY = rf"(?:{one_of(MEAT_POULTRY)})(?: {RE_PORTION})?$"
RE_LAMB = rf"(?:{one_of(MEAT_LAMB)})(?: {RE_PORTION})?$"
RE_GAME_BIRD = rf"(?:{one_of(MEAT_GAME_BIRD)})(?: {RE_PORTION})?$"
RE_GAME = rf"(?:{one_of(MEAT_GAME)})(?: {RE_PORTION})?$"
RE_PORK = rf"(?:{one_of(MEAT_PORK)})(?: {RE_PORTION})?$"
RE_TUNA = rf"(?:{one_of(MEAT_TUNA)})(?: {RE_PORTION})?$"
RE_SALMON = rf"(?:{one_of(MEAT_SALMON)})(?: {RE_PORTION})?$"
RE_FATTY_FISH = rf"(?:{one_of(MEAT_FATTY_FISH)})(?: {RE_PORTION})?$"
RE_LEAN_FISH = rf"(?:{one_of(MEAT_LEAN_FISH)})(?: {RE_PORTION})?$"
RE_OCTOPUS = rf"(?:{one_of(MEAT_OCTOPUS)})(?: {RE_PORTION})?$"
RE_CRUSTACEAN = rf"(?:{one_of(MEAT_CRUSTACEAN)})(?: {RE_PORTION})?$"
RE_OTHER_SEAFOOD = rf"(?:{one_of(MEAT_OTHER_SEAFOOD)})(?: {RE_PORTION})?$"
RE_HAM = rf"(?:{one_of(MEAT_HAM)})(?: {RE_PORTION})?$"
RE_BEEF = rf"(?:{one_of(MEAT_BEEF)})(?: {RE_PORTION})?$"
RE_BACON = rf"(?:{one_of(MEAT_BACON)})(?: {RE_PORTION})?$"
RE_MEAT = rf"(?:{one_of(MEAT)})(?: {RE_PORTION})?$"
