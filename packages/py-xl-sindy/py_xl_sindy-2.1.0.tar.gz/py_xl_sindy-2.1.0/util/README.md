## Util folder

This folder contain all the script in order to generate experiment data, to compare result and to generate graph.

### Mujoco Simulation parameter

Everything linked with launching mujoco simulation is inside the folder `mujoco_align_data` each simulation data is composed of **two files** :
- `environment.xml` : the file containing the model parameter in *MJCD modeling language*.
- `xlsindy_gen.py` : a python file containing function making the bridge between the *mujoco simulation* and the *xlsindy framework* (mainly state space rotation/translation from mujoco to theorical system and *theorical model equations* in order to have **ground truth** data)

### Util script utilisation steps

*all the script use a **CLI** interface that accept `--help` in order to get complete information about each script*

To give a clearer view of the different util script, I will give the different step order to use the different script :

#### Data generation 

1. `batch_launch.py` : **Launch** a batch of mujoco simulation and store each experiment in a different file in `result` folder. `.json` file is created containing simulation data (seed,parameter,etc..) and a `.npz` file is created containing time-series data.
2. `create_validation_database.py` : **Create** a database containing random extract from each experiment. Used to generate *RMSE_validation*. Doesn't erase sample from the time-series, so we actually *train* on *validation data* but since *RMSE_validation* is not the most meaningfull way to measure success in this field it is not important.
3. `batch_file_execute.py` *script* `exploration_metric` : **Populate** the `.json` file with arbitrary decided *exploration metric* defined in `exploration_metrics.py`.
4. `batch_file_execute.py` *script* `align_data` : **Execute regression** for each result using a defined *regression algorithm*. Internally **append** each experiment `.json` file with *regression data*. Uses `align_data.py`.
5. `batch_file_execute.py` *script* `validation_trajectory` : **Populate** the `.json` file with the *real validation metric* **RMSE_trajectory** that measure the deviation of the retrieved model with the mujoco model over time. Can also be used to generate `trajectory_validation.svg` a graph that shows retrieved model against the ideal model on each *noise level* and *regression algorithm*. Uses `validation_trajectory.py`.
6. `create_panda_database.py` : **Create** a panda database file containing *all* the data coming from `.json` files. Used for rendering purpose afterward.

#### Figure / result generation

- `validation_trajectory.py` *parameter* `record` `plot`: **Generate** video record of a new *ideal validation trajectory* and plot the different **retrieved model deviation** with this new *ideal validation trajectory*
![validation trajectory exemple](/util/exemple_figures/trajectory_validation.svg)
- `method_comparison.py` (and `method_comparison_tiny.py`) : **Generate** a matrix plot that cross compare each method and noise level, *following* a choosen *metric*
![validation trajectory exemple](/util/exemple_figures/method_comparison_RMSE_trajectory.svg)
- `metric_comparison.py` : **Generate** a plot of each metric score depending on the method and noise level.
![validation trajectory exemple](/util/exemple_figures/metric_comparison.svg)