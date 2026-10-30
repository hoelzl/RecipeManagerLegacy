"""Catalog queries over a recipe collection.

A general search (by ingredient or tag) belongs here; it is not implemented yet.
"""

from recipe_manager.models import Recipe


def recipes_with_tag(recipes: list[Recipe], tag: str) -> list[Recipe]:
    """Return recipes carrying ``tag``, case-insensitively."""
    needle = tag.casefold()
    return [
        recipe
        for recipe in recipes
        if any(candidate.casefold() == needle for candidate in recipe.tags)
    ]
