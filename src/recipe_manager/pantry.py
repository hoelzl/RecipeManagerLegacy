"""Check recipes against pantry stock."""

from recipe_manager.models import Recipe


def missing_ingredients(recipe: Recipe, pantry: dict[str, float]) -> list[str]:
    """Return ingredient names whose available amount is insufficient."""
    return [
        ingredient.name
        for ingredient in recipe.ingredients
        if ingredient.amount is not None
        and pantry.get(ingredient.name, 0.0) <= ingredient.amount
    ]


def can_cook(recipe: Recipe, pantry: dict[str, float]) -> bool:
    """Return whether the pantry contains enough of every ingredient."""
    return not missing_ingredients(recipe, pantry)
