"""Small read-only metrics for recipe collections.

The functions here only read recipes; they never change parsing, persistence, or
reporting behavior.
"""

from collections.abc import Iterable

from recipe_manager.models import Recipe


def ingredient_count(recipe: Recipe) -> int:
    """Return the number of ingredient rows in a recipe."""
    return len(recipe.ingredients)


def recipe_titles(recipes: Iterable[Recipe]) -> list[str]:
    """Return recipe titles in input order."""
    return [recipe.title for recipe in recipes]
