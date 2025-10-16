import pandas as pd
import matplotlib.pyplot as plt

# Load your dataset (replace 'data.csv' with your file, or use your DataFrame)
df = pd.read_pickle("experiment_database.pkl")

print("column name :", df.columns)


print("experiment name :", df["input_experiment_folder"].unique())

# df = df[df["optimization_function"] == "hard_threshold_sparse_regression"]
# df = df[df["optimization_function"] == "lasso_regression"]
# df = df[df["input_experiment_folder"] == "cart_pole_double"]
# df = df[df["input_experiment_folder"] == "cart_pole"]
# df = df[df["input_experiment_folder"] == "double_pendulum_pm"]

# Define the columns to plot (replace with your actual column names)
x_column = "RMSE_acceleration"
y_column = "RMSE_model"
# y_column = 'RMSE_model'

# Extract the values for plotting
x = df[x_column]
y = df[y_column]

# Create the scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(x, y, color="blue", alpha=0.6, edgecolor="k")
plt.xlabel(x_column)
plt.ylabel(y_column)
# plt.xscale("log")
plt.title(f"Scatter Plot: {y_column} vs {x_column}")
plt.grid(True)
plt.show()
