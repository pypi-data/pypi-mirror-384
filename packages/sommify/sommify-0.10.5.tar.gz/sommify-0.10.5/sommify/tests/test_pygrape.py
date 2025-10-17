from sommify import pygrape


def test_fuzzy_search() -> None:
    assert pygrape.grapes.search_fuzzy("pinot no").name == "Pinot Noir"
