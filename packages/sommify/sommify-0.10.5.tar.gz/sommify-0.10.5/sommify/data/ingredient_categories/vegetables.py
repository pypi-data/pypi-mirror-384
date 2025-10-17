VEG_FLOWER = [
    r"artichoke",
    r"broccoli",
    r"caper",
    r"cauliflower",
]


VEG_FRUIT = [
    # fruit and seed vegetables
    r"avocado",
    r"bell pepper",
    r"breadfruit",
    r"chayote",
    r"chickpea",
    r"corn",
    r"cowpea",
    r"cucumber",
    # r"durian",
    r"eggplant",
    r"aubergine",
    r"gherkin",
    r"pickle",
    r"husk tomato",
    # r"jackfruit",
    r"lentil",
    r"lotus",
    r"musk cucumber",
    r"okra",
    r"olive",
    r"pea",
    r"peanut",
    r"pumpkin",
    r"snake gourd",
    r"soybean",
    r"squash",
    r"tomatillo",
    r"tomato",
    # r"water chestnut",
    r"wax gourd",
    r"zucchini",
]

# leaf and stem vegetables
VEG_GREEN = [
    r"amaranth",
    r"arugula",
    r"asparagus",
    r"bamboo",
    r"bok choy",
    r"borage",
    r"brussels? sprouts?",
    r"burdock",
    r"cabbage",
    r"cardoon",
    r"celery",
    r"chard",
    r"chicory",
    r"chive",
    r"collard",
    r"endive",
    r"fennel",
    r"grape lea(?:f|ve|ves)",
    r"indian fig",
    r"kale",
    r"kohlrabi",
    r"lamb'?s lettuce",
    r"(?:lamb'?s quarters?|pigweed)",
    r"leek",
    r"lemongrass",
    r"lettuce",
    r"lotus",
    r"moringa",
    r"mustard",
    r"napa cabbage",
    r"sorrel",
    r"spinach",
    r"nettle",
    r"tossa jute",
    r"watercress",
]

# root, bulb, and tuberous vegetables
VEG_ROOT = [
    r"beet",
    r"carrot",
    r"cassava",
    r"celeriac",
    r"water chestnut",
    # r"garlic",
    r"ginger",
    r"horseradish",
    r"jerusalem artichoke",
    r"jicama",
    r"lotus",
    # r"onion",
    # r"potato",
    r"sweet potato",
    r"parsnip",
    r"radish",
    r"rutabaga",
    r"salsify",
    # r"shallot",
    r"taro",
    r"ti",
    r"turnip",
    r"yam",
]


VEG_DEFAULT = [
    *VEG_FLOWER,
    *VEG_GREEN,
    *VEG_FRUIT,
]

RE_VEG_ROOT = r"(?:\b" + r"\b|\b".join(VEG_ROOT) + r"\b)$"
RE_VEG_DEFAULT = r"(?:\b" + r"\b|\b".join(VEG_DEFAULT) + r"\b)$"
RE_VEG_GREEN = r"(?:\b" + r"\b|\b".join(VEG_GREEN) + r"\b)$"
