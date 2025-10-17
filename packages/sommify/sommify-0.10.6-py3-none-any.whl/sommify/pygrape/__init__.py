import re
from collections import namedtuple

from thefuzz import fuzz, process
from unidecode import unidecode

from ..pyregion import regions
from .data import grapes as data

grape_to_object = {}


def format_name(name: str) -> str:
    return name.lower().replace("i̇", "i").title()


for o in data:
    name = format_name(o["name"])
    grape_to_object[name] = {**o, "name": name}

# named tuple


Grape = namedtuple(
    "Grape",
    [
        "name",
        "synonyms",
        "description",
        "color",
        "regions",
        "flavor_profile",
        "acidity",
        "tannin",
        "body",
        "alcohol",
        "wine_styles",
        "numeric",
    ],
)


# create a generator of grapes
class ExistingGrapes:
    __slots__ = ["grapes", "_synonym_to_name"]

    def __init__(self) -> None:
        self.grapes = []
        self._synonym_to_name = {}
        for name in grape_to_object:
            grape = Grape(
                name=name,
                synonyms=grape_to_object[name].get("synonyms", []),
                description=grape_to_object[name].get("description", None),
                color=grape_to_object[name].get("color", None),
                regions=grape_to_object[name].get("regions", []),
                flavor_profile=grape_to_object[name].get("flavor_profile", []),
                acidity=grape_to_object[name].get("acidity", None),
                tannin=grape_to_object[name].get("tannin", None),
                body=grape_to_object[name].get("body", None),
                alcohol=grape_to_object[name].get("alcohol", None),
                wine_styles=grape_to_object[name].get("wine_styles", []),
                numeric=list(grape_to_object.keys()).index(name),
            )

            self.grapes.append(grape)
            self._synonym_to_name[name] = name
            self._synonym_to_name[unidecode(name)] = name
            for synonym in grape.synonyms:
                if re.search(r"×", synonym):
                    continue
                # if re.search(r"\d", synonym) or re.search(r"×", synonym):
                # continue
                self._synonym_to_name[synonym] = name
                self._synonym_to_name[unidecode(synonym)] = name

    def __iter__(self) -> namedtuple:
        yield from self.grapes

    def __getitem__(self, index: int) -> Grape:
        return self.grapes[index]

    def __len__(self) -> int:
        return len(self.grapes)

    def __repr__(self) -> str:
        return f"ExistingGrapes({len(self.grapes)})"

    def __str__(self) -> str:
        return f"ExistingGrapes({len(self.grapes)})"

    def get(self, **kwargs) -> Grape:
        for grape in self.grapes:
            if all(getattr(grape, k) == v for k, v in kwargs.items()):
                return grape
        return None

    def search_fuzzy(self, grape: str, threshold: int = 82) -> Grape:
        name = unidecode(grape)

        name, distance = process.extractOne(
            grape, self._synonym_to_name.keys(), scorer=fuzz.QRatio
        )
        if distance > threshold:
            return self.get(name=self._synonym_to_name[name])
        else:
            return None

    def extract_region(self, grape: str, threshold: int = 82) -> tuple:
        # first we check for included region names i.e "Bordeaux", "d'Asti", "de Bourgogne"
        region = regions.search_fuzzy(grape, threshold=threshold)

        if region is not None and grape not in ["Rosette"]:
            return None, region

        # id contains d'Asti, de Bourgogne, etc.
        ptrn = r"(.+)\b(?:d'|de\s|della\s)(\w+)"
        match = re.search(ptrn, grape)

        if not match:
            grape, region = grape, None
        else:
            grape, region = match.groups()
            region = regions.search_fuzzy(region, threshold=threshold)

        return grape, region

    def search(
        self,
        grape: str,
        fuzzy: bool = False,
        threshold: int = 82,
        with_region: bool = False,
    ) -> Grape:
        name = unidecode(grape)

        if not with_region:
            if fuzzy:
                grape = self.search_fuzzy(name, threshold=threshold)
            else:
                grape = self.get(name=self._synonym_to_name.get(name))

        name, region = self.extract_region(name, threshold=threshold)

        if not name:
            return None, region

        if fuzzy:
            grape = self.search_fuzzy(name, threshold=threshold)
        else:
            grape = self.get(name=self._synonym_to_name.get(name))

        return grape, region


grapes = ExistingGrapes()

# TODO add all support function for grapes e.g get the best desription, get the best region, etc.
