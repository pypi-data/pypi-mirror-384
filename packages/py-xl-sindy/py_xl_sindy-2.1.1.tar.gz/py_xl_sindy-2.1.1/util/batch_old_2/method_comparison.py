import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors


# Helper function to darken a color by a given factor.
# factor should be between 0 and 1 (1 returns the original color).
def darken_color(color, factor):
    rgb = mcolors.to_rgb(color)
    return tuple(c * factor for c in rgb)


# Load your DataFrame
df = pd.read_pickle("experiment_database.pkl")

# Filter: Only keep files that succeeded on every sub-experiment,
# i.e. for each file, every RMSE_validation is not NaN.
valid_files = df.groupby("filename")["RMSE_validation"].apply(lambda x: x.notna().all())
valid_files = valid_files[valid_files].index  # filenames where all are True
df = df[df["filename"].isin(valid_files)]

# Create a column that identifies the (algoritm, optimization_function) couple.
df["couple"] = df["algoritm"] + " - " + df["optimization_function"]

# Get a sorted list of unique couples (sorted alphabetically)
couples = sorted(df["couple"].unique())

# Set up a base color for each couple using the tab10 colormap.
cmap = plt.cm.get_cmap("tab10")
base_colors = {}
for i, couple in enumerate(couples):
    base_colors[couple] = cmap(i % 10)

# Determine the maximum noise level in the dataset (for scaling darkening)
max_noise = df["noise_level"].max()

# Prepare the plot.
fig, ax = plt.subplots(figsize=(12, 6))
width = 0.8  # width available for each couple group
legend_entries = {}

# For each couple, plot a box for each noise level.
for i, couple in enumerate(couples):
    # Filter data for this couple.
    df_couple = df[df["couple"] == couple]
    # Get unique noise levels for this couple (sorted in ascending order).
    noise_levels = sorted(df_couple["noise_level"].unique())
    n_levels = len(noise_levels)

    # Compute x positions within the group.
    if n_levels == 1:
        pos_list = [i]
    else:
        pos_list = np.linspace(i - width / 2, i + width / 2, n_levels)

    # Plot a box plot for each noise level.
    for pos, noise in zip(pos_list, noise_levels):
        # Select the RMSE_validation data for this noise level.
        data = df_couple[df_couple["noise_level"] == noise]["RMSE_validation"].values

        # Determine the color: noise==0 uses the base color, otherwise darken relative to max_noise.
        base_color = base_colors[couple]
        if noise == 0:
            color = base_color
        else:
            # Darkening factor: noise 0 gives factor 1; max_noise gives factor ~0.5.
            factor = 1 - (noise / max_noise * 0.5)
            color = darken_color(base_color, factor)

        # Create the boxplot for this noise level.
        bp = ax.boxplot(
            data,
            positions=[pos],
            widths=width / (n_levels + 1),
            patch_artist=True,
            showfliers=False,
        )
        for box in bp["boxes"]:
            box.set(facecolor=color, alpha=0.7)
        for whisker in bp["whiskers"]:
            whisker.set(color=color)
        for cap in bp["caps"]:
            cap.set(color=color)
        for median in bp["medians"]:
            median.set(color="black")

        # Build a legend entry (one per couple and noise level combination).
        label = f"{couple} (noise={noise})"
        if label not in legend_entries:
            legend_entries[label] = plt.Line2D(
                [],
                [],
                color=color,
                marker="s",
                linestyle="None",
                markersize=10,
                label=label,
            )

# Set x-axis: one tick per couple.
ax.set_xticks(range(len(couples)))
ax.set_xticklabels(couples, rotation=45, ha="right")
ax.set_ylabel("RMSE_validation")
ax.set_title(
    "Box Plot of RMSE_validation for each (algoritm, optimization_function) couple by noise level"
)
ax.legend(
    legend_entries.values(),
    legend_entries.keys(),
    bbox_to_anchor=(1.05, 1),
    loc="upper left",
)
plt.tight_layout()
plt.show()
