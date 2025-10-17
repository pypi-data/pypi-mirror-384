from sommify.recipes.reader import TagReader


def test_tag_encoding() -> bool:
    tag_reader = TagReader()
    encoded_values = tag_reader.tag_model.encode(["dasdsad", "aaaa"]).tolist()
    assert len(encoded_values) == 2
