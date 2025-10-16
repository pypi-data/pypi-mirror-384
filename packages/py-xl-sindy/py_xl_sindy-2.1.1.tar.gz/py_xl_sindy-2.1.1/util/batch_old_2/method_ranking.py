import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors


# Helper function to darken a color by a given factor.
# factor should be between 0 and 1, where 1 returns the original color.
def darken_color(color, factor):
    rgb = mcolors.to_rgb(color)
    return tuple(c * factor for c in rgb)


# Load the DataFrame
df = pd.read_pickle("experiment_database.pkl")
print("column names:", df.columns)

# Step 1: Define the experiment ordering.
# We filter to noise_level 0 and the base sub-experiment where:
# optimization_function is 'hard_threshold_sparse_regression' and algoritm is 'xlsindy'.
df_noise0 = df[df["noise_level"] == 0.0]
mask_main = (
    df_noise0["optimization_function"] == "hard_threshold_sparse_regression"
) & (df_noise0["algoritm"] == "xlsindy")
df_main = df_noise0[mask_main].copy()
df_main = df_main.sort_values("RMSE_validation")

# We assume each experiment is uniquely identified by a 'filename' column.
exp_order = df_main["filename"].unique()
exp_to_x = {exp: idx for idx, exp in enumerate(exp_order)}

# Step 2: Set up a base color for each (algoritm, optimization_function) pair.
unique_pairs = df[["algoritm", "optimization_function"]].drop_duplicates()
base_colors = {}
cmap = plt.cm.get_cmap("tab10")
for i, row in enumerate(unique_pairs.itertuples(index=False)):
    pair = (row.algoritm, row.optimization_function)
    base_colors[pair] = cmap(i % 10)  # cycle if more than 10 pairs

# Determine the maximum noise level in the dataset (for scaling the darkening)
max_noise = df["noise_level"].max()

# Step 3: Group by (algoritm, optimization_function, noise_level) and plot.
plt.figure(figsize=(10, 6))
groups = df.groupby(["algoritm", "optimization_function", "noise_level"])
for (alg, opt_func, noise), group in groups:
    group = group.copy()
    # Use the experiment ordering defined above. Drop any experiments not present in exp_to_x.
    group["x_coord"] = group["filename"].map(exp_to_x)
    group = group.dropna(subset=["x_coord"])
    if group.empty:
        continue
    group = group.sort_values("x_coord")

    # Get the base color for this (alg, opt_func) pair.
    base_color = base_colors.get((alg, opt_func), "black")

    if noise == 0.0:
        color = base_color
        linestyle = "-"
        linewidth = 2
    else:
        # Compute a darkening factor: noise 0 gives factor 1 and max_noise gives factor 0.5.
        factor = 1 - (noise / max_noise * 0.5)
        color = darken_color(base_color, factor)
        linestyle = "--"
        linewidth = 1

    label = f"{alg} - {opt_func} (noise={noise})"
    plt.plot(
        group["x_coord"],
        group["RMSE_validation"],
        label=label,
        color=color,
        linestyle=linestyle,
        marker="o",
    )

plt.xlabel(
    "Experiment (ordered by RMSE_validation from base: hard_threshold_sparse_regression, xlsindy, noise=0)"
)
plt.ylabel("RMSE_validation")
plt.yscale("log")
plt.title("RMSE Validation across Experiments for various noise levels")
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.show()
