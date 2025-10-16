import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load your DataFrame
df = pd.read_pickle("experiment_database.pkl")
print("column names:", df.columns)

# Optionally normalize a metric column
df["metric_exploration_volumes"] = np.log1p(df["metric_exploration_volumes"])

# Separate data based on RMSE_model status
df_nan = df[df["RMSE_model"].isna()]
df_non = df[df["RMSE_model"].notna()]

# List of metric columns (we pick two specific ones)
metric_cols = [col for col in df.columns if col.startswith("metric")]
metric_cols = [metric_cols[2], metric_cols[4]]

# Get unique noise values (using the full df to be safe)
noise_values = sorted(df["noise_level"].unique())

# Get unique (optimization_function, input_experiment_folder) pairs
pairs = (
    df[["optimization_function", "input_experiment_folder"]]
    .drop_duplicates()
    .sort_values(by=["optimization_function", "input_experiment_folder"])
)
pairs_list = pairs.values.tolist()
print("Pairs:", pairs_list, "Noise levels:", noise_values)

# Define grid dimensions:
n_rows = len(pairs_list)
n_noise = len(noise_values)
n_metrics = len(metric_cols)
total_cols = n_noise * n_metrics  # Each noise gets one subplot per metric

# Use a reduced figure size while maintaining text legibility:
fig, axes = plt.subplots(
    n_rows, total_cols, figsize=(2.5 * total_cols, 2.5 * n_rows), sharey=False
)

# Ensure axes is 2D even if one row or one column
if n_rows == 1:
    axes = axes.reshape(1, -1)
if total_cols == 1:
    axes = axes.reshape(-1, 1)

# Loop over each unique pair (row), each noise value, and each metric
for row_idx, (func, folder) in enumerate(pairs_list):
    for noise_idx, noise in enumerate(noise_values):
        for metric_idx, metric in enumerate(metric_cols):
            col_idx = noise_idx * n_metrics + metric_idx
            ax = axes[row_idx, col_idx]

            # Filter data for current combination in each subset
            subset_nan = df_nan[
                (df_nan["optimization_function"] == func)
                & (df_nan["input_experiment_folder"] == folder)
                & (df_nan["noise_level"] == noise)
            ]
            subset_non = df_non[
                (df_non["optimization_function"] == func)
                & (df_non["input_experiment_folder"] == folder)
                & (df_non["noise_level"] == noise)
            ]
            subset_low = df_non[
                (df_non["optimization_function"] == func)
                & (df_non["input_experiment_folder"] == folder)
                & (df_non["noise_level"] == noise)
                & (df_non["RMSE_model"] < 2)
            ]

            # Get the metric data for each category
            data_nan = subset_nan[metric].dropna()
            data_non = subset_non[metric].dropna()
            data_low = subset_low[metric].dropna()

            # Draw three boxplots side-by-side:
            bp = ax.boxplot(
                [data_nan, data_non, data_low],
                positions=[1, 2, 3],
                widths=0.6,
                patch_artist=True,
                showfliers=False,
            )

            # Assign colors for clarity: blue for NaN, green for Non-NaN, and coral for RMSE_model<2
            colors = ["lightblue", "lightgreen", "lightcoral"]
            for patch, color in zip(bp["boxes"], colors):
                patch.set_facecolor(color)

            # Update x-tick labels with the counts for each category
            ax.set_xticks([1, 2, 3])
            ax.set_xticklabels(
                [
                    f"NaN (n={len(data_nan)})",
                    f"Non-NaN (n={len(data_non)})",
                    f"RMSE<2 (n={len(data_low)})",
                ],
                fontsize=8,
            )

            # Annotate top row with noise and metric info
            if row_idx == 0:
                if metric_idx == 0:
                    ax.set_title(f"Noise: {noise}", fontsize=10)
                ax.annotate(
                    metric,
                    xy=(0.5, 1.05),
                    xycoords="axes fraction",
                    ha="center",
                    fontsize=9,
                )

            # Label the leftmost subplot in each row with function and folder info
            if noise_idx == 0 and metric_idx == 0:
                ax.set_ylabel(f"Func: {func}\nFolder: {folder}", fontsize=10)

plt.tight_layout()
plt.savefig("boxplots.png", dpi=300)
# plt.show()
