# # from utils import *
# import html
# import unicodedata

# from unidecode import unidecode

# from . import regex as re_
# from .utils import *


# def normalize(phrase):
#     phrase = unicodedata.normalize("NFD", phrase)
#     phrase = unidecode(phrase)
#     phrase = phrase.lower()
#     phrase = re.sub(r"\([^)]*\)", "", phrase)
#     phrase = re.sub(r"\(|\)", "", phrase)

#     for vulgar_fraction, fraction_str in vf.dictionary.items():
#         phrase = re.sub(vulgar_fraction, " " + fraction_str + " ", phrase)

#     phrase = phrase.replace("–", "-")
#     phrase = phrase.replace("⁄", "/")
#     phrase = re.sub(r"half ?(?:and|-) ?half", "half-and-half", phrase)
#     phrase = re.sub(r"\.\.+", "", phrase)
#     phrase = re.sub(r" *\. *(?![0-9])", ". ", phrase)
#     phrase = re.sub(r"(?<=[0-9]) *\. *(?=[0-9])", ".", phrase)
#     phrase = re.sub(r" '", "'", phrase)
#     phrase = re.sub(r"(,[^,]+)?< ?a href.*", "", phrase)
#     phrase = re.sub(r""" *<(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+> *""", "", phrase)
#     phrase = re.sub(r"(?<=[a-z])/[a-z]+", "", phrase)
#     phrase = re.sub(r"\b(?:5|five)[- ]?spice", "fivespice", phrase)
#     phrase = re.sub(r".*: ?", "", phrase)
#     phrase = re.sub(r"\s+", " ", phrase)
#     phrase = phrase.strip()
#     return phrase


# def read_phrase(phrase):
#     if not P_filter(str(phrase)):
#         return None

#     phrase = html.unescape(phrase)
#     phrase = normalize(phrase)
#     phrase = P_duplicates(phrase)

#     phrase = P_multi_misc_fix(phrase)
#     phrase = P_multi_misc_fix(phrase)
#     phrase = P_missing_multiplier_symbol_fix(phrase)
#     phrase = P_quantity_dash_unit_fix(phrase)
#     phrase = P_juice_zest_fix(phrase)

#     values = re.search(re_.INGREDIENT, phrase).groupdict()

#     values["unit"] = None
#     if values["quantity"]:
#         values["quantity"], values["unit"] = re.search(
#             rf"(?P<quantity>{re_.Q})? ?(?P<unit>.*)?", values["quantity"]
#         ).groups()
#         values["quantity"] = Q_to_number(values["quantity"])

#     values["unit"] = U_unify(values["unit"])
#     values["quantity"], values["unit"] = Q_U_unify(values["quantity"], values["unit"])

#     values["size"] = S_unify(values["size"])

#     if values["ingredient"] != values["ingredient"] or not values["ingredient"]:
#         return None

#     values["ingredient"] = I_to_singular(values["ingredient"])
#     values["simple"] = I_label_protein(values["ingredient"])
#     values["simple"] = I_simplify(values["simple"])

#     if values["simple"] == "sugar":
#         values["quantity"], values["unit"] = Q_U_sugar(
#             values["quantity"], values["unit"]
#         )

#     values["simple"] = re.sub(r"\bnan\b", "naan", values["simple"])

#     filtered = {
#         c: values[c]
#         for c in ["quantity", "unit", "size", "color", "ingredient", "simple"]
#     }
#     filtered["simple"] = values["simple"]
#     return filtered
