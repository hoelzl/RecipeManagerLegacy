"""Suggest simple ingredient substitutions."""

SUBSTITUTIONS: dict[str, list[str]] = {
    "butter": ["margarine", "coconut oil"],
    "milk": ["oat milk", "soy milk"],
    "egg": ["flax egg", "applesauce"],
    "sugar": ["honey", "maple syrup"],
    "flour": ["almond flour", "oat flour"],
    "cream": ["coconut cream", "cashew cream"],
}


def suggest_substitutions(ingredient: str) -> list[str]:
    """Return known substitutes for an ingredient (case-insensitive)."""
    return SUBSTITUTIONS.get(ingredient.strip().lower(), [])
