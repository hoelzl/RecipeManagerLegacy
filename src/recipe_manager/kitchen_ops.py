"""Typed, transport-independent state for the kitchen service (stock, quotes, reservations)."""

from copy import deepcopy
from threading import RLock
from typing import TypedDict


class Quote(TypedDict):
    session_id: str
    recipe_id: str
    servings: int
    required: dict[str, int]
    available: bool
    shortages: dict[str, int]
    total_cents: int


class Reservation(Quote):
    request_id: str
    reserved: bool
    replayed: bool


class InventoryItem(TypedDict):
    available: int
    unit_price_cents: int


class Inventory(TypedDict):
    session_id: str
    items: dict[str, InventoryItem]


class Menu(TypedDict):
    session_id: str
    recipes: dict[str, dict[str, int]]


class KitchenState:
    """Own one isolated menu, inventory, and idempotency namespace."""

    def __init__(
        self,
        *,
        session_id: str,
        menu: dict[str, dict[str, int]],
        stock: dict[str, int],
        price_cents: dict[str, int],
    ) -> None:
        self._session_id = session_id
        self._menu = deepcopy(menu)
        self._stock = stock.copy()
        self._price_cents = price_cents.copy()
        self._reservations: dict[str, tuple[str, int, Reservation]] = {}
        self._lock = RLock()

    def list_menu(self) -> Menu:
        return {"session_id": self._session_id, "recipes": deepcopy(self._menu)}

    def get_inventory(self) -> Inventory:
        with self._lock:
            return {
                "session_id": self._session_id,
                "items": {
                    name: {
                        "available": self._stock[name],
                        "unit_price_cents": self._price_cents[name],
                    }
                    for name in sorted(self._stock)
                },
            }

    def quote(self, recipe_id: str, servings: int) -> Quote:
        with self._lock:
            if recipe_id not in self._menu:
                raise ValueError(f"unknown recipe: {recipe_id}")
            if servings < 1:
                raise ValueError("servings must be positive")
            required = {
                name: amount * servings
                for name, amount in self._menu[recipe_id].items()
            }
            shortages = {
                name: amount - self._stock.get(name, 0)
                for name, amount in required.items()
                if amount > self._stock.get(name, 0)
            }
            total_cents = sum(
                required[name] * self._price_cents[name] for name in required
            )
            return {
                "session_id": self._session_id,
                "recipe_id": recipe_id,
                "servings": servings,
                "required": required,
                "available": not shortages,
                "shortages": shortages,
                "total_cents": total_cents,
            }

    def reserve(
        self, recipe_id: str, servings: int, request_id: str
    ) -> Reservation:
        with self._lock:
            key = request_id.strip()
            if not key:
                raise ValueError("request_id must not be empty")
            if key in self._reservations:
                stored_recipe, stored_servings, stored_result = self._reservations[key]
                if (recipe_id, servings) != (stored_recipe, stored_servings):
                    raise ValueError(
                        "request_id already used for a different recipe or serving count"
                    )
                return {**stored_result, "replayed": True}

            quote = self.quote(recipe_id, servings)
            reserved = quote["available"]
            if reserved:
                for name, amount in quote["required"].items():
                    self._stock[name] -= amount
            result: Reservation = {
                **quote,
                "request_id": key,
                "reserved": reserved,
                "replayed": False,
            }
            self._reservations[key] = (recipe_id, servings, result)
            return result.copy()
