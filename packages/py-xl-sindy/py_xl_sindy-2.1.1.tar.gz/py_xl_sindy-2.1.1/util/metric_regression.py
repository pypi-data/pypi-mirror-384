"""
This script compute the linear regression between metric and solution
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

df = pd.read_pickle("experiment_database.pkl")

print("column name :", df.columns)


print("experiment name :", df["input_experiment_folder"].unique())

df = df[df["optimization_function"] == "hard_threshold_sparse_regression"]
# df = df[df["optimization_function"] == "lasso_regression"]
# df = df[df["input_experiment_folder"] == "cart_pole_double"]
df = df[df["input_experiment_folder"] == "cart_pole"]
# df = df[df["input_experiment_folder"] == "double_pendulum_pm"]

# Select all columns that start with "metric"
metric_columns = [col for col in df.columns if col.startswith("metric")]

metric_columns += ["RMSE_acceleration"]

# metric_columns = [metric_columns[3],metric_columns[4]]
# metric_columns = [metric_columns[-1]]
metric_columns = [metric_columns[0], metric_columns[-1]]

# Ensure there are metric columns
if not metric_columns:
    print("No metric columns found.")
else:
    # Define X (independent variables) and y (dependent variable)
    X = df[metric_columns]
    y = df["RMSE_model"]
    # y = np.log(df["RMSE_model"])

    data = pd.concat([X, y], axis=1).dropna()

    # Updated X and y without NaN values
    X = data[metric_columns]

    y = data["RMSE_model"]

    # Initialize and fit the linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict values
    y_pred = model.predict(X)

    # Get R² score (quality of regression)
    r2 = r2_score(y, y_pred)

    # Print coefficients and quality of regression
    print("Linear Regression Results:")
    print("---------------------------")
    print("Intercept:", model.intercept_)
    print("\nCoefficients:")
    for col, coef in zip(metric_columns, model.coef_):
        print(f"{col}: {coef}")

    print("\nQuality of Regression (R² score):", r2)

    # Compute and display coefficient importance
    # Here, importance is defined as |coefficient| * standard deviation of the feature
    print("\nCoefficient Importance (|Coefficient| * Feature Std):")

    abs_sum = np.sum(np.abs(model.coef_) * X[metric_columns].std())

    for col, coef in zip(metric_columns, model.coef_):
        importance = np.abs(coef) * X[col].std() / abs_sum * 100
        print(f"{col}: {importance:.4f}")
