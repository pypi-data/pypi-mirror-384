# Note about the paper and data generation 

I needed to change the way I generated data for the second paper. Now I want to test the different mixed method strategies.

## Data generation pipeline : 

The pipeline is as follows:
- `batch_launch` : This script launches the data generation process.
- `batch_file_execute` | `align_data` : This script aligns the generated data, following the different algorithms.
- `batch_file_execute` | `validation_trajectory` : This script create validation trajectories from the aligned model. ( This is the best way to validate model or not)
- `create_panda_database` : This script creates a pandas database from the aligned data.

After when the database is generated, we can use the data to generate different graphs.

## Batch launch : 

I changed the `batch_launch` script in order to have the experiment that contain batch experiments. ( for mixed / implicit method )


## Article name and spirit 

### August 24

I thought about multiple stuff concerning the big title of the article... 

- Space transform : Use this word instead of paradigm