import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors


# Helper function to darken a color by a given factor.
def darken_color(color, factor):
    rgb = mcolors.to_rgb(color)
    return tuple(c * factor for c in rgb)


# Load the DataFrame.
df = pd.read_pickle("experiment_database.pkl")

# Create a 'couple' column combining algoritm and optimization_function.
df["couple"] = (
    df["algoritm"]
    + " \n "
    + df["optimization_function"].apply(lambda x: " ".join(x.split("_")))
)

print("number of system : ", len(df["filename"].unique()))

# Get a sorted list of unique couples.
couples = sorted(df["couple"].unique())

# Assign a base color for each couple using the tab10 colormap.
cmap = plt.cm.get_cmap("tab10")
base_colors = {couple: cmap(i % 10) for i, couple in enumerate(couples)}

# Determine the maximum noise level (used to scale darkening).
max_noise = df["noise_level"].max()

# Define the three metrics.
metrics = ["RMSE_validation", "RMSE_acceleration", "RMSE_model", "RMSE_trajectory"]

# Set up three subplots that share the same x-axis.
fig, axs = plt.subplots(nrows=len(metrics), ncols=1, sharex=True, figsize=(14, 12))
plt.subplots_adjust(hspace=0.3)

width = 0.8  # width available for each couple group

# Loop over each metric and its corresponding subplot.
for ax, metric in zip(axs, metrics):
    # For each couple, plot a box for each noise level.

    tick_list = []
    tick_data = []

    for i, couple in enumerate(couples):
        df_couple = df[df["couple"] == couple]
        # Get unique noise levels for this couple, sorted in ascending order.
        noise_levels = sorted(df_couple["noise_level"].unique())
        n_levels = len(noise_levels)

        # Compute x positions for each noise level within the group.
        if n_levels == 1:
            pos_list = [i]
        else:
            pos_list = np.linspace(i - width / 2, i + width / 2, n_levels)

        tick_list += list(pos_list)

        for pos, noise, i in zip(pos_list, noise_levels, range(len(pos_list))):
            # Use all non-NaN values for the current metric.
            data = df_couple[df_couple["noise_level"] == noise][metric].dropna().values
            # Annotate with the count of data points.
            tick_data += [len(data)]
            if len(data) == 0:
                continue  # Skip if there are no valid points.

            # Determine the color: noise=0 uses the base color; higher noise gets a darker shade.
            base_color = base_colors[couple]
            if noise == 0:
                color = base_color
            else:
                factor = 1 - (
                    i / len(pos_list) * 0.5
                )  # noise 0 => factor 1; max_noise => factor ~0.5.
                color = darken_color(base_color, factor)

            # Plot the boxplot for this noise level.
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

        sec2 = ax.secondary_xaxis(location=0)
        sec2.set_xticks(tick_list, labels=[f"n={x}" for x in tick_data])
        sec2.tick_params("x", length=0)

    # ax.set_ylabel(metric)
    ax.set_title(" ".join(metric.split("_")))

    ax.grid(axis="y")

# Set the shared x-axis: one tick per couple.

axs[-1].set_xticks(range(len(couples)))
axs[-1].set_xticklabels(couples, rotation=0, ha="center")
axs[-1].tick_params("x", pad=20)

axs[-1].set_xlabel("Couple (algoritm - optimization_function)")

axs[-1].set_yscale("log")

plt.tight_layout(rect=[0, 0, 1, 0.95])

fig.savefig(f"poster_figure/metric_comparison.svg", format="svg")
plt.show()
