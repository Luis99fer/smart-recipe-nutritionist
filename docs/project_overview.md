# Project Overview

## Project Title

**Smart Recipe Nutritionist**

## Summary

Smart Recipe Nutritionist is a Python command-line application that helps users evaluate ingredient combinations, explore nutrition facts, find similar recipes, and generate simple daily menus.

The project combines machine learning, recipe similarity search, nutrition lookup, and command-line interaction in a structured Python application.

This project was originally developed as part of a School 21 Russia programming assignment and later reorganized as a professional portfolio project.

## Main Idea

The user provides a list of ingredients, for example:

```text
chicken, tomato, garlic
```

The application then returns:

```text
1. A machine learning forecast for the ingredient combination
2. Nutrition facts for the provided ingredients
3. Top-3 similar recipes
```

The app can also generate a daily menu with:

```text
BREAKFAST
LUNCH
DINNER
```

## Core Features

### Ingredient Combination Forecast

The project uses a trained machine learning model to classify an ingredient combination into a quality label.

Possible labels include:

```text
bad
so-so
great
```

The model is loaded from:

```text
models/best_rating_label_model.joblib
```

The feature column order is loaded from:

```text
models/feature_columns.joblib
```

### Nutrition Lookup

The application retrieves nutrition facts from a local processed CSV file:

```text
data/ingredient_nutrition_daily_values.csv
```

Nutrition values are represented as percentages of recommended daily values.

The app can optionally use the USDA FoodData Central API as a fallback when an ingredient is not found locally. The API key is not hardcoded and should be provided through an environment variable.

### Similar Recipe Recommendation

The application recommends similar recipes using cosine similarity between:

```text
user-provided ingredients
```

and

```text
binary ingredient vectors from processed recipe data
```

The processed recipe data is stored in:

```text
data/similar_recipes.csv
```

### Daily Menu Generation

The application can generate a simple daily menu with:

```text
BREAKFAST
LUNCH
DINNER
```

The menu generator selects recipes based on:

- inferred meal type;
- recipe rating;
- available nutrition facts;
- a simple nutrition-based scoring function.

## Project Structure

```text
smart-recipe-nutritionist/
│
├── README.md
├── .gitignore
├── requirements.txt
├── LICENSE
│
├── src/
│   ├── nutritionist.py
│   └── recipes.py
│
├── notebooks/
│   └── recipes.ipynb
│
├── data/
│   ├── README.md
│   ├── ingredient_nutrition_daily_values.csv
│   └── similar_recipes.csv
│
├── models/
│   ├── README.md
│   ├── best_rating_label_model.joblib
│   └── feature_columns.joblib
│
├── docs/
│   ├── project_overview.md
│   ├── model_pipeline.md
│   └── usage_guide.md
│
├── reports/
│   └── analysis_summary.md
│
└── assets/
    ├── project_banner.png
    ├── pipeline_diagram.png
    └── app_architecture.png
```

## Main Python Components

The core application logic is implemented in:

```text
src/recipes.py
```

The command-line entry point is:

```text
src/nutritionist.py
```

## Main Classes

### RecipesData

Loads recipe datasets and detects binary ingredient columns.

### NutritionLookup

Retrieves nutrition facts from a local CSV file or optionally from the USDA API.

### SimilarRecipesEngine

Finds similar recipes using cosine similarity.

### RatingForecaster

Loads the trained machine learning model and predicts the quality label of an ingredient combination.

### DailyMenuGenerator

Generates a breakfast, lunch, and dinner menu based on recipe ratings and nutrition facts.

### NutritionistApp

Combines all components into a single high-level application interface used by the CLI.

## Example CLI Usage

Ingredient forecast and recommendations:

```bash
python src/nutritionist.py chicken, tomato, garlic
```

Daily menu generation:

```bash
python src/nutritionist.py --menu
```

## Technical Approach

The project follows a modular design:

```text
Input ingredients
        ↓
Feature vectorization
        ↓
ML rating forecast
        ↓
Nutrition lookup
        ↓
Similar recipe search
        ↓
Formatted CLI output
```

The app is designed to be runnable locally with processed data and model artifacts included in the repository.

## Skills Demonstrated

This project demonstrates:

- Python programming;
- command-line application development;
- machine learning model inference;
- scikit-learn model loading;
- joblib model persistence;
- pandas-based data processing;
- cosine similarity search;
- API integration;
- environment variable usage;
- data preprocessing;
- project documentation;
- portfolio-ready repository organization.

## Portfolio Value

This project is valuable for a GitHub portfolio because it is not only an analysis notebook. It is a working command-line application.

It shows the ability to:

- build a usable Python app;
- structure code into reusable classes;
- load trained ML artifacts;
- process real data;
- design user-facing output;
- document setup and usage clearly.

## Conclusion

Smart Recipe Nutritionist is a practical Python application that combines machine learning, recipe data, nutrition lookup, and recommendation logic.

It demonstrates strong applied Python skills and is suitable for a professional portfolio focused on machine learning, data analysis, and software development.