#!/usr/bin/env python3
"""
Command-line entry point for Smart Recipe Nutritionist.

Usage examples:
    python src/nutritionist.py chicken, tomato, garlic
    python src/nutritionist.py --menu
"""

from __future__ import annotations

import sys
from pathlib import Path

from recipes import NutritionistApp


def build_app() -> NutritionistApp:
    """
    Build the NutritionistApp using project-relative paths.

    This makes the CLI work from the project root without relying on
    hardcoded absolute paths.
    """
    project_root = Path(__file__).resolve().parents[1]

    return NutritionistApp(
        model_path=project_root / "models" / "best_rating_label_model.joblib",
        feature_columns_path=project_root / "models" / "feature_columns.joblib",
        nutrition_csv_path=project_root / "data" / "ingredient_nutrition_daily_values.csv",
        similar_recipes_csv_path=project_root / "data" / "similar_recipes.csv",
    )


def main() -> int:
    """
    Run the command-line application.
    """
    try:
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python src/nutritionist.py ingredient1, ingredient2, ingredient3")
            print("  python src/nutritionist.py --menu")
            return 1

        app = build_app()

        if sys.argv[1] == "--menu":
            print(app.daily_menu())
            return 0

        output = app.run(sys.argv[1:])
        print(output)
        return 0

    except FileNotFoundError as exc:
        print(f"Missing file: {exc}")
        return 1

    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())