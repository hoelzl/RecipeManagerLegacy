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

import re

from recipe_manager.models import Ingredient, Recipe

BOM = "\ufeff"  # byte-order mark some editors put at the start of a file

# Units recognised after the amount; anything else is part of the name.
UNITS = {
    "g", "kg", "mg", "ml", "cl", "dl", "l",
    "tsp", "tbsp", "cup", "cups", "oz", "lb",
    "pinch", "clove", "cloves", "slice", "slices",
}


def parse_amount(text: str) -> float:
    """Parse ``"2"``, ``"0.5"``, ``"1/2"`` or a mixed number such as ``"1 1/2"``."""
    total = 0.0
    for part in text.split():
        if "/" in part:
            numerator, denominator = part.split("/", 1)
            total += float(numerator) / float(denominator)
        else:
            total += float(part)
    return total


def _is_number(token: str) -> bool:
    return re.fullmatch(r"\d+(\.\d+)?|\d+/[1-9]\d*", token) is not None


def parse_ingredient(line: str) -> Ingredient:
    """Parse an ingredient line such as ``"200 g flour"``, ``"1 1/2 cups milk"``,
    ``"3 eggs"`` or ``"salt to taste"`` (no amount: ``amount`` is ``None``)."""
    text = line.strip()
    if not text:
        raise ValueError("empty ingredient line")
    tokens = text.split()
    count = 0
    while count < len(tokens) and _is_number(tokens[count]):
        count += 1
    if count == 0:
        return Ingredient(name=text, amount=None)
    amount = parse_amount(" ".join(tokens[:count]))
    rest = tokens[count:]
    if len(rest) > 1 and rest[0].lower() in UNITS:
        unit = rest[0]
        name = " ".join(rest[1:])
    else:
        unit = ""
        name = " ".join(rest)
    return Ingredient(name=name, amount=amount, unit=unit)


def parse_recipe_text(text: str) -> Recipe:
    """Parse the small recipe text format into a :class:`Recipe`."""
    title = ""
    servings = 1
    tags: list[str] = []
    ingredients: list[Ingredient] = []
    instructions: list[str] = []
    section = ""
    for raw in text.removeprefix(BOM).splitlines():
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
