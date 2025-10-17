FRUIT_STONE = [
    r"apricot",
    r"cherry",
    r"date",
    r"mango",
    r"nectarine",
    r"peach",
    r"plum",
    r"prune",
    r"lychee",
    r"plu(?:mc)?ots?",
    r"apriums?",
]


FRUIT_BERRY = [
    r"blackberry",
    r"blueberry",
    r"boysenberry",
    r"cranberry",
    r"cloudberry",
    r"crowberry",
    r"elderberry",
    r"goji berry",
    r"gooseberry",
    r"grape",
    r"huckleberry",
    r"hackberry",
    r"lingonberry",
    r"loganberry",
    r"mulberry",
    r"raspberry",
    r"strawberry",
    r"currant",
    r"pawpaw",
    r"grape",
]


FRUIT_MELON = [
    r"watermelon",
    r"melon",
    r"cant[ae]loupe",
    r"honeydew",
    r"winter ?melon",
    r"ash ?gourd",
    r"casaba",
    r"autumn sweet",
    r"armenian cucumber",
    r"gac fruit" r"sugar baby matisse",
    r"ivory gaya",
]


FRUIT_CITRUS = [
    r"citrons?",
    r"clamondins?",
    r"daidais?",
    r"grapefruits?",
    r"kabosus?",
    r"kiyomis?",
    r"kumquats?",
    r"lemons?",
    r"limes?",
    r"mandarins?",
    r"mangshanyegan?",
    r"navels?",
    r"orange(?:lo)?s?",
    r"pomelo(?:es|s)?",
    r"sudachis?",
    r"tangerines?",
    r"yuzu",
]


FRUIT_TROPICAL = [
    r"acais?",
    r"ackees?",
    r"banana?",
    r"breadfruits?",
    r"custard apples?",
    r"cherimoyas?",
    r"chico(?:es|s)?",
    r"dates?",
    r"dragonfruits?",
    r"durians?",
    r"fig(?:ue)?s?",
    r"grapefruits?",
    r"guavas?",
    r"jabuticabas?",
    r"jackfruits?",
    r"kiwano(?:es|s)?",
    r"kiwis?",
    r"kumquats?",
    r"loquats?",
    r"mameys?",
    r"mango(?:es|s)?",
    r"mangosteens?",
    r"marangs?",
    r"mulberr(?:y|ies)",
    r"oranges?",
    r"papayas?",
    r"passion fruits?",
    r"pawpaws?",
    r"persimmons?",
    r"pineapples?",
    r"plantains?",
    r"pomegranates?",
    r"pomelo(?:es|s)?",
    r"quinces?",
    r"rambutans?",
    r"sapodillas?",
    r"sapotes?",
    r"soursops?",
    r"star fruits?",
    r"ugli fruits?",
    r"yuzu",
]


FRUIT_DEFAULT = [
    *FRUIT_STONE,
    *FRUIT_BERRY,
    *FRUIT_MELON,
    *FRUIT_CITRUS,
    *FRUIT_TROPICAL,
    r"apples?",
    r"pears?",
]

RE_FRUIT_DEFAULT = r"(?:\b" + r"\b|\b".join(FRUIT_DEFAULT) + r"\b)$"
RE_BERRY = r"(?:\b" + r"\b|\b".join(FRUIT_BERRY) + r"\b)$"
RE_FRUIT_TROPICAL = r"(?:\b" + r"\b|\b".join(FRUIT_TROPICAL) + r"\b)$"
