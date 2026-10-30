"""Parse ingredient lines and a tiny recipe text format.

The text format looks like this::

    Title: Pancakes
    Servings: 4
    Tags: breakfast, sweet
    Ingredients:
    - 200 g flour
    - 1/2 cup sugar
    - 3 eggs
    - salt to taste
    Instructions:
    - Mix the dry ingredients.
    - Whisk in the eggs and milk.
    - Fry until golden.
"""

from recipe_manager.models import Ingredient, Recipe


def parse_ingredient(line: str) -> Ingredient:
    """Parse a single ingredient line such as ``"200 g flour"`` or ``"3 eggs"``."""
    text = line.strip()
    if not text:
        raise ValueError("empty ingredient line")
    tokens = text.split()
    # The first token is expected to be the amount.
    amount = float(tokens[0])
    rest = tokens[1:]
    # A short alphabetic token right after the amount is treated as a unit.
    if rest and rest[0].isalpha() and len(rest[0]) <= 4:
        unit = rest[0]
        name = " ".join(rest[1:])
    else:
        unit = ""
        name = " ".join(rest)
    if not name:
        name = unit
        unit = ""
    return Ingredient(name=name, amount=amount, unit=unit)


def parse_recipe_text(text: str) -> Recipe:
    """Parse the small recipe text format into a :class:`Recipe`."""
    title = ""
    servings = 1
    tags: list[str] = []
    ingredients: list[Ingredient] = []
    instructions: list[str] = []
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif lower.startswith("servings:"):
            servings = int(line.split(":", 1)[1].strip())
        elif lower.startswith("tags:"):
            tags = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
        elif lower.startswith("ingredients:"):
            section = "ingredients"
        elif lower.startswith("instructions:"):
            section = "instructions"
        elif line.startswith("-"):
            item = line[1:].strip()
            if section == "ingredients":
                ingredients.append(parse_ingredient(item))
            elif section == "instructions":
                instructions.append(item)
    return Recipe(
        title=title,
        servings=servings,
        ingredients=ingredients,
        tags=tags,
        instructions=instructions,
    )
