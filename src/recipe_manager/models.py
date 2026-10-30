from dataclasses import dataclass, field


@dataclass
class Ingredient:
    name: str
    amount: float
    unit: str = ""


@dataclass
class Recipe:
    title: str
    servings: int
    ingredients: list[Ingredient] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)

    def scaled_to(self, servings: int) -> "Recipe":
        """Return a copy of the recipe scaled to a different number of servings."""
        factor = servings / self.servings
        return Recipe(
            title=self.title,
            servings=servings,
            ingredients=[
                Ingredient(i.name, i.amount * factor, i.unit) for i in self.ingredients
            ],
            tags=list(self.tags),
            instructions=list(self.instructions),
        )
