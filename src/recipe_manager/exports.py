"""Export recipes as stable, JSON-ready rows (serialization is not implemented yet)."""

from typing import TypedDict

from recipe_manager.models import Recipe


class ExportRow(TypedDict):
    title: str
    servings: int


def export_rows(recipes: list[Recipe]) -> list[ExportRow]:
    """Return stable, JSON-ready rows without choosing a serialization policy."""
    return [
        {"title": recipe.title, "servings": recipe.servings}
        for recipe in recipes
    ]
