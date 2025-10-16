"""
This script create or update the panda database from all the experiment.
Create one record by result section in json file.
"""

import glob
import json
import pandas as pd


def convert_value(value):
    """Converts numeric strings to numbers, and lists of numeric strings to lists of numbers."""
    if isinstance(value, str):
        try:
            # Convert string to float (or int if possible)
            num = float(value)
            return int(num) if num.is_integer() else num
        except ValueError:
            return value  # Return as string if conversion fails

    if isinstance(value, list):
        # Recursively process each element of the list
        return [convert_value(v) for v in value]

    return value  # Return as is if it's not a string or list


def flatten_common(data, parent_key=""):
    """
    Recursively flattens a dictionary.
    All keys will be concatenated with underscores.
    """
    items = {}
    for key, value in data.items():
        new_key = f"{parent_key}{key}_" if parent_key else f"{key}_"
        if isinstance(value, dict):
            items.update(flatten_common(value, new_key))
        else:
            items[new_key[:-1]] = convert_value(value)  # remove trailing underscore
    return items


def flatten_result_section(section):
    """
    Flattens a result section without prefixing keys with 'result'.
    """
    items = {}

    def _flatten(x, prefix=""):
        if isinstance(x, dict):
            for k, v in x.items():
                _flatten(v, prefix + k + "_")
        else:
            items[prefix[:-1]] = convert_value(x)  # remove trailing underscore

    _flatten(section)
    return items


def flatten_json_with_results(nested_json):
    """
    Separates common parts and result sections.
    For each key starting with 'result', create a record that merges
    the common flattened data with the flattened result section.
    If no result section exists, just return the common parts.
    """
    common_data = {}
    result_records = []

    # Separate common parts and result sections
    for key, value in nested_json.items():
        if key.startswith("result"):
            # Process this result section and flatten without prefixing "result"
            flat_result = flatten_result_section(value)
            result_records.append(flat_result)
        else:
            # Flatten common sections normally (with keys concatenated as parent_child)
            common_data.update(flatten_common({key: value}))

    # If no result sections are present, return the common data as one record
    if not result_records:
        return [common_data]

    # Otherwise, merge the common data into each result record
    merged_records = []
    for record in result_records:
        merged = {**common_data, **record}
        merged_records.append(merged)
    return merged_records


# Process each JSON file in the "result" folder
all_records = []
for json_file in glob.glob("result/*.json"):
    with open(json_file, "r") as f:
        json_data = json.load(f)
        # flatten_json_with_results returns a list of records
        records = flatten_json_with_results(json_data)
        for i in range(len(records)):
            records[i]["filename"] = json_file
        all_records.extend(records)

# Create a DataFrame from the records
df = pd.DataFrame(all_records)
print(df.columns)

# Save the DataFrame exactly:
df.to_pickle("experiment_database.pkl")
