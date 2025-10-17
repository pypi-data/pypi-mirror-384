import hashlib
import re
from collections import namedtuple
from typing import Optional

from thefuzz import fuzz, process
from unidecode import unidecode

from .data import regions as data


def flatten(_l: list) -> list:
    return [item for sublist in _l for item in sublist]


class Region:
    def __init__(
        self,
        name: str,
        synonyms: list[str] = None,
        parent: Optional[str] = None,
        path: list[str] = None,
        subregions: list[str] = None,
        country: str = None,
        description: Optional[dict] = None,
        climate_types: Optional[str] = None,
        avg_annual_rainfall: Optional[float] = None,
        elevation_range: Optional[tuple] = None,
        soil_types: Optional[str] = None,
        primary_grapes: Optional[list[str]] = None,
        wine_styles: Optional[list[str]] = None,
    ) -> None:
        data = f"{name} {parent} {country}"

        hash_object = hashlib.sha256(data.encode())
        deterministic_hash = hash_object.hexdigest()

        self.id = deterministic_hash[:10]
        self.name = name
        self.synonyms = synonyms or []
        self.parent = parent
        self.subregions = subregions or []
        self.country = country
        self.description = description
        self.path = path
        self.climate_types = climate_types
        self.avg_annual_rainfall = avg_annual_rainfall
        self.elevation_range = elevation_range
        self.soil_types = soil_types
        self.primary_grapes = primary_grapes or []
        self.wine_styles = wine_styles or []

        self._repr_tuple = namedtuple(
            "Region",
            ["name", "parent"],
        )(
            name,
            parent,
        )

    # make hashable
    def __hash__(self) -> int:
        # combine country, parent and name to create a unique hash
        return hash((self.country, self.parent, self.name))

    def __repr__(self) -> str:
        """Use the namedtuple representation for __repr__"""
        return repr(self._repr_tuple)

    def __str__(self) -> str:
        """Use the namedtuple representation for __str__"""
        return str(self._repr_tuple)

    def __eq__(self, other: "Region") -> bool:
        """Implement equality comparison"""
        if not isinstance(other, Region):
            return False
        return (
            self.name == other.name
            and self.synonyms == other.synonyms
            and self.parent == other.parent
            and self.subregions == other.subregions
            and self.country == other.country
            and self.description == other.description
        )


def create_region_tree(branch: dict, path: list = None) -> list:
    if path is None:
        path = []

    default_description = {
        "julie": "",
        "default": "",
        "sommelier": "",
    }

    obj = Region(
        name=branch["name"],
        synonyms=branch.get("synonyms", []),
        parent=branch.get("parent", None),
        path=path + [branch["name"]],
        subregions=[x["name"] for x in branch.get("subregions", [])],
        country=branch["country"],
        description=branch.get("description", default_description),
        climate_types=branch.get("climate_types", None),
        avg_annual_rainfall=branch.get("avg_annual_rainfall", None),
        elevation_range=branch.get("elevation_range", None),
        soil_types=branch.get("soil_types", None),
        primary_grapes=branch.get("primary_grapes", []),
        wine_styles=branch.get("wine_styles", []),
    )

    current_path = path + [branch["name"]]

    return [
        obj,
        *flatten(
            [
                create_region_tree(
                    {
                        **subbranch,
                        "parent": branch["name"],
                        "country": branch["country"],
                    },
                    path=current_path,
                )
                for subbranch in branch.get("subregions", [])
            ]
        ),
    ]


class ExistingRegions:
    __slots__ = ["regions", "region_tree", "_synonym_to_name"]

    def __init__(self) -> None:
        self.regions = sorted(
            flatten([create_region_tree(branch) for branch in data]),
            key=lambda x: x.name,
        )
        self.region_tree = data
        self._synonym_to_name = {}
        for region in self.regions:
            self._synonym_to_name[region.name] = region.name
            self._synonym_to_name[unidecode(region.name)] = region.name
            for synonym in region.synonyms:
                self._synonym_to_name[synonym] = region.name
                self._synonym_to_name[unidecode(synonym)] = region.name

    def __getitem__(self, key: str) -> Region:
        return self.regions[key]

    def __len__(self) -> int:
        return len(self.regions)

    def __iter__(self) -> object:
        yield from self.regions

    def __repr__(self) -> str:
        return f"ExistingRegions({self.regions})"

    def __str__(self) -> str:
        return f"ExistingRegions({self.regions})"

    def get(self, **kwargs) -> Region:
        # if no non-None kwargs, return None
        if all(value is None for value in kwargs.values()):
            return None

        for region in self.regions:
            if all(
                getattr(region, key) == value or value is None
                for key, value in kwargs.items()
            ):
                return region

    def get_all(self, **kwargs) -> list:
        """
        same as get, but returns all matches
        """
        if all(value is None for value in kwargs.values()):
            return None

        matches = []
        for region in self.regions:
            if all(
                getattr(region, key) == value or value is None
                for key, value in kwargs.items()
            ):
                matches.append(region)

        return matches

    def path_to_region(self, path: list) -> Region:
        best_match = None
        best_match_n = 0
        for region in self.regions:
            if region.name in path:
                ancestors = region.path
                n = len([a for a in ancestors if a in path])
                if n > best_match_n:
                    best_match = region
                    best_match_n = n

        return best_match

    def decode_token(self, token: str) -> str:
        # check for literal match first
        region = self.get(name=token)
        if not region:
            region = self.search_fuzzy(token)
        if not region:
            return None
        return region.name

    def flatten_branch(self, branch: dict, parent: str = None) -> list:
        return [
            self.get(name=branch["name"], parent=parent),
            *flatten(
                [
                    self.flatten_branch(subregion, parent=branch["name"])
                    for subregion in branch.get("subregions", [])
                ]
            ),
        ]

    def find_branch(self, name: str, branch: object = None) -> object:
        if branch is None:
            branch = self.region_tree

        for region in branch:
            if region["name"] == name:
                return region

            res = self.find_branch(name, region.get("subregions", []))

            if res is not None:
                return res

        return None

    def get_descendants(self, region: object) -> list:
        branch = self.find_branch(region if isinstance(region, str) else region.name)

        if branch is None:
            return []

        return self.flatten_branch(branch)[1:]

    def get_ancestors(self, region: object) -> list:
        path = region.path
        return [self.get(name=n, parent=p) for n, p in zip(path, [None] + path[:-1])][
            :-1
        ]

    def get_path(self, region: object) -> list:
        path = region.path
        return [self.get(name=n, parent=p) for n, p in zip(path, [None] + path[:-1])]

    def remove_wine_classifications(self, name: str) -> str:
        name = re.sub(r"\b(IGT|DOC|DOP|DOCG|DO|AVA|AOC|AOP|IGP|VDP|VDT|AC)\b", "", name)
        # drop any trailing whitespace
        name = name.strip()
        name = re.sub(r" +", " ", name)

        return name

    def search_fuzzy(
        self, name: str, threshold: int = 82, ignore_classifications: bool = True
    ) -> Region:
        if ignore_classifications:
            name = self.remove_wine_classifications(name)

        name = unidecode(name)

        name, distance = process.extractOne(
            name, self._synonym_to_name.keys(), scorer=fuzz.QRatio
        )

        if distance < threshold:
            return None

        return self.get(name=self._synonym_to_name[name])

    def find_closest_geo(self, region: str, subset: object = None) -> list:
        """Find geographically closest region to name in subset. Ordering of closeness is:
        0. regions that are children of name
        1. regions that are siblings of name (same parent)
        2. regions that are cousins of name (same grandparent)
        ...
        N. same country
        """

        if isinstance(region, str):
            region = self.get(name=region)

        if subset is None:
            subset = self.regions

        # check regional hierarchy
        current = region
        while current:
            descendants = self.get_descendants(current)
            descendants = [d for d in descendants if d in subset and d != region]
            if len(descendants) > 0:
                return descendants

            current = self.get(name=current.parent)

        # check country
        same_country = [
            r for r in subset if r.country == region.country and r != region
        ]
        if len(same_country) > 0:
            return same_country

        return None


regions = ExistingRegions()
