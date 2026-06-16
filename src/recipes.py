"""
Core logic for Smart Recipe Nutritionist.

This module provides the main classes used by the command-line application:

- RecipesData: loads recipe datasets and detects ingredient columns.
- NutritionLookup: retrieves nutrition facts from a local CSV or USDA API.
- SimilarRecipesEngine: recommends similar recipes using cosine similarity.
- RatingForecaster: predicts whether an ingredient combination is promising.
- DailyMenuGenerator: generates a breakfast, lunch, and dinner menu.
- NutritionistApp: high-level application interface used by the CLI.

The module is designed for portfolio and educational use.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.metrics.pairwise import cosine_similarity


def guess_epicurious_url(title: str) -> str:
    """
    Build a probable Epicurious URL from a recipe title.

    This is a fallback used when the dataset does not provide a URL.
    """
    slug = str(title).lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)

    return f"https://www.epicurious.com/recipes/food/views/{slug}"


@dataclass
class SimilarRecipe:
    """
    Container for a similar recipe recommendation.
    """

    title: str
    rating: float
    url: str
    ingredients: List[str]


class RecipesData:
    """
    Utility class for loading recipe data and detecting ingredient columns.

    The Epicurious-style recipe dataset contains many binary ingredient
    columns. This class identifies those columns automatically.
    """

    DEFAULT_NON_INGREDIENTS = {
        "title",
        "rating",
        "calories",
        "protein",
        "fat",
        "sodium",
        "url",
        "desc",
        "description",
        "date",
        "image",
        "servings",
        "yield",
        "total_time",
        "prep_time",
        "cook_time",
    }

    def __init__(
        self,
        data_path: str | Path,
        non_ingredient_cols: Optional[Iterable[str]] = None,
    ):
        self.data_path = Path(data_path)
        self.non_ingredient_cols = (
            set(non_ingredient_cols or set()) | self.DEFAULT_NON_INGREDIENTS
        )

        self.df: Optional[pd.DataFrame] = None
        self.ingredient_cols: Optional[List[str]] = None

    def load(self) -> pd.DataFrame:
        """
        Load the dataset into a pandas DataFrame.
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Recipe data file not found: {self.data_path}")

        self.df = pd.read_csv(self.data_path)
        return self.df

    def detect_ingredient_columns(self) -> List[str]:
        """
        Detect binary ingredient columns.

        A column is considered an ingredient column if:
        - it is not in the known non-ingredient columns;
        - all non-null values are binary-like values.
        """
        if self.df is None:
            self.load()

        assert self.df is not None

        cols: List[str] = []

        for col in self.df.columns:
            if col in self.non_ingredient_cols:
                continue

            values = self.df[col].dropna().unique()

            if len(values) == 0:
                continue

            if set(values).issubset({0, 1, 0.0, 1.0, True, False}):
                cols.append(col)

        self.ingredient_cols = cols
        return cols

    def ingredient_matrix(self) -> pd.DataFrame:
        """
        Return a binary matrix of ingredient columns.
        """
        if self.df is None:
            self.load()

        if self.ingredient_cols is None:
            self.detect_ingredient_columns()

        assert self.df is not None
        assert self.ingredient_cols is not None

        return self.df[self.ingredient_cols].fillna(0).astype(int)

    def recipe_ingredients(self, row: pd.Series) -> List[str]:
        """
        Return the list of ingredients present in a recipe row.
        """
        if self.ingredient_cols is None:
            self.detect_ingredient_columns()

        assert self.ingredient_cols is not None

        return [
            col
            for col in self.ingredient_cols
            if int(row.get(col, 0)) == 1
        ]


class NutritionLookup:
    """
    Retrieve nutrition facts for ingredients.

    The class first attempts to read nutrition data from a local CSV file.
    Optionally, it can fall back to the USDA FoodData Central API if an
    API key is provided through the USDA_API_KEY environment variable.

    The API key is intentionally not hardcoded in the source code.
    """

    DAILY_VALUE_MAP = {
        "protein": 50.0,
        "total fat": 78.0,
        "fat": 78.0,
        "saturated fat": 20.0,
        "cholesterol": 300.0,
        "sodium": 2300.0,
        "carbohydrate": 275.0,
        "total carbohydrate": 275.0,
        "fiber": 28.0,
        "sugars": 50.0,
        "calcium": 1300.0,
        "iron": 18.0,
        "potassium": 4700.0,
        "vitamin d": 20.0,
        "magnesium": 420.0,
        "zinc": 11.0,
    }

    FDC_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    def __init__(
        self,
        nutrition_csv_path: Optional[str | Path] = None,
        api_key: Optional[str] = None,
        allow_api_fallback: bool = True,
    ):
        self.nutrition_csv_path = Path(nutrition_csv_path) if nutrition_csv_path else None
        self.api_key = api_key or os.getenv("USDA_API_KEY")
        self.allow_api_fallback = allow_api_fallback
        self.nutrition_df: Optional[pd.DataFrame] = None

        if self.nutrition_csv_path and self.nutrition_csv_path.exists():
            self.nutrition_df = pd.read_csv(self.nutrition_csv_path)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize an ingredient name.
        """
        return re.sub(r"\s+", " ", str(name).strip().lower())

    @staticmethod
    def _clean_query_name(ingredient: str) -> str:
        """
        Clean ingredient names before API lookup.
        """
        ingredient = NutritionLookup._normalize_name(ingredient)

        if "/" in ingredient:
            ingredient = ingredient.split("/")[0].strip()

        if "," in ingredient:
            ingredient = ingredient.split(",")[0].strip()

        if "(" in ingredient:
            ingredient = ingredient.split("(")[0].strip()

        return ingredient

    def get_from_csv(self, ingredient: str) -> Dict[str, float]:
        """
        Retrieve nutrition facts from the local nutrition CSV.
        """
        if self.nutrition_df is None:
            return {}

        key = self._normalize_name(ingredient)

        if "ingredient_norm" not in self.nutrition_df.columns:
            return {}

        rows = self.nutrition_df[self.nutrition_df["ingredient_norm"] == key]

        if rows.empty:
            return {}

        row = rows.iloc[0]
        result: Dict[str, float] = {}

        for col in self.nutrition_df.columns:
            if col in {"ingredient", "ingredient_norm"}:
                continue

            if pd.notna(row[col]):
                result[col] = float(row[col])

        return result

    def fetch_ingredient(self, ingredient: str) -> Dict[str, float]:
        """
        Fetch nutrition facts from USDA FoodData Central.

        Returns nutrient values as percentages of recommended daily values.
        """
        if not self.api_key:
            return {}

        ingredient = self._clean_query_name(ingredient)

        params = {
            "query": ingredient,
            "pageSize": 1,
            "api_key": self.api_key,
        }

        nutrient_name_map = {
            "protein": "protein",
            "cholesterol": "cholesterol",
            "sodium": "sodium",
            "fiber": "fiber",
            "sugars": "sugars",
            "potassium": "potassium",
            "vitamin d": "vitamin d",
            "magnesium": "magnesium",
            "zinc": "zinc",
            "total lipid (fat)": "total fat",
            "fatty acids, total saturated": "saturated fat",
            "carbohydrate, by difference": "total carbohydrate",
            "calcium, ca": "calcium",
            "iron, fe": "iron",
        }

        last_error = None

        for attempt in range(3):
            try:
                response = requests.get(self.FDC_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                foods = data.get("foods", [])

                if not foods:
                    return {}

                food = foods[0]
                nutrients: Dict[str, float] = {}

                for item in food.get("foodNutrients", []):
                    raw_name = self._normalize_name(item.get("nutrientName", ""))
                    mapped_name = nutrient_name_map.get(raw_name, raw_name)

                    value = item.get("value")
                    unit = str(item.get("unitName") or "").lower()

                    if value is None:
                        continue

                    if mapped_name not in self.DAILY_VALUE_MAP:
                        continue

                    if unit not in {"g", "mg", "mcg"}:
                        continue

                    daily_value = self.DAILY_VALUE_MAP[mapped_name]
                    percent = float(value) / daily_value * 100
                    nutrients[mapped_name] = round(percent, 2)

                return nutrients

            except requests.exceptions.RequestException as exc:
                last_error = exc
                time.sleep(2 * (attempt + 1))

        print(f"Skipping API lookup for {ingredient}: {last_error}")
        return {}

    def get(self, ingredient: str) -> Dict[str, float]:
        """
        Get nutrition facts from CSV first, then optionally from API.
        """
        if self.nutrition_df is not None:
            result = self.get_from_csv(ingredient)

            if result:
                return result

        if self.allow_api_fallback:
            return self.fetch_ingredient(ingredient)

        return {}

    def build_csv_from_ingredients(
        self,
        ingredients: Iterable[str],
        out_path: str | Path,
    ) -> pd.DataFrame:
        """
        Build a local nutrition CSV for a set of ingredients.

        This is useful for creating reproducible offline nutrition data.
        """
        rows = []

        for ingredient in sorted({self._normalize_name(i) for i in ingredients}):
            row = {
                "ingredient": ingredient,
                "ingredient_norm": self._normalize_name(ingredient),
            }

            try:
                row.update(self.fetch_ingredient(ingredient))
            except Exception as exc:
                print(f"Skipping {ingredient}: {exc}")

            rows.append(row)

        out_df = pd.DataFrame(rows)
        out_path = Path(out_path)
        out_df.to_csv(out_path, index=False)

        self.nutrition_df = out_df
        self.nutrition_csv_path = out_path

        return out_df


class SimilarRecipesEngine:
    """
    Recommend recipes that are similar to a list of input ingredients.

    Similarity is computed using cosine similarity between:
    - a binary query vector built from user ingredients;
    - binary ingredient vectors from recipe data.
    """

    def __init__(
        self,
        recipes_df: pd.DataFrame,
        ingredient_cols: List[str],
        url_col: str = "url",
    ):
        self.recipes_df = recipes_df.copy()
        self.ingredient_cols = ingredient_cols
        self.url_col = url_col

        self.matrix = (
            self.recipes_df[self.ingredient_cols]
            .fillna(0)
            .astype(int)
            .values
        )

    def _query_vector(self, ingredients: Iterable[str]) -> np.ndarray:
        """
        Convert input ingredients into a binary vector.
        """
        ingredients_set = {
            str(item).strip().lower()
            for item in ingredients
        }

        vector = []

        for col in self.ingredient_cols:
            col_lower = col.lower()
            match = any(
                ingredient in col_lower or col_lower in ingredient
                for ingredient in ingredients_set
            )
            vector.append(1 if match else 0)

        return np.array(vector, dtype=int)

    def top_k(self, ingredients: Iterable[str], k: int = 3) -> List[SimilarRecipe]:
        """
        Return the top-k most similar recipes.
        """
        query_vector = self._query_vector(ingredients)

        if query_vector.sum() == 0:
            return []

        similarities = cosine_similarity(
            self.matrix,
            query_vector.reshape(1, -1),
        ).ravel()

        order = np.argsort(-similarities)

        results: List[SimilarRecipe] = []

        for idx in order:
            if similarities[idx] <= 0:
                continue

            row = self.recipes_df.iloc[idx]
            title = str(row.get("title", "Untitled"))

            url = row.get(self.url_col, "")

            if pd.isna(url) or not str(url).strip():
                url = guess_epicurious_url(title)

            recipe_ingredients = [
                col
                for col in self.ingredient_cols
                if int(row.get(col, 0)) == 1
            ]

            results.append(
                SimilarRecipe(
                    title=title,
                    rating=float(row.get("rating", np.nan)),
                    url=str(url),
                    ingredients=recipe_ingredients,
                )
            )

            if len(results) == k:
                break

        return results


class RatingForecaster:
    """
    Predict the quality label of an ingredient combination.

    The class loads:
    - a trained scikit-learn model;
    - the feature column order used during training.
    """

    def __init__(self, model_path: str | Path, feature_columns_path: str | Path):
        self.model_path = Path(model_path)
        self.feature_columns_path = Path(feature_columns_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        if not self.feature_columns_path.exists():
            raise FileNotFoundError(
                f"Feature columns file not found: {self.feature_columns_path}"
            )

        self.model = joblib.load(self.model_path)
        self.feature_columns = joblib.load(self.feature_columns_path)

        if self.model is None:
            raise ValueError("Loaded model is None.")

        if self.feature_columns is None:
            raise ValueError("Loaded feature columns are None.")

    def _vectorize(self, ingredients: Iterable[str]) -> pd.DataFrame:
        """
        Convert ingredients into a one-row feature matrix.
        """
        values = {col: 0 for col in self.feature_columns}

        for ingredient in ingredients:
            key = str(ingredient).strip().lower()

            if key in values:
                values[key] = 1

        return pd.DataFrame([values])

    def predict_label(self, ingredients: Iterable[str]) -> str:
        """
        Predict label for the ingredient combination.
        """
        features = self._vectorize(ingredients)
        prediction = self.model.predict(features)[0]

        return str(prediction)

    @staticmethod
    def label_to_message(label: str) -> str:
        """
        Convert a predicted label into a user-friendly message.
        """
        mapping = {
            "bad": (
                "You might find it tasty, but in our opinion, it is a bad idea "
                "to have a dish with that list of ingredients."
            ),
            "so-so": (
                "It may work, but it looks like a so-so combination rather than "
                "an impressive dish."
            ),
            "great": (
                "This looks like a great combination. We think it has a strong "
                "chance to become a tasty dish."
            ),
        }

        return mapping.get(str(label), str(label))


class DailyMenuGenerator:
    """
    Generate a simple daily menu using recipe ratings and nutrition data.
    """

    def __init__(
        self,
        recipes_df: pd.DataFrame,
        ingredient_cols: List[str],
        nutrition_lookup: NutritionLookup,
    ):
        self.recipes_df = recipes_df.copy()
        self.ingredient_cols = ingredient_cols
        self.nutrition_lookup = nutrition_lookup

    @staticmethod
    def infer_meal_type(title: str) -> str:
        """
        Infer a rough meal type from recipe title keywords.
        """
        title = str(title).lower()

        breakfast_keywords = [
            "breakfast",
            "omelet",
            "omelette",
            "muffin",
            "pancake",
            "granola",
            "oatmeal",
            "toast",
            "egg",
        ]

        lunch_keywords = [
            "salad",
            "sandwich",
            "wrap",
            "soup",
            "bowl",
        ]

        dinner_keywords = [
            "steak",
            "chicken",
            "beef",
            "pasta",
            "roast",
            "dinner",
            "salmon",
            "pork",
        ]

        if any(word in title for word in breakfast_keywords):
            return "BREAKFAST"

        if any(word in title for word in lunch_keywords):
            return "LUNCH"

        if any(word in title for word in dinner_keywords):
            return "DINNER"

        return "LUNCH"

    def recipe_ingredients(self, row: pd.Series) -> List[str]:
        """
        Return cleaned recipe ingredient names from a recipe row.
        """
        raw_ingredients = [
            col
            for col in self.ingredient_cols
            if int(row.get(col, 0)) == 1
        ]

        cleaned = []

        for ingredient in raw_ingredients:
            ingredient = ingredient.lower().strip()

            if "/" in ingredient:
                parts = [
                    part.strip()
                    for part in ingredient.split("/")
                    if part.strip()
                ]
                cleaned.extend(parts)
            else:
                cleaned.append(ingredient)

        seen = set()
        result = []

        for ingredient in cleaned:
            if ingredient not in seen:
                seen.add(ingredient)
                result.append(ingredient)

        return result

    def recipe_nutrients(self, ingredients: List[str]) -> Dict[str, float]:
        """
        Aggregate nutrition percentages for a recipe.
        """
        total: Dict[str, float] = {}

        for ingredient in ingredients:
            facts = self.nutrition_lookup.get(ingredient)

            if not facts:
                continue

            for nutrient, value in facts.items():
                total[nutrient] = total.get(nutrient, 0.0) + value

        return total

    def recipe_score(self, row: pd.Series) -> float:
        """
        Score a recipe using rating and nutrition balance.
        """
        ingredients = self.recipe_ingredients(row)
        nutrients = self.recipe_nutrients(ingredients)

        if not nutrients:
            return -1e9

        total_percent = sum(nutrients.values())
        penalty = sum(value - 100 for value in nutrients.values() if value > 100)

        rating = float(row.get("rating", 0.0))

        return rating * 10 + total_percent - penalty * 2

    def candidates_by_meal(self, meal_type: str) -> pd.DataFrame:
        """
        Return recipe candidates for a meal type.
        """
        df = self.recipes_df.copy()
        df["meal_type"] = df["title"].apply(self.infer_meal_type)
        df = df[df["meal_type"] == meal_type].copy()

        if not df.empty:
            df = df.sort_values("rating", ascending=False).head(200)

        return df

    def best_recipe_for_meal(self, meal_type: str) -> Optional[dict]:
        """
        Select one strong recipe candidate for a given meal type.
        """
        candidates = self.candidates_by_meal(meal_type)

        if candidates.empty:
            return None

        candidates = candidates.copy()
        candidates["menu_score"] = candidates.apply(self.recipe_score, axis=1)
        candidates = candidates.sort_values(
            ["menu_score", "rating"],
            ascending=False,
        )

        top_n = min(10, len(candidates))
        chosen = candidates.head(top_n).sample(1).iloc[0]

        ingredients = self.recipe_ingredients(chosen)
        nutrients = self.recipe_nutrients(ingredients)

        title = str(chosen.get("title", "Untitled"))
        url = chosen.get("url", "")

        if pd.isna(url) or not str(url).strip():
            url = guess_epicurious_url(title)

        return {
            "title": title,
            "rating": float(chosen.get("rating", 0.0)),
            "ingredients": ingredients,
            "nutrients": nutrients,
            "url": url,
        }

    def generate_daily_menu(self) -> Dict[str, Optional[dict]]:
        """
        Generate breakfast, lunch, and dinner recommendations.
        """
        return {
            "BREAKFAST": self.best_recipe_for_meal("BREAKFAST"),
            "LUNCH": self.best_recipe_for_meal("LUNCH"),
            "DINNER": self.best_recipe_for_meal("DINNER"),
        }

    @staticmethod
    def format_daily_menu(menu: Dict[str, Optional[dict]]) -> str:
        """
        Format the daily menu as readable text.
        """
        sections = []

        nutrient_order = [
            "protein",
            "total carbohydrate",
            "total fat",
            "saturated fat",
            "cholesterol",
            "sodium",
            "fiber",
            "sugars",
            "calcium",
            "iron",
            "potassium",
            "vitamin d",
            "magnesium",
            "zinc",
        ]

        for meal_name in ["BREAKFAST", "LUNCH", "DINNER"]:
            item = menu.get(meal_name)

            sections.append(meal_name)
            sections.append("---------------------")

            if item is None:
                sections.append("No recipe available.")
                sections.append("")
                continue

            sections.append(f'{item["title"]} (rating: {item["rating"]})')
            sections.append("Ingredients:")

            for ingredient in item["ingredients"]:
                sections.append(f"- {ingredient}")

            sections.append("Nutrients:")

            nutrients = item["nutrients"]
            shown_any = False

            for nutrient in nutrient_order:
                if nutrient in nutrients:
                    sections.append(f"- {nutrient}: {nutrients[nutrient]:.0f}%")
                    shown_any = True

            if not shown_any:
                sections.append("- No nutrient data available")

            sections.append(f'URL: {item["url"]}')
            sections.append("")

        return "\n".join(sections).strip()


class NutritionistApp:
    """
    High-level application interface used by the CLI.
    """

    def __init__(
        self,
        model_path: str | Path,
        feature_columns_path: str | Path,
        nutrition_csv_path: str | Path,
        similar_recipes_csv_path: str | Path,
    ):
        self.forecaster = RatingForecaster(model_path, feature_columns_path)

        self.nutrition = NutritionLookup(
            nutrition_csv_path=nutrition_csv_path,
            allow_api_fallback=True,
        )

        similar_recipes_csv_path = Path(similar_recipes_csv_path)

        if not similar_recipes_csv_path.exists():
            raise FileNotFoundError(
                f"Similar recipes file not found: {similar_recipes_csv_path}"
            )

        self.similar_df = pd.read_csv(similar_recipes_csv_path)

        non_ingredient = {"title", "rating", "url"}
        self.ingredient_cols = [
            col
            for col in self.similar_df.columns
            if col not in non_ingredient
        ]

        self.similar_engine = SimilarRecipesEngine(
            recipes_df=self.similar_df,
            ingredient_cols=self.ingredient_cols,
            url_col="url",
        )

        self.menu_nutrition = NutritionLookup(
            nutrition_csv_path=nutrition_csv_path,
            allow_api_fallback=False,
        )

        self.menu_generator = DailyMenuGenerator(
            recipes_df=self.similar_df,
            ingredient_cols=self.ingredient_cols,
            nutrition_lookup=self.menu_nutrition,
        )

    def daily_menu(self) -> str:
        """
        Generate and format a daily menu.
        """
        menu = self.menu_generator.generate_daily_menu()
        return self.menu_generator.format_daily_menu(menu)

    @staticmethod
    def parse_cli_ingredients(raw_args: Iterable[str]) -> List[str]:
        """
        Parse command-line ingredients.

        Supports input such as:
        - "chicken, tomato, garlic"
        - "chicken" "tomato" "garlic"
        """
        ingredients: List[str] = []

        for item in raw_args:
            parts = [
                part.strip().lower()
                for part in str(item).split(",")
                if part.strip()
            ]
            ingredients.extend(parts)

        seen = set()
        result: List[str] = []

        for ingredient in ingredients:
            if ingredient not in seen:
                seen.add(ingredient)
                result.append(ingredient)

        return result

    def forecast_section(self, ingredients: List[str]) -> str:
        """
        Build the forecast output section.
        """
        label = self.forecaster.predict_label(ingredients)
        message = self.forecaster.label_to_message(label)

        return "I. OUR FORECAST\n" + message

    def nutrition_section(self, ingredients: List[str]) -> str:
        """
        Build the nutrition facts output section.
        """
        lines = ["II. NUTRITION FACTS"]

        preferred_order = [
            "protein",
            "total carbohydrate",
            "total fat",
            "saturated fat",
            "cholesterol",
            "sodium",
            "fiber",
            "sugars",
            "calcium",
            "iron",
            "potassium",
            "vitamin d",
            "magnesium",
            "zinc",
        ]

        for ingredient in ingredients:
            lines.append(ingredient.title())
            facts = self.nutrition.get(ingredient)

            if not facts:
                lines.append("No nutrition facts found.")
                continue

            for nutrient in preferred_order:
                if nutrient in facts:
                    lines.append(
                        f"{nutrient.title()} - {facts[nutrient]:.0f}% of Daily Value"
                    )

        return "\n".join(lines)

    def similar_section(self, ingredients: List[str]) -> str:
        """
        Build the similar recipes output section.
        """
        lines = ["III. TOP-3 SIMILAR RECIPES:"]
        top_recipes = self.similar_engine.top_k(ingredients, k=3)

        if not top_recipes:
            lines.append("No similar recipes found.")
            return "\n".join(lines)

        for recipe in top_recipes:
            lines.append(f"- {recipe.title}, rating: {recipe.rating}, URL:")
            lines.append(recipe.url)

        return "\n".join(lines)

    def run(self, ingredients: Iterable[str]) -> str:
        """
        Run the full assistant pipeline for a list of ingredients.
        """
        parsed = self.parse_cli_ingredients(ingredients)

        if not parsed:
            return "No ingredients were provided."

        sections = [
            self.forecast_section(parsed),
            self.nutrition_section(parsed),
            self.similar_section(parsed),
        ]

        return "\n\n".join(sections)