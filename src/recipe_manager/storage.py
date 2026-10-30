import json
from pathlib import Path

from recipe_manager.models import Ingredient, Recipe


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
    """Read recipes from a JSON file written by :func:`save_recipes`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        Recipe(
            title=d["title"],
            servings=d["servings"],
            ingredients=[Ingredient(**i) for i in d["ingredients"]],
        )
        for d in data
    ]
