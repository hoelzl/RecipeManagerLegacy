"""Building blocks for meal-planning features.

The application can represent a plan; selecting recipes for a plan is not implemented
yet.
"""

from dataclasses import dataclass

from recipe_manager.models import Recipe


@dataclass
class PlannedMeal:
    day: str
    recipe: Recipe


def plan_titles(meals: list[PlannedMeal]) -> list[str]:
    """Return compact ``day: title`` labels for a meal plan."""
    return [f"{meal.day}: {meal.recipe.title}" for meal in meals]
