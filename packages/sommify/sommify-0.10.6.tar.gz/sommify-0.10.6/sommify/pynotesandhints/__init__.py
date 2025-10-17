import json
from collections import namedtuple

from thefuzz import fuzz, process

from .data import notes_and_hits as data

# Use a more descriptive namedtuple and directly convert data to namedtuple objects
NotesAndHint = namedtuple("NotesAndHint", "name synonyms description vector category")


def get_category_from_vector(vector: list) -> list:
    categories = [
        "fruits",
        "flowers",
        "spices",
        "herbal",
        "minerality",
        "oak",
        "fermentation",
        "tertiary",
    ]
    return [categories[i] for i, v in enumerate(vector) if v]


# Convert data to NotesAndHint objects more efficiently
notes_and_hints_list = [
    NotesAndHint(
        name=item["name"],
        synonyms=item["synonyms"],
        description=item["description"],
        vector=item["vector"],
        category=get_category_from_vector(item["vector"]),
    )
    for item in data
]


# Improved class for handling notes and hints
class ExistingNotesAndHints:
    def __init__(self, notes_and_hints: list) -> None:
        self.notes_and_hints = notes_and_hints
        self._synonym_to_name = {
            synonym: note.name
            for note in notes_and_hints
            for synonym in note.synonyms
            if not any(char.isdigit() or char == "×" for char in synonym)
        }
        self._synonym_to_name.update({note.name: note.name for note in notes_and_hints})

    def __iter__(self) -> iter:
        return iter(self.notes_and_hints)

    def __getitem__(self, index: int) -> NotesAndHint:
        return self.notes_and_hints[index]

    def __len__(self) -> int:
        return len(self.notes_and_hints)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({len(self)})"

    def get(self, **kwargs) -> NotesAndHint:
        return next(
            (
                note
                for note in self.notes_and_hints
                if all(getattr(note, k) == v for k, v in kwargs.items())
            ),
            None,
        )

    def search_fuzzy(self, note_or_hint: str, threshold: float = 82) -> NotesAndHint:
        name, distance = process.extractOne(
            note_or_hint, self._synonym_to_name.keys(), scorer=fuzz.QRatio
        )
        if distance > threshold:
            return self.get(name=self._synonym_to_name[name])
        return None


notes_and_hints = ExistingNotesAndHints(notes_and_hints_list)
