from .data import meat
from .data.constants import (
    colors,
    sizes,
    states,
    u_all_values,
    u_imperial_values,
    u_metric_values,
    u_misc_values,
    word_numbers,
)
import re

range_separators = [r"-", r"to", r"–", r"or"]


def one_of(l):
    return r"|".join(l)


N_PREP = re.compile(
    rf"\b(?:each of(?= )|of each(?= )|of an?(?= )|of(?= )|an?(?= )|each,(?= )|each(?= ))"
)
N_WORD = re.compile(rf"\b(?:{one_of(word_numbers)})\b")
N_FRACTION = re.compile(r"\d+ ?/ ?\d+")
N_DECIMAL = re.compile(r"\d+\.\d+")
N_WHOLE = re.compile(r"\d+(?![/\.])")
N_COMPOSED = re.compile(rf"{N_WHOLE.pattern} {N_FRACTION.pattern}")
NUMBER = re.compile(
    rf"(?:"
    rf"{N_WORD.pattern}(?= |$)"
    rf"|"
    rf"{N_DECIMAL.pattern}"
    rf"|"
    rf"{N_FRACTION.pattern}"
    rf"|"
    rf"{N_WHOLE.pattern}(?: {N_FRACTION.pattern})?"
    rf")"
)

R_SEP = re.compile(rf" ?(?:{one_of(range_separators)}) ?")
RANGE = re.compile(
    rf"(?:" rf"{NUMBER.pattern}" rf"{R_SEP.pattern}" rf"{NUMBER.pattern}" rf")"
)

MOD = re.compile(
    rf"(?:"
    rf"\b\w+[- ]?(?:less|free|ful)\b"
    rf"|"
    rf"\b(?:\w+ly )?(?:(?:\w|-)+-|un|pre|extra|over|de)?(?:{one_of(states)})(?:-[\w-]+)?\b"
    rf"|"
    rf"\b(?:low|reduced|high|non)[- ]?(?:\w+)\b"
    rf")"
)

MOD_SEP = re.compile(
    r"(?:(?: ?,)? or | (?: ?,)? and/or | ?, ?|(?: ?,)? and | ?& ?| to | )"
)
MODS = re.compile(rf"(?:{MOD.pattern}{MOD_SEP.pattern})*{MOD.pattern}")

COLOR = re.compile(rf"(?:" rf"\b(?:{one_of(colors)})\b" rf")")
COLORS = re.compile(rf"(?:{COLOR.pattern}{MOD_SEP.pattern})*{COLOR.pattern}")

SIZE = re.compile(rf"(?:\b(?:{one_of(sizes)})(?:[- ]sized)?\b)")
SIZES = re.compile(rf"(?:{SIZE.pattern}{MOD_SEP.pattern})*{SIZE.pattern}")

U = re.compile(r"(?:(?<![a-z])(?:" + one_of(u_all_values) + r")(?![a-z]))")
U_IMPERIAL = re.compile(
    r"(?:(?<![a-z])(?:" + one_of(u_imperial_values) + r")(?![a-z]))"
)
U_METRIC = re.compile(r"(?:(?<![a-z])(?:" + one_of(u_metric_values) + r")(?![a-z]))")
U_MISC = re.compile(
    rf"(?:(?:{N_PREP.pattern} )?(?:{SIZES.pattern} {MOD_SEP.pattern}?)?(?:{MODS.pattern} )?(?<![a-z])(?:"
    + one_of(u_misc_values)
    + r")(?![a-z–-]))"
)
UNIT = re.compile(rf"(?:(?:(?:generous|heaping|heaped) )?{U.pattern}\.?)")

Q = re.compile(rf"(?:{RANGE.pattern}|{NUMBER.pattern})(?!-)")
Q_UNIT = re.compile(rf"(?:{Q.pattern}[ -]?{UNIT.pattern})")
Q_SIZE = re.compile(rf"(?:{Q.pattern} {SIZE.pattern})")

Q_COMPOSED = re.compile(
    rf"(?:"
    rf"{Q.pattern} ?{U_IMPERIAL.pattern}\.? ?{Q.pattern} ?{U_IMPERIAL.pattern}\.?"
    rf"|"
    rf"{Q.pattern} ?{U_METRIC.pattern}\.? ?{Q.pattern} ?{U_METRIC.pattern}\.?"
    rf")"
)

Q_DIMS = re.compile(
    rf"(?:"
    rf"(?:{NUMBER.pattern}[- –]?{UNIT.pattern})"
    rf" ?(?:by|x) ?"
    rf"(?:{NUMBER.pattern}[- –]?{UNIT.pattern})"
    rf")"
)
Q_UNIT_MISC = re.compile(
    rf"(?:"
    rf"(?:(?P<multiplier>{Q.pattern} )?(?P<quantity>{Q.pattern})-(?P<unit>{UNIT.pattern}))"
    rf" (?P<misc>{U_MISC.pattern})"
    rf")"
)

MULTIPLIER = re.compile(rf"(?:(?P<multiplier>{Q.pattern}) ?[x*] ?)")

Q_UNIT_RANGE = re.compile(
    rf"(?:"
    rf"{Q_COMPOSED.pattern}{R_SEP.pattern}{Q_COMPOSED.pattern}"
    rf"|"
    rf"{Q_UNIT.pattern}{R_SEP.pattern}{Q_UNIT.pattern}"
    rf")"
)

QUANTITY = re.compile(
    rf"(?:"
    rf"(?:(?P<multiplier>{Q.pattern}) ?[x*] ?)?"
    rf"(?P<quantity>{Q_DIMS.pattern}|{Q_UNIT_RANGE.pattern}|{Q_COMPOSED.pattern}|{Q_UNIT.pattern}|{Q.pattern}|{UNIT.pattern})?"
    rf"(?:"
    rf"(?: ?/ ?| or )"
    rf"(?:(?P<multiplier_alt>{Q.pattern}) ?[x*] ?)?"
    rf"(?P<quantity_alt>{Q_DIMS.pattern}|{Q_UNIT_RANGE.pattern}|{Q_COMPOSED.pattern}|{Q_UNIT.pattern}|{Q.pattern}|{UNIT.pattern})?"
    rf")?"
    rf"(?: ?(?P<misc_size>{SIZES.pattern})?{MOD_SEP.pattern}?(?P<misc_mods>{MODS.pattern})? ?(?P<extra_misc>{U_MISC.pattern}))?"
    rf")"
)

START_IRREG = re.compile(
    r"(?:sliced |cut |\w+ into |(?:\w+ed )?in |with(?:out)? |from |- |on |to (?=[a-z])|for |weighing |mixed (?:into |with |to |in )|is )"
)
START_POST_MOD = re.compile(r" ?, ?")
START_ALT_ING = re.compile(r"(?: or | and | & )")
POST_UNIT = re.compile(
    rf"(?:(?:{one_of(u_misc_values)}\b)(?=$|{START_POST_MOD.pattern}|{START_ALT_ING.pattern}| {START_IRREG.pattern}))"
)

END_ING = re.compile(
    rf"$| {START_IRREG.pattern}|{START_POST_MOD.pattern}| {POST_UNIT.pattern}|{START_ALT_ING.pattern}"
)

IRREG_POST_MODS = re.compile(
    rf"(?P<irreg_post_mod>" rf"{START_IRREG.pattern}[^,]*?(?= ?, ?| or | and |$)" rf")"
)

INGREDIENT = re.compile(
    rf"(?:about |approx(?:imately)? |around |plus |additional |extra |to taste |more )?"
    rf"(?:{QUANTITY.pattern} ?)?"
    rf"(?:or so |or about |about |approximately |around |per person )?"
    rf"(?:{N_PREP.pattern} )?"
    rf"(?:(?P<size>{SIZES.pattern}){MOD_SEP.pattern})?"
    rf"(?:(?P<pre_mod>{MODS.pattern}){MOD_SEP.pattern})?"
    rf"(?:(?P<color>{COLORS.pattern}) )?"
    rf"(?P<rest>"
    rf"(?:(?P<ingredient>.+?(?={END_ING.pattern})))?"
    rf"(?: ?(?P<post_unit>{POST_UNIT.pattern}))?"
    rf"(?: ?{IRREG_POST_MODS.pattern})?"
    rf"(?: ?, (?P<post_mod>.+?(?= or | and | & |$)))?"
    rf"(?:(?: or | and | & )(?P<ingredient_alt>{Q.pattern}.*))?"
    rf")"
)

PROTEIN = re.compile(
    one_of(
        [
            rf"""\b(?P<{key.replace(' ', '_')}>{one_of(values)})\b(?:$|.*(?P<{key.replace(' ', '_')}_portion>{
                one_of(meat.portions[
                    meat.type_portions[key] if key in meat.type_portions else 'all'
                ] + meat.portions['general'])
            }))"""
            for key, values in meat.dictionary.items()
        ]
    )
)

PORTION = re.compile(one_of(meat.portions["all"]))

# tests = [
#     "175g/6oz piece smoked pancetta , rind removed",
#     "1 inch x 2 inch large knob ginger",
#     "1/4 cup celery , finely chopped",
#     "3-4 lbs beef round steak",
#     "1 1/2 head celery",
#     "1kg 50g beef",
#     "100ml/3 1/2fl oz double cream",
#     "1 1/2-2kg/3lb 5oz - 4lb 8oz lamb shoulder",
#     "5 1/2 cloves garlic , crushed",
#     "5 tsp cloves",
#     "5 garlic cloves to taste, crushed",
#     "3 3-ounce bags of chilli powder, smoked whoole",
#     "1 x 6-bone rack of lamb",
#     "1 1/2 big 6-bone racks of lamb",
#     "1 big rack of lamb or 2 megapints",
#     "freshly ground black pepper to taste",
#     "3 bay leaves",
#     "7-8 cinnamon sticks",
#     "1 thick crusted baguette",
#     "small bunch tarragon , roughly chopped",
#     "3 handfuls fresh, raw, small shelled prawns",
# ]

# for test in tests:
#     pprint(test)
#     pprint(re.search(INGREDIENT, test).groupdict())

# print(
#     re.search(INGREDIENT, "freshly ground black pepper to taste").groupdict()
# )
