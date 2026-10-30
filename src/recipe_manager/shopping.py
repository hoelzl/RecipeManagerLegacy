"""Helpers for turning recipes into shopping-list data.

Formatting a shopping list for output is not implemented yet.
"""

from collections.abc import Iterable

from recipe_manager.models import Recipe


def unique_ingredient_names(recipes: Iterable[Recipe]) -> list[str]:
    """Return sorted ingredient names, de-duplicated case-insensitively."""
    names = {ingredient.name.casefold() for recipe in recipes for ingredient in recipe.ingredients}
    return sorted(names)
