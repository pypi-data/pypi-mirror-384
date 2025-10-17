from sommify import pyregion


def test_fuzzy_search() -> None:
    assert pyregion.regions.search_fuzzy("bordeaux").name == "Bordeaux"
