import os
import glob
import numpy as np
import pandas as pd

# Directories and file pattern
filing_percentage = 0.5
result_dir = "result"

pattern = os.path.join(result_dir, "*__*.npz")
file_list = glob.glob(pattern)

# This list will hold one dictionary per sample
samples = []

# Create a reproducible random generator
rng = np.random.default_rng(seed=42)

# Loop over each file found by glob
for file_path in file_list:
    # Extract system name from the filename (everything before '__')
    base_name = os.path.basename(file_path).split("__")[0]

    # Load the experiment data
    sim_data = np.load(file_path)
    time_data = sim_data["array1"]
    qpos_data = sim_data["array2"]
    qvel_data = sim_data["array3"]
    qacc_data = sim_data["array4"]
    force_data = sim_data["array5"]

    # Determine sample size (ensure at least one sample is taken)
    n_samples = time_data.shape[0]
    sample_size = max(1, int(np.ceil(filing_percentage * n_samples)))

    # Randomly choose indices without replacement
    indices = rng.choice(n_samples, size=sample_size, replace=False)

    # For each selected index, add a row to our list with provenance info
    for i in indices:
        samples.append(
            {
                "system": base_name,
                "filename": os.path.basename(file_path),
                "time": time_data[i],
                "qpos": qpos_data[i],
                "qvel": qvel_data[i],
                "qacc": qacc_data[i],
                "force": force_data[i],
            }
        )

# Create a DataFrame from the list of sample dictionaries
df = pd.DataFrame(samples)
print("Created DataFrame with {} samples.".format(len(df)))

df.to_pickle("validation_database.pkl")
