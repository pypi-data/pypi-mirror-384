from sommify.prompts import (
    country_entity_to_iso,
    extract_mentions_naive,
    region_entity_to_closest,
)

extract_mentions_naive(
    "france", region_pool=["france"], subregion_pool=["bordeaux"], grape_pool=["pinot"]
)


def test_extract_mentions_naive() -> bool:
    assert extract_mentions_naive(
        "france",
        region_pool=["france"],
        subregion_pool=["bordeaux"],
        grape_pool=["pinot"],
    )["regions"] == ["france"]


def test_country_entity_to_iso() -> bool:
    assert country_entity_to_iso("slovakia") == "SK"


def test_region_entity_to_closest() -> bool:
    assert region_entity_to_closest("bordeau") == "Bordeaux"
