import json
from pathlib import Path
from typing import Any

from recipe_manager.models import Ingredient, Recipe


class RecipeFileError(ValueError):
    """A recipe file does not have the expected structure."""


def save_recipes(recipes: list[Recipe], path: Path) -> None:
    """Write recipes to a JSON file."""
    data = [
        {
            "title": r.title,
            "servings": r.servings,
            "ingredients": [vars(i) for i in r.ingredients],
            "tags": r.tags,
            "instructions": r.instructions,
        }
        for r in recipes
    ]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_recipes(path: Path) -> list[Recipe]:
    """Read recipes from a JSON file written by :func:`save_recipes`.

    ``tags``, ``instructions`` and an ingredient's ``amount`` and ``unit`` are
    optional. A missing required field raises :class:`RecipeFileError` naming the
    file and the recipe's position.
    """
    # utf-8-sig also accepts files that start with a byte-order mark.
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise RecipeFileError(f"{path}: expected a list of recipes")
    return [_recipe_from_dict(d, f"{path}: recipe #{n}") for n, d in enumerate(data, 1)]


def _recipe_from_dict(d: Any, where: str) -> Recipe:
    if not isinstance(d, dict):
        raise RecipeFileError(f"{where}: expected an object")
    missing = [key for key in ("title", "servings", "ingredients") if key not in d]
    if missing:
        title = d.get("title", "?")
        raise RecipeFileError(f"{where} ({title!r}): missing {', '.join(missing)}")
    ingredients = []
    for i in d["ingredients"]:
        if "name" not in i:
            raise RecipeFileError(f"{where} ({d['title']!r}): ingredient without a name")
        ingredients.append(Ingredient(i["name"], i.get("amount"), i.get("unit", "")))
    return Recipe(
        title=d["title"],
        servings=d["servings"],
        ingredients=ingredients,
        tags=list(d.get("tags", [])),
        instructions=list(d.get("instructions", [])),
    )
