"""Render a recipe as a plain-text report.

This module works, but it has grown organically and is a good candidate for a
refactor: manual string concatenation, a hand-rolled step counter, and a naive
pluralization rule that is wrong more often than it is right.
"""

from recipe_manager.models import Recipe


def format_recipe(recipe: Recipe) -> str:
    out = ""
    out += "=" * 40 + "\n"
    out += recipe.title + " (serves " + str(recipe.servings) + ")\n"
    out += "=" * 40 + "\n"
    if recipe.tags:
        out += "tags: " + ", ".join(recipe.tags) + "\n"
    out += "\nIngredients:\n"
    for ing in recipe.ingredients:
        if ing.amount is None:
            out += "  - " + ing.name + "\n"
        elif ing.unit == "":
            if ing.amount == 1:
                out += "  - " + str(int(ing.amount)) + " " + ing.name + "\n"
            else:
                # Naive pluralization: just append an "s".
                out += "  - " + str(int(ing.amount)) + " " + ing.name + "s\n"
        else:
            amt = ing.amount
            if amt == int(amt):
                amt_str = str(int(amt))
            else:
                amt_str = str(amt)
            out += "  - " + amt_str + " " + ing.unit + " " + ing.name + "\n"
    if recipe.instructions:
        out += "\nInstructions:\n"
        n = 1
        for step in recipe.instructions:
            out += "  " + str(n) + ". " + step + "\n"
            n += 1
    return out
