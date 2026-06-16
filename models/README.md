# Models

This directory stores trained model artifacts required by Smart Recipe Nutritionist.

## Required Files

To run the command-line application locally, the following model files are required:

```text
models/
├── best_rating_label_model.joblib
└── feature_columns.joblib
```

These files are included in the GitHub repository because they are necessary for the final app to work.

## File Descriptions

| File | Description | Included in GitHub |
|---|---|---|
| `best_rating_label_model.joblib` | Trained machine learning model used to predict the quality label of an ingredient combination. | Yes |
| `feature_columns.joblib` | List of feature columns used during model training and prediction. | Yes |

## Why Model Files Are Included

The two `.joblib` files are included because they are required to run the command-line application.

Without these files, the app cannot predict whether an ingredient combination is likely to be:

```text
bad
so-so
great
```

The raw training dataset is not included, but the final trained model artifacts are provided to make the project runnable and reproducible from the user perspective.

## How the Model Is Used

The CLI application loads the model through the `RatingForecaster` class.

The model receives a binary feature vector representing the ingredients provided by the user.

Example input:

```text
chicken, tomato, garlic
```

The application converts the ingredients into a one-row feature matrix using the saved feature column order from:

```text
feature_columns.joblib
```

Then it predicts one of the rating labels.

## Expected Local Structure

Before running the app, the `models/` directory should look like this:

```text
models/
├── README.md
├── best_rating_label_model.joblib
└── feature_columns.joblib
```

## Example Usage

From the project root:

```bash
python src/nutritionist.py chicken, tomato, garlic
```

The application will load:

```text
models/best_rating_label_model.joblib
models/feature_columns.joblib
```

and return a forecast for the ingredient combination.

## Reproducibility Notes

The notebook in the `notebooks/` directory documents the experimental workflow used during development.

A future version of this repository may include a dedicated training script to reproduce the model artifacts from the raw recipe dataset.

## Security Note

Do not commit credentials, private API keys, `.env` files, or local secrets to GitHub.

USDA API access, if used, should be configured through an environment variable:

```bash
USDA_API_KEY=your_api_key_here
```