# Usage Guide

## Overview

This guide explains how to run Smart Recipe Nutritionist locally.

The project provides a command-line application that can:

- evaluate ingredient combinations;
- show nutrition facts;
- recommend similar recipes;
- generate a simple daily menu.

The main CLI entry point is:

```text
src/nutritionist.py
```

---

## 1. Project Setup

### Clone the Repository

```bash
git clone https://github.com/Luis99fer/smart-recipe-nutritionist.git
cd smart-recipe-nutritionist
```

### Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Required Files

To run the application, make sure these files exist:

```text
data/ingredient_nutrition_daily_values.csv
data/similar_recipes.csv
models/best_rating_label_model.joblib
models/feature_columns.joblib
```

Expected structure:

```text
smart-recipe-nutritionist/
├── data/
│   ├── ingredient_nutrition_daily_values.csv
│   └── similar_recipes.csv
├── models/
│   ├── best_rating_label_model.joblib
│   └── feature_columns.joblib
└── src/
    ├── nutritionist.py
    └── recipes.py
```

The raw dataset file `epi_r.csv` is not required to run the final app.

---

## 3. Running Ingredient Forecast Mode

Use this mode when you want to evaluate a list of ingredients.

Example:

```bash
python src/nutritionist.py chicken, tomato, garlic
```

You can also pass the ingredients as one quoted string:

```bash
python src/nutritionist.py "chicken, tomato, garlic"
```

Or as separate arguments:

```bash
python src/nutritionist.py chicken tomato garlic
```

---

## 4. Expected Ingredient Mode Output

The app returns three main sections:

```text
I. OUR FORECAST
II. NUTRITION FACTS
III. TOP-3 SIMILAR RECIPES
```

Example structure:

```text
I. OUR FORECAST
This looks like a great combination. We think it has a strong chance to become a tasty dish.

II. NUTRITION FACTS
Chicken
Protein - 62% of Daily Value
Sodium - 4% of Daily Value

Tomato
Vitamin C - 20% of Daily Value

III. TOP-3 SIMILAR RECIPES:
- Chicken Tomato Pasta, rating: 4.3, URL:
https://example.com/recipe
```

Actual output depends on the model, local nutrition data, and recipe dataset.

---

## 5. Running Daily Menu Mode

Use this mode to generate a simple daily menu.

```bash
python src/nutritionist.py --menu
```

The output contains:

```text
BREAKFAST
LUNCH
DINNER
```

Each section may include:

- recipe title;
- recipe rating;
- ingredients;
- nutrition facts;
- recipe URL.

---

## 6. USDA API Fallback

The app can optionally query the USDA FoodData Central API when a nutrition fact is not available in the local nutrition CSV.

The API key must be configured as an environment variable.

Windows PowerShell:

```powershell
$env:USDA_API_KEY="your_api_key_here"
```

macOS/Linux:

```bash
export USDA_API_KEY="your_api_key_here"
```

The key must not be hardcoded in the source code.

If no API key is configured, the app still works with the local file:

```text
data/ingredient_nutrition_daily_values.csv
```

---

## 7. Running the Notebook

The notebook is located in:

```text
notebooks/recipes.ipynb
```

It documents the exploratory and experimental workflow used during project development.

To open it:

```bash
jupyter notebook
```

Then navigate to:

```text
notebooks/recipes.ipynb
```

Depending on the notebook workflow, the optional raw dataset may be needed:

```text
data/epi_r.csv
```

This raw file is not required for normal CLI usage.

---

## 8. Checking Source Code Syntax

From the project root, run:

```bash
python -m py_compile src/recipes.py
python -m py_compile src/nutritionist.py
```

If no output appears, the files compiled successfully.

---

## 9. Common Errors

### Missing model file

Error example:

```text
Model file not found: models/best_rating_label_model.joblib
```

Fix:

```text
Place best_rating_label_model.joblib inside the models/ directory.
```

### Missing feature columns file

Error example:

```text
Feature columns file not found: models/feature_columns.joblib
```

Fix:

```text
Place feature_columns.joblib inside the models/ directory.
```

### Missing similar recipes file

Error example:

```text
Similar recipes file not found: data/similar_recipes.csv
```

Fix:

```text
Place similar_recipes.csv inside the data/ directory.
```

### No nutrition facts found

This can happen when an ingredient is not available in the local nutrition CSV and no USDA API key is configured.

Fix options:

```text
1. Use ingredients available in the local CSV.
2. Add nutrition data manually to ingredient_nutrition_daily_values.csv.
3. Configure USDA_API_KEY as an environment variable.
```

---

## 10. Example Commands

Ingredient forecast:

```bash
python src/nutritionist.py chicken, tomato, garlic
```

Ingredient forecast with quoted input:

```bash
python src/nutritionist.py "egg, cheese, tomato"
```

Daily menu:

```bash
python src/nutritionist.py --menu
```

Syntax check:

```bash
python -m py_compile src/recipes.py
python -m py_compile src/nutritionist.py
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 11. Notes

This application is intended for educational, portfolio, and experimentation purposes.

The nutrition output should not be interpreted as medical or dietary advice.

The recipe recommendations are based on similarity logic and available dataset features, not professional nutrition planning.