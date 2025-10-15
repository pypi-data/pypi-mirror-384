"""`pydantic_builders.example` module.

This module contains simple classes with simple methods for testing purposes.
See `tests/tests_pydantic_builder/test_example.py` for example of usage of the `AbstractBaseBuilder` class.
"""

from typing import Self
from pydantic import BaseModel


class Range(BaseModel):
    """Dummy class for testing representing a range."""

    min: float | None = None
    max: float | None = None

    def __add__(self, other: Self | float | int) -> Self:
        if isinstance(other, (float, int)):
            return Range(min=self.min + other, max=self.max + other)
        return Range(min=self.min + other.min, max=self.max + other.max)

    def __radd__(self, other: float | int) -> Self:
        return self.__add__(other)

    def __mul__(self, other: float | int) -> Self:
        return Range(min=self.min * other, max=self.max * other)

    def size(self) -> float:
        if self.min is None or self.max is None:
            return float("inf")

        return self.max - self.min


class Ingredient(BaseModel):
    """Dummy class for testing representing a recipe ingredient."""

    id: int
    name: str
    quantity: float | Range
    unit: str
    optional: bool = False

    def convert_to_grams(self) -> Self:
        """Convert ingredient quantity to grams based on common unit conversions.

        Returns the quantity in grams, or the original quantity if unit is unknown.
        """
        conversions = {
            "kg": 1000.0,
            "g": 1.0,
            "lb": 453.592,
            "oz": 28.3495,
            "cup": 240.0,  # Approximate for water/milk
            "tbsp": 15.0,  # Approximate for liquids
            "tsp": 5.0,  # Approximate for liquids
        }

        return self.__class__(
            id=self.id,
            name=self.name,
            quantity=self.quantity * conversions.get(self.unit.lower(), 1.0),
            unit="g",
            optional=self.optional,
        )


class Recipe(BaseModel):
    """Dummy class for testing representing a recipe."""

    title: str
    serving_size: int | None = None
    preparation_time: float | Range | None
    cooking_time: float | Range | None = None
    ingredients: list[Ingredient]
    steps: list[str] = []

    def scale_recipe(self, new_serving_size: int) -> Self:
        """Scale recipe ingredients based on new serving size."""
        if self.serving_size is None or self.serving_size == 0:
            raise ValueError("Cannot scale recipe without original serving size")

        scale_factor = new_serving_size / self.serving_size

        scaled_ingredients = []
        for ingredient in self.ingredients:
            scaled_ingredient = Ingredient(
                id=ingredient.id,
                name=ingredient.name,
                quantity=ingredient.quantity * scale_factor,
                unit=ingredient.unit,
                optional=ingredient.optional,
            )
            scaled_ingredients.append(scaled_ingredient)

        return Recipe(
            **self.model_dump(exclude={"serving_size", "ingredients"}),
            ingredients=scaled_ingredients,
            serving_size=new_serving_size,
        )

    def get_total_time_range(self) -> Range:
        """Calculate total cooking time range including prep and cooking time."""
        prep_min = prep_max = cook_min = cook_max = 0.0

        # Handle preparation time
        if isinstance(self.preparation_time, Range):
            prep_min = self.preparation_time.min or 0.0
            prep_max = self.preparation_time.max or 0.0
        elif isinstance(self.preparation_time, (int, float)):
            prep_min = prep_max = float(self.preparation_time)

        # Handle cooking time
        if isinstance(self.cooking_time, Range):
            cook_min = self.cooking_time.min or 0.0
            cook_max = self.cooking_time.max or 0.0
        elif isinstance(self.cooking_time, (int, float)):
            cook_min = cook_max = float(self.cooking_time)

        return Range(min=prep_min + cook_min, max=prep_max + cook_max)

    def get_total_grams(self) -> float:
        """Calculate total grams of ingredients."""

        return sum(
            ingredient.convert_to_grams().quantity for ingredient in self.ingredients
        )
