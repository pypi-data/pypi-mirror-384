import json
import glob
import numpy as np
import matplotlib.pyplot as plt

# Get list of all JSON files in the "result" folder
json_files = glob.glob("result/*.json")

# Lists to store extracted data
experiment_folders = []
exploration_volumes = []
rmse_accelerations = []
rmse_models = []
solution_norms = []  # will hold each solution norm as a NumPy array

# Loop over each JSON file and extract the desired information
for filename in json_files:
    with open(filename, "r") as f:
        data = json.load(f)

    # Extract experiment folder from the "input" section
    exp_folder = data["input"]["experiment_folder"]
    experiment_folders.append(exp_folder)

    # Extract exploration volume and RMSE_model from the "result" section
    # Convert them to floats
    exp_vol = float(data["result"]["exploration_volumes"])
    rmse = float(data["result"]["RMSE_model"])
    rmse_acceleration = float(data["result"]["RMSE_acceleration"])
    exploration_volumes.append(exp_vol)
    rmse_models.append(rmse)
    rmse_accelerations.append(rmse_acceleration)
    # Extract solution_norm_nn (a string) and convert it to a NumPy array.
    # The string looks like "[-0.01793783  0.00615766  0.1389602  ...]", so we remove the brackets and use fromstring.
    sol_norm_str = data["result"]["solution_norm_nn"]
    sol_norm_array = np.fromstring(sol_norm_str.strip("[]"), sep=" ")
    solution_norms.append(sol_norm_array)

# Create a scatter plot of exploration volumes vs RMSE_model
plt.figure(figsize=(8, 6))
plt.scatter(
    np.log10(exploration_volumes), np.log10(rmse_models), marker="o", color="blue"
)
plt.scatter(
    np.log10(exploration_volumes), np.log10(rmse_accelerations), marker="o", color="red"
)
plt.xlabel("Exploration Volumes")
plt.ylabel("RMSE_model")
plt.title("Scatter Plot of Exploration Volumes vs RMSE_model")
plt.grid(True)
plt.show()

# Optionally, combine all solution norms into a single NumPy array
# (this will work best if each solution norm has the same shape)
solution_norms_array = np.array(solution_norms)

# Print extracted experiment folders and the combined solution norm array
print("Extracted Experiment Folders:")
print(experiment_folders)
print("\nCombined Solution Norms Array:")
print(solution_norms_array)
