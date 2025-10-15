# 🏗️ **Pydantic Builder**

## 📋 **Overview**

Pydantic Builder is a micro-framework that simplifies the creation of test fixtures and object construction for Pydantic models.
It implements a type-safe builder pattern that allows you to construct complex Pydantic model instances with a clean, fluent API.

### ✨ **Features**

- 🔒 **Type-safe** builder pattern with full generic type support
- 🔗 **Fluent API** with method chaining for readable object construction
- 🎯 **Focus on what matters** - only specify the fields you care about, use defaults for the rest
- 🧪 **Perfect for testing** - reduces boilerplate in test fixtures
- 💡 **IDE-friendly** - full autocompletion support for all model fields
- 🎨 **Clean test code** - keeps tests focused on what's being tested, not setup

## 📥 **Installation**

> 💡 The package is available on PyPI:

```shell
pip install pydantic_builder
```

> **Requirements:** Python >= 3.10

## 🚀 **Usage**

### 🔰 **Basic Usage**

Create a builder for any Pydantic model by extending `AbstractBaseBuilder`:

```python
from pydantic import BaseModel
from pydantic_builder import AbstractBaseBuilder

# Your Pydantic model
class Point(BaseModel):
    x: int
    y: int

# Create a builder for it
class PointBuilder(AbstractBaseBuilder[Point]):
    @property
    def default_instance(self) -> Point:
        return Point(x=0, y=0)

# Use the builder
point = PointBuilder().build()
# Point(x=0, y=0)

# Override specific fields
point = PointBuilder().with_(x=10).build()
# Point(x=10, y=0)

# Chain multiple field updates
point = PointBuilder().with_(x=5).with_(y=3).build()
# Point(x=5, y=3)
```

### 🌟 **Intermediate Usage - Simplifying Tests**

The builder pattern really shines in tests, where you want to focus on specific scenarios without cluttering your test with irrelevant setup:

```python
from pydantic import BaseModel
from pydantic_builder import AbstractBaseBuilder

class Range(BaseModel):
    min: float | None = None
    max: float | None = None
    
    def size(self) -> float:
        if self.min is None or self.max is None:
            return float("inf")
        return self.max - self.min

class RangeBuilder(AbstractBaseBuilder[Range]):
    @property
    def default_instance(self) -> Range:
        return Range(min=0, max=5)

# In your tests - only specify what's relevant to the test
def test_size_with_no_upper_bound():
    # Clear and focused - only the max=None matters for this test
    range_ = RangeBuilder().with_(max=None).build()
    assert range_.size() == float("inf")

def test_size_with_specific_bounds():
    # Chain multiple attributes cleanly
    range_ = RangeBuilder().with_(min=1).with_(max=10).build()
    assert range_.size() == 9
```

### 🔥 **Advanced Usage - Composing Builders**

For complex models with nested structures, builders can be composed together:

```python
from pydantic import BaseModel
from pydantic_builder import AbstractBaseBuilder

class Ingredient(BaseModel):
    id: int
    name: str
    quantity: float
    unit: str
    optional: bool = False

class Recipe(BaseModel):
    title: str
    serving_size: int
    preparation_time: float
    cooking_time: float
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

class IngredientBuilder(AbstractBaseBuilder[Ingredient]):
    @property
    def default_instance(self) -> Ingredient:
        return Ingredient(id=1, name="flour", quantity=100, unit="g")

class RecipeBuilder(AbstractBaseBuilder[Recipe]):
    @property
    def default_instance(self) -> Recipe:
        return Recipe(
            title="Default Recipe",
            serving_size=4,
            preparation_time=30,
            cooking_time=60,
            ingredients=[
                Ingredient(id=1, name="flour", quantity=100, unit="g"),
                Ingredient(id=2, name="sugar", quantity=50, unit="g"),
            ],
            steps=["Mix ingredients", "Bake for 30 minutes"],
        )

# Compose builders together for complex test scenarios
def test_recipe_with_custom_ingredients():
    recipe = (
        RecipeBuilder()
        .with_(
            title="Custom Cake",
            ingredients=[
                IngredientBuilder().with_(name="flour", quantity=200).build(),
                IngredientBuilder().with_(name="sugar", quantity=150).build(),
                IngredientBuilder().with_(name="eggs", quantity=3, unit="units").build(),
            ]
        )
        .build()
    )
    
    assert recipe.title == "Custom Cake"
    assert len(recipe.ingredients) == 3
    assert recipe.ingredients[0].quantity == 200


def test_recipe_scaling():

    # Arrange
    original_serving_size = 2 # 1st important value
    original_ingredient_quantity = 100 # 2nd important value
    new_serving_size = original_serving_size * 2 # 3rd important value

    recipe = RecipeBuilder()
    .with_(
        serving_size=original_serving_size # 1st important value
    )
    .with_(
        ingredients=[
            IngredientBuilder()
            .with_(
                quantity=original_ingredient_quantity # 2nd important value
            )
            .build()
            ]
    )
    .build()

    # Act
    scaled_recipe = recipe.scale_recipe(new_serving_size) # 3rd important value

    # Assert
    assert scaled_recipe.serving_size == new_serving_size
    assert scaled_recipe.ingredients[0].quantity == original_ingredient_quantity * 2
    
```

## 🎯 **Why Use Builders?**

**Without builders:**
```python
def test_ingredient_conversion():
    # Have to specify every field, even irrelevant ones
    ingredient = Ingredient(
        id=1, # Don't care about id for this test
        name="flour",  # Don't care about name for this test
        quantity=1,
        unit="kg",
        optional=False  # Don't care about optional for this test
    )
    assert ingredient.convert_to_grams().quantity == 1000
```

**With builders:**
```python
def test_ingredient_conversion():
    # Only specify what matters for this test
    ingredient = IngredientBuilder().with_(quantity=1, unit="kg").build()
    assert ingredient.convert_to_grams().quantity == 1000
```

## 🔍 **Going Further**

<!-- * 📚 Check out the [full documentation](#) for more examples (coming soon) -->
* 🧪 See the [test files](tests/tests_pydantic_builder/) for comprehensive usage examples
* 💬 Open an issue for questions or feature requests

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.
