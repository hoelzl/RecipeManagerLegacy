"""Arrange recipes into a cookbook: chapters, ordering and link anchors.

This module only decides the structure; ``cookbook_render`` turns it into
Markdown or HTML.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from recipe_manager.calories import CalorieEstimate, estimate_per_serving
from recipe_manager.models import Recipe

OTHER_CHAPTER = "Other"


@dataclass
class Entry:
    recipe: Recipe
    anchor: str
    other_tags: list[str]
    calories: CalorieEstimate | None = None


@dataclass
class Chapter:
    name: str
    anchor: str
    entries: list[Entry] = field(default_factory=list)


@dataclass
class Cookbook:
    title: str
    chapters: list[Chapter]


def slugify(text: str) -> str:
    """``"Tomato Soup!"`` -> ``"tomato-soup"``; never empty."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return slug or "section"


class _Anchors:
    """Hand out slugs that are unique within one document."""

    def __init__(self) -> None:
        self._used: set[str] = set()

    def __call__(self, text: str) -> str:
        base = slugify(text)
        anchor, n = base, 2
        while anchor in self._used:
            anchor, n = f"{base}-{n}", n + 1
        self._used.add(anchor)
        return anchor


def _tags(recipe: Recipe) -> list[str]:
    """The recipe's tags without surrounding whitespace, blank ones dropped."""
    return [t.strip() for t in recipe.tags if t.strip()]


def build_cookbook(
    recipes: list[Recipe],
    title: str = "Cookbook",
    calorie_table: Mapping[str, float] | None = None,
) -> Cookbook:
    """Group ``recipes`` into chapters by their first tag.

    Chapters are sorted alphabetically with untagged recipes in a final "Other"
    chapter; recipes are sorted by title within a chapter. Two recipes with the
    same title (ignoring case) raise :class:`ValueError`.
    """
    seen: set[str] = set()
    for recipe in recipes:
        key = recipe.title.casefold()
        if key in seen:
            raise ValueError(f"duplicate recipe title: {recipe.title!r}")
        seen.add(key)

    groups: dict[str, tuple[str, list[Recipe]]] = {}
    untagged: list[Recipe] = []
    for recipe in recipes:
        tags = _tags(recipe)
        if not tags:
            untagged.append(recipe)
            continue
        first = tags[0]
        name = first[0].upper() + first[1:]
        groups.setdefault(first.casefold(), (name, []))[1].append(recipe)

    ordered = [groups[key] for key in sorted(groups)]
    if untagged:
        ordered.append((OTHER_CHAPTER, untagged))

    anchors = _Anchors()
    chapters = []
    for name, members in ordered:
        chapter = Chapter(name, anchors(name))
        for recipe in sorted(members, key=lambda r: r.title.casefold()):
            calories = (
                None if calorie_table is None else estimate_per_serving(recipe, calorie_table)
            )
            chapter.entries.append(
                Entry(recipe, anchors(recipe.title), _tags(recipe)[1:], calories)
            )
        chapters.append(chapter)
    return Cookbook(title, chapters)
