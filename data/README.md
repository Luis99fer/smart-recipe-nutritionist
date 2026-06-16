# Data

This directory stores the data files required to run Smart Recipe Nutritionist locally.

The project uses processed recipe data, nutrition facts, and optional raw recipe data used during experimentation.

## Required Files for the App

To run the command-line application, the following files are required:

```text
data/
├── ingredient_nutrition_daily_values.csv
└── similar_recipes.csv
```

These files are included in the GitHub repository because they are required for the final application to work.

## Optional Local File

The following file may be used for notebook experimentation or data preparation:

```text
data/
└── epi_r.csv
```

This file is not included in GitHub.

## File Descriptions

| File | Description | Included in GitHub |
|---|---|---|
| `ingredient_nutrition_daily_values.csv` | Processed nutrition facts for ingredients, expressed as percentages of daily values. | Yes |
| `similar_recipes.csv` | Processed recipe data used for similar recipe recommendations and daily menu generation. | Yes |
| `epi_r.csv` | Raw Epicurious-style recipe dataset used during development and experimentation. | No |

## Why the Processed Files Are Included

The files `ingredient_nutrition_daily_values.csv` and `similar_recipes.csv` are included because they are required by the command-line app.

Without these files, the app cannot:

- retrieve local nutrition facts;
- recommend similar recipes;
- generate daily menus;
- run reproducibly without depending fully on external APIs.

## Why the Raw Dataset Is Not Included

The raw dataset file `epi_r.csv` is not committed to this repository because:

- it is a raw external dataset;
- it may be large;
- it is mainly used for experimentation and notebook development;
- it is not required for the final CLI application;
- the repository should remain lightweight.

The `.gitignore` file excludes:

```text
data/epi_r.csv
```

## Expected Data Structure

After setting up the project locally, the `data/` directory should look like this:

```text
data/
├── README.md
├── ingredient_nutrition_daily_values.csv
└── similar_recipes.csv
```

If you want to reproduce the exploratory workflow from the notebook, you may also place the raw dataset here:

```text
data/
└── epi_r.csv
```

## Nutrition Data

The file `ingredient_nutrition_daily_values.csv` contains ingredient-level nutrition information.

The values are represented as percentages of recommended daily values.

Example columns may include:

```text
ingredient
ingredient_norm
protein
total carbohydrate
total fat
saturated fat
cholesterol
sodium
fiber
sugars
calcium
iron
potassium
vitamin d
magnesium
zinc
```

The application first checks this local file before attempting any API fallback.

## USDA API Fallback

The project can optionally use the USDA FoodData Central API to fetch nutrition facts for ingredients not found in the local CSV.

The API key should not be hardcoded in the source code.

Use an environment variable instead.

Windows PowerShell:

```powershell
$env:USDA_API_KEY="your_api_key_here"
```

macOS/Linux:

```bash
export USDA_API_KEY="your_api_key_here"
```

If no API key is provided, the app will still work with the local nutrition CSV.

## Similar Recipes Data

The file `similar_recipes.csv` is used by the recommendation engine.

It should contain:

- recipe titles;
- recipe ratings;
- recipe URLs;
- binary ingredient columns.

The recommendation system uses cosine similarity between the user-provided ingredients and recipe ingredient vectors.

## Notes

This repository focuses on the final application and its reproducible usage.

Raw data, generated datasets, credentials, and large files should remain outside Git unless they are small, processed, and required to run the app.