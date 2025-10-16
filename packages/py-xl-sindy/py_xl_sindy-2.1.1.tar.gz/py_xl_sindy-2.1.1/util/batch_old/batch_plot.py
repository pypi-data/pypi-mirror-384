import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Get list of all JSON files in the "result" folder
json_files = glob.glob("result/*.json")

# List to hold each JSON file's scalar data (one record per file)
records = []
# List to hold each file's solution_norm vector (as a NumPy array)
solution_norms = []

id = 0

ideal_solutions_norm = []

for filename in json_files:
    with open(filename, "r") as f:
        data = json.load(f)

    # Extract scalar values from the JSON. Many numeric values are stored as strings,
    # so we convert them as needed.
    experiment_folder = data["input"]["experiment_folder"]
    exploration_vol = float(data["result"]["exploration_volumes"])
    rmse_model = float(data["result"]["RMSE_model"])
    rmse_acceleration = float(data["result"]["RMSE_acceleration"])
    sparsity_diff = float(data["result"]["sparsity_difference"])
    sparsity_diff_perc = float(data["result"]["sparsity_difference_percentage"])
    max_time = float(data["input"]["max_time"])
    forces_period = float(data["input"]["forces_period"])
    forces_period_shift = float(data["input"]["forces_period_shift"])
    coordinate_number = int(data["environment"]["coordinate_number"])
    catalog_len = int(data["environment"]["catalog_len"])

    forces_input = data["input"]["forces_scale_vector"]
    forces_input = np.array(forces_input, dtype=float)

    max_forces = np.sum(forces_input)

    # Build a record (dictionary) of scalar inputs for this file
    record = {
        "filename": filename,
        "experiment_folder": experiment_folder,
        "exploration_volumes": exploration_vol,
        "RMSE_model": rmse_model,
        "RMSE_acceleration": rmse_acceleration,
        "sparsity_difference": sparsity_diff,
        "sparsity_difference_percentage": sparsity_diff_perc,
        "max_time": max_time,
        "forces_period": forces_period,
        "forces_period_shift": forces_period_shift,
        "coordinate_number": coordinate_number,
        "catalog_len": catalog_len,
        "id": id,
        "max_forces": max_forces,
    }
    records.append(record)
    id += 1

    # Convert the solution_norm_nn string (which looks like a NumPy array) to an actual array
    sol_norm_str = data["result"]["solution_norm_nn"]
    sol_norm_array = np.fromstring(sol_norm_str.strip("[]"), sep=" ")

    ideal_solutions_norm_str = data["result"]["ideal_solution_norm_nn"]
    ideal_solutions_norm_sarray = np.fromstring(
        ideal_solutions_norm_str.strip("[]"), sep=" "
    )

    solution_norms.append(
        sol_norm_array[ideal_solutions_norm_sarray != 0]
    )  # Keep only non null term
    ideal_solutions_norm.append(
        ideal_solutions_norm_sarray[ideal_solutions_norm_sarray != 0]
    )

# Create a pandas DataFrame from the records
df = pd.DataFrame(records)
# print("Scalar data from JSON files:")
# print(df)

exp_names = df["experiment_folder"].unique()
num_exp = len(exp_names)

# Generate a scatter plot using two of the scalar columns from the DataFrame
fig = plt.figure(figsize=(8, 6), dpi=100, constrained_layout=True)

gs = fig.add_gridspec(
    num_exp, 2, hspace=0.15, top=0.99, bottom=0.09, right=0.99, left=0.09
)


def make_ghost_ax(ax):

    # Hide ticks and tick labels
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Hide spines (the border lines around the plot)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # Hide grid
    ax.grid(False)

    # Hide the plot frame
    ax.set_frame_on(False)


ghost_axes = fig.add_subplot(gs[:num_exp, :])

make_ghost_ax(ghost_axes)


ghost_axes.set_ylabel("RMSE% model", labelpad=20)

# ghost_axes.set_title("Scatter Plot of Exploration Volumes vs RMSE_model")

for i in range(num_exp):

    ax = fig.add_subplot(gs[i, :])
    row_exp = df.loc[df["experiment_folder"] == exp_names[i]]

    # ax.scatter(row_exp["max_forces"], row_exp["RMSE_model"], marker='o', label=exp_names[i])
    ax.scatter(
        row_exp["exploration_volumes"],
        row_exp["RMSE_model"],
        marker="o",
        label=exp_names[i],
    )  # Normal exploration plot
    ax.set_xscale("log")

    # ax.set_yscale("log")

    ax.legend()
    ax.grid(True)

    spar_ax = ax.twinx()
    spar_ax.scatter(
        row_exp["exploration_volumes"],
        row_exp["sparsity_difference"],
        marker="o",
        color="r",
        label=exp_names[i],
    )  # Normal exploration plot

    ideal_solution = ideal_solutions_norm[row_exp["id"].iat[0]]

    # ax = fig.add_subplot(gs[i+num_exp,0])
    # ax.bar(np.arange(len(ideal_solution)), ideal_solution, width=1, label="True Model")


ghost_axes.set_xlabel("Exploration Volumes", labelpad=20)

plt.tight_layout()
plt.show()

# Optionally, if you want to combine the solution_norm vectors into a single NumPy array:
solution_norms_array = np.array(solution_norms)
print("Combined Solution Norms Array:")
print(solution_norms_array)
