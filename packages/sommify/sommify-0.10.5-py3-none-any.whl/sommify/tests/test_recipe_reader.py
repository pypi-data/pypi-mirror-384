from sommify.recipes.reader import RecipeReader


def test_beef_recipe() -> bool:
    title = "Braised Beef Short Ribs"
    ingredient = [
        "beef short ribs",
        "red wine",
        "beef broth",
        "onion",
        "carrot",
        "celery",
        "garlic",
        "thyme",
        "rosemary",
        "bay leaf",
        "flour",
        "butter",
        "salt",
        "pepper",
    ]
    recipe_vector = RecipeReader().read(title, ingredient)
    assert recipe_vector["categories"] == ["beef"] and recipe_vector["models"] == [
        "red-meat"
    ]


def test_pizza_recipe() -> None:
    title = "Margherita Pizza"
    ingredient = [
        "pizza dough",
        "tomato sauce",
        "mozzarella cheese",
        "basil",
        "olive oil",
        "salt",
    ]
    recipe_vector = RecipeReader().read(title, ingredient)
    assert recipe_vector["categories"] == ["pizza"] and recipe_vector["models"] == [
        "other"
    ]


def test_dessert_recipe() -> None:
    title = "Chocolate Lava Cake"
    ingredient = [
        "butter",
        "dark chocolate",
        "sugar",
        "eggs",
        "flour",
        "vanilla extract",
    ]
    recipe_vector = RecipeReader().read(title, ingredient)
    assert recipe_vector["categories"] == ["dessert"] and recipe_vector["models"] == [
        "sweets"
    ]


def test_white_meat_recipe() -> None:
    title = "Grilled Chicken Breast"
    ingredient = [
        "chicken breast",
        "olive oil",
        "lemon juice",
        "garlic",
        "rosemary",
        "salt",
        "pepper",
    ]
    recipe_vector = RecipeReader().read(title, ingredient)
    assert recipe_vector["categories"] == ["poultry"] and recipe_vector["models"] == [
        "white-meat"
    ]


def test_fish_recipe() -> None:
    title = "Baked Salmon with Dill"
    ingredient = [
        "salmon fillets",
        "dill",
        "lemon",
        "butter",
        "garlic",
        "salt",
        "pepper",
    ]
    recipe_vector = RecipeReader().read(title, ingredient)
    assert recipe_vector["categories"] == ["salmon"] and recipe_vector["models"] == [
        "fish"
    ]


def test_beef_recipe_small() -> bool:
    title = "Braised Beef Short Ribs"
    ingredient = [
        "beef short ribs",
        "red wine",
        "beef broth",
        "onion",
        "carrot",
        "celery",
        "garlic",
        "thyme",
        "rosemary",
        "bay leaf",
        "flour",
        "butter",
        "salt",
        "pepper",
    ]
    recipe_vector = RecipeReader(small=True).read(title, ingredient)
    assert recipe_vector["categories"] == ["beef"] and recipe_vector["models"] == [
        "red-meat"
    ]


def test_pizza_recipe_small() -> None:
    title = "Margherita Pizza"
    ingredient = [
        "pizza dough",
        "tomato sauce",
        "mozzarella cheese",
        "basil",
        "olive oil",
        "salt",
    ]
    recipe_vector = RecipeReader(small=True).read(title, ingredient)
    assert recipe_vector["categories"] == ["pizza"] and recipe_vector["models"] == [
        "other"
    ]


def test_dessert_recipe_small() -> None:
    title = "Chocolate Lava Cake"
    ingredient = [
        "butter",
        "dark chocolate",
        "sugar",
        "eggs",
        "flour",
        "vanilla extract",
    ]
    recipe_vector = RecipeReader(small=True).read(title, ingredient)
    assert recipe_vector["categories"] == ["dessert"] and recipe_vector["models"] == [
        "sweets"
    ]


def test_white_meat_recipe_small() -> None:
    title = "Grilled Chicken Breast"
    ingredient = [
        "chicken breast",
        "olive oil",
        "lemon juice",
        "garlic",
        "rosemary",
        "salt",
        "pepper",
    ]
    recipe_vector = RecipeReader(small=True).read(title, ingredient)
    assert recipe_vector["categories"] == ["poultry"] and recipe_vector["models"] == [
        "white-meat"
    ]


def test_fish_recipe_small() -> None:
    title = "Baked Salmon with Dill"
    ingredient = [
        "salmon fillets",
        "dill",
        "lemon",
        "butter",
        "garlic",
        "salt",
        "pepper",
    ]
    recipe_vector = RecipeReader(small=True).read(title, ingredient)
    assert recipe_vector["categories"] == ["salmon"] and recipe_vector["models"] == [
        "fish"
    ]
