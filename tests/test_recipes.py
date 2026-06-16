import sys
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from recipes import (
    DailyMenuGenerator,
    NutritionLookup,
    NutritionistApp,
    RecipesData,
    SimilarRecipesEngine,
    guess_epicurious_url,
)


def test_guess_epicurious_url():
    result = guess_epicurious_url("Herb Chicken Quinoa Bowl")

    assert result == "https://www.epicurious.com/recipes/food/views/herb-chicken-quinoa-bowl"


def test_parse_cli_ingredients_removes_duplicates():
    raw_args = ["Chicken, tomato", "garlic", "chicken"]

    result = NutritionistApp.parse_cli_ingredients(raw_args)

    assert result == ["chicken", "tomato", "garlic"]


def test_nutrition_lookup_from_csv(tmp_path):
    csv_path = tmp_path / "nutrition.csv"

    content = (
        "ingredient,ingredient_norm,protein,sodium\n"
        "chicken,chicken,62,4\n"
        "tomato,tomato,2,1\n"
    )

    csv_path.write_text(content, encoding="utf-8")

    lookup = NutritionLookup(
        nutrition_csv_path=csv_path,
        allow_api_fallback=False,
    )

    result = lookup.get("chicken")

    assert result == {
        "protein": 62.0,
        "sodium": 4.0,
    }


def test_nutrition_lookup_missing_ingredient_without_api(tmp_path):
    csv_path = tmp_path / "nutrition.csv"

    content = (
        "ingredient,ingredient_norm,protein,sodium\n"
        "chicken,chicken,62,4\n"
    )

    csv_path.write_text(content, encoding="utf-8")

    lookup = NutritionLookup(
        nutrition_csv_path=csv_path,
        allow_api_fallback=False,
    )

    result = lookup.get("unknown ingredient")

    assert result == {}


def test_recipes_data_detects_ingredient_columns(tmp_path):
    csv_path = tmp_path / "recipes.csv"

    content = (
        "title,rating,url,chicken,tomato,calories\n"
        "Recipe A,4.5,http://example.com/a,1,0,500\n"
        "Recipe B,3.5,http://example.com/b,0,1,300\n"
    )

    csv_path.write_text(content, encoding="utf-8")

    data = RecipesData(csv_path)
    data.load()
    result = data.detect_ingredient_columns()

    assert result == ["chicken", "tomato"]


def test_recipes_data_recipe_ingredients(tmp_path):
    csv_path = tmp_path / "recipes.csv"

    content = (
        "title,rating,url,chicken,tomato,garlic\n"
        "Recipe A,4.5,http://example.com/a,1,0,1\n"
    )

    csv_path.write_text(content, encoding="utf-8")

    data = RecipesData(csv_path)
    df = data.load()
    data.detect_ingredient_columns()

    result = data.recipe_ingredients(df.iloc[0])

    assert result == ["chicken", "garlic"]


def test_similar_recipes_engine_top_k():
    df = pd.DataFrame(
        {
            "title": ["Chicken Bowl", "Tomato Salad", "Beef Stew"],
            "rating": [4.5, 4.0, 3.8],
            "url": [
                "http://example.com/chicken",
                "http://example.com/tomato",
                "http://example.com/beef",
            ],
            "chicken": [1, 0, 0],
            "tomato": [1, 1, 0],
            "beef": [0, 0, 1],
        }
    )

    engine = SimilarRecipesEngine(
        recipes_df=df,
        ingredient_cols=["chicken", "tomato", "beef"],
    )

    result = engine.top_k(["chicken", "tomato"], k=2)

    assert len(result) == 2
    assert result[0].title == "Chicken Bowl"


def test_similar_recipes_engine_returns_empty_for_unknown_ingredients():
    df = pd.DataFrame(
        {
            "title": ["Chicken Bowl"],
            "rating": [4.5],
            "url": ["http://example.com/chicken"],
            "chicken": [1],
            "tomato": [0],
        }
    )

    engine = SimilarRecipesEngine(
        recipes_df=df,
        ingredient_cols=["chicken", "tomato"],
    )

    result = engine.top_k(["unknown"], k=3)

    assert result == []


def test_daily_menu_infer_meal_type():
    assert DailyMenuGenerator.infer_meal_type("Blueberry Pancake") == "BREAKFAST"
    assert DailyMenuGenerator.infer_meal_type("Chicken Salad") == "LUNCH"
    assert DailyMenuGenerator.infer_meal_type("Beef Pasta") == "DINNER"


def test_daily_menu_recipe_ingredients():
    df = pd.DataFrame(
        {
            "title": ["Chicken Bowl"],
            "rating": [4.5],
            "url": ["http://example.com/chicken"],
            "chicken": [1],
            "tomato/garlic": [1],
        }
    )

    lookup = NutritionLookup(allow_api_fallback=False)

    generator = DailyMenuGenerator(
        recipes_df=df,
        ingredient_cols=["chicken", "tomato/garlic"],
        nutrition_lookup=lookup,
    )

    result = generator.recipe_ingredients(df.iloc[0])

    assert result == ["chicken", "tomato", "garlic"]


def test_daily_menu_format_empty_menu():
    menu = {
        "BREAKFAST": None,
        "LUNCH": None,
        "DINNER": None,
    }

    result = DailyMenuGenerator.format_daily_menu(menu)

    assert "BREAKFAST" in result
    assert "LUNCH" in result
    assert "DINNER" in result
    assert "No recipe available." in result