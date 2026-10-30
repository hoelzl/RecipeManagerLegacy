"""Render a recipe as a plain-text report."""

from recipe_manager.formatting import format_ingredient
from recipe_manager.models import Recipe

RULE = "=" * 40


def format_recipe(recipe: Recipe) -> str:
    lines = [RULE, f"{recipe.title} (serves {recipe.servings})", RULE]
    if recipe.tags:
        lines.append("tags: " + ", ".join(recipe.tags))
    lines += ["", "Ingredients:"]
    lines += [f"  - {format_ingredient(ing)}" for ing in recipe.ingredients]
    if recipe.instructions:
        lines += ["", "Instructions:"]
        lines += [f"  {n}. {step}" for n, step in enumerate(recipe.instructions, 1)]
    return "\n".join(lines) + "\n"
