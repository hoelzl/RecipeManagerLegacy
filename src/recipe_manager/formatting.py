"""Format ingredient amounts the way a cook would write them."""

from recipe_manager.models import Ingredient

# Units measured by weight or volume read naturally as decimals ("7.5 g");
# everything else (cups, spoons, pieces) reads better as a fraction ("1 1/2 cups").
METRIC_UNITS = {"g", "kg", "mg", "ml", "cl", "dl", "l"}

FRACTIONS = [(1 / 4, "1/4"), (1 / 3, "1/3"), (1 / 2, "1/2"), (2 / 3, "2/3"), (3 / 4, "3/4")]


def _decimal(amount: float) -> str:
    """Round to a precision that suits the magnitude and drop trailing zeros."""
    digits = 0 if abs(amount) >= 100 else 1 if abs(amount) >= 10 else 2
    text = f"{amount:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _fraction(amount: float) -> str:
    whole = int(amount)
    rest = amount - whole
    if rest < 0.02:
        return str(whole)
    if rest > 0.98:
        return str(whole + 1)
    for value, label in FRACTIONS:
        if abs(rest - value) < 0.02:
            return f"{whole} {label}" if whole else label
    return _decimal(amount)


def format_amount(amount: float | None, *, fractions: bool = False) -> str:
    """Return ``amount`` as text: ``200``, ``7.5``, ``0.33``; with ``fractions``
    common fractions are used instead (``1 1/2``). ``None`` gives ``""``."""
    if amount is None:
        return ""
    if fractions and amount > 0:
        return _fraction(amount)
    return _decimal(amount)


def format_ingredient(ingredient: Ingredient) -> str:
    """Return ``"200 g flour"``, ``"1 1/2 eggs"`` or just the name if unquantified.

    Names are used as written; there is no automatic pluralisation.
    """
    if ingredient.amount is None:
        return ingredient.name
    amount = format_amount(
        ingredient.amount, fractions=ingredient.unit.lower() not in METRIC_UNITS
    )
    parts = [amount, ingredient.unit, ingredient.name]
    return " ".join(part for part in parts if part)
