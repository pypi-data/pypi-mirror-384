import pathlib
from importlib.resources import files

import pandas as pd
from SALib.sample import saltelli
import numpy as np

from . import data


class Dataset:
    def __init__(self, technologies: pd.DataFrame, demands: pd.DataFrame, resources: pd.DataFrame):
        self.technologies = technologies
        self.demands = demands
        self.resources = resources

    def use_only_technologies(self, to_use: list[str]):
        """
        Keep only the `to_use` in all the dataframes
        """
        self.technologies = self.technologies.loc[self.technologies['name'].isin(to_use)]
        self.demands = self.demands.loc[self.demands['name'].isin(to_use)]
        self.resources = self.resources.loc[self.resources['name'].isin(to_use)]

    def remove_technologies(self, to_remove: list[str]):
        """
        Remove the `to_remove` from all the dataframes
        """
        self.technologies = self.technologies.loc[~self.technologies['name'].isin(to_remove)]
        self.demands = self.demands.loc[~self.demands['name'].isin(to_remove)]
        self.resources = self.resources.loc[~self.resources['name'].isin(to_remove)]

    def add_technology(self, name: str, *, source: str = None, **kwargs):
        """
        Read `name`d technology from `source` and add it to the dataframes
        """
        if source and kwargs:
            raise ValueError("Source and kwargs are mutually exclusive")
        if source is not None:
            pass
        else:
            technology = kwargs.copy()
            technology['name'] = name
            self.technologies = pd.concat([self.technologies, pd.DataFrame.from_dict(technology)], ignore_index=True)


def __from_data(path) -> pathlib.Path:
    return files(data).joinpath('datasets').joinpath(path)


quebec = Dataset(pd.read_csv(__from_data("infrastructure/quebec/2020/quebec_technologies.csv")),
                 pd.read_csv(__from_data("infrastructure/quebec/2020/quebec_demands.csv")),
                 pd.read_csv(__from_data("infrastructure/quebec/2020/quebec_resources.csv")))

quebec_td = Dataset(pd.read_csv(__from_data("infrastructure/quebec/td/quebec_td_technologies.csv")),
                    pd.read_csv(__from_data("infrastructure/quebec/td/quebec_td_demands.csv")),
                    pd.read_csv(__from_data("infrastructure/quebec/td/quebec_td_resources.csv")))

quebec_transition = Dataset(pd.read_csv(__from_data("infrastructure/quebec/transition/quebec_transition_technologies.csv")),
                            pd.read_csv(__from_data("infrastructure/quebec/transition/quebec_transition_demands.csv")),
                            pd.read_csv(__from_data("infrastructure/quebec/transition/quebec_transition_resources.csv")))

def gen_sobol_sequence(trajectories: int = 4, calc_second_order: bool = False, parameters: list[dict] = None):
    """
    Generates a Sobol sequence for sensitivity analysis based on the provided parameter specifications.

    Parameters:
    -----------
    trajectories : int, optional
        The number of trajectories (or samples) to generate for each parameter. This defines how many 
        sample points will be used in the Sobol sequence. Default is 4.
    
    calc_second_order : bool, optional
        Whether to calculate second-order effects in the Sobol sensitivity analysis. If set to True, 
        second-order interactions between parameters will be computed, which increases the number of samples. 
        Default is False.
    
    parameters : list[dict], optional
        A list of dictionaries, where each dictionary defines a parameter with the following keys:
        - 'name' : str - The name of the parameter.
        - 'lower_bound' : float - The lower bound of the parameter's range.
        - 'upper_bound' : float - The upper bound of the parameter's range.

    Returns:
    --------
    sampling : numpy.ndarray
        A 2D array where each row represents a sample in the Sobol sequence and each column corresponds to 
        a parameter. The number of samples depends on the number of trajectories and whether second-order 
        effects are considered.
    
    problem : dict
        A dictionary defining the Sobol problem structure, which includes:
        - 'num_vars': The number of variables (parameters).
        - 'names': A list of parameter names.
        - 'bounds': A list of the bounds for each parameter, where each bound is a two-element list [lower_bound, upper_bound].


    Example:
    --------
    To generate a Sobol sequence for two parameters, 'alpha' and 'beta', with different bounds and 
    four trajectories:

    ```
    parameters = [
        {'name': 'PV_LV', 'lower_bound': 0, 'upper_bound': 50},
        {'name': 'WIND', 'lower_bound': 0, 'upper_bound': 20},
        {'name': 'CCGT', 'lower_bound': 0, 'upper_bound': 10}
        ]

    sampling, problem = gen_sobol_sequence(trajectories=4, calc_second_order=False, parameters=parameters)
    ```

    """

    num_vars = len(parameters)

    # Extract the names and bounds from the parameters
    names = [param['name'] for param in parameters]
    bounds = [[param['lower_bound'], param['upper_bound']] for param in parameters]

    # Create the problem dictionary
    problem = {
        'num_vars': num_vars,
        'names': names,
        'bounds': bounds
    }

    sampling = saltelli.sample(problem, trajectories, calc_second_order=calc_second_order)  

    return sampling, problem


def parametrize_params(params: list[dict], n_steps: int):
    """
    Creates a parametrized dataframe by generating sequences of values between a minimum and maximum value
    for multiple parameters, and adds optional index information for each parameter.

    Parameters:
    -----------
    params : list[dict]
        A list of dictionaries, where each dictionary defines a parameter with the following keys:
        - 'param': str - The name of the parameter.
        - 'min_val': float - The minimum value for the sequence.
        - 'max_val': float - The maximum value for the sequence.
        - 'index0', 'index1', 'index2', 'index3': Optional values to provide additional information for the parameter.
    
    n_steps : int
        The number of steps (or increments) for generating the sequence of values between `min_val` and `max_val`.
    
    Returns:
    --------
    data_frame : pandas.DataFrame
        A dataframe with rows for each parameter and its associated index columns, along with the generated
        sequence of values as additional columns.
    
    Example:
    --------
    To generate a dataframe for multiple parameters:

    ```
    params = [
        {'param': 'alpha', 'min_val': 0, 'max_val': 100, 'index0': 'group1', 'index1': 'typeA'},
        {'param': 'beta', 'min_val': 50, 'max_val': 150, 'index0': 'group2', 'index1': 'typeB'}
    ]
    
    df = parametrize_params(params, 5)
    print(df)
    ```

    This will produce:
    ```
       param  index0  index1 index2 index3  value1  value2  value3  value4  value5
    0  alpha  group1  typeA   None   None     0.0    25.0    50.0    75.0   100.0
    1   beta  group2  typeB   None   None    50.0    75.0   100.0   125.0   150.0
    ```

    """
    
    # Initialize a list to store all rows of data
    rows = []
    
    # Iterate over each parameter dictionary
    for param in params:
        # Extract the values from the parameter dictionary
        parameter = param.get('param')
        min_val = param.get('min_val')
        max_val = param.get('max_val')
        index0 = param.get('index0', None)
        index1 = param.get('index1', None)
        index2 = param.get('index2', None)
        index3 = param.get('index3', None)
        
        # Generate the sequence of values from min_val to max_val with n_steps
        seq_values = np.linspace(min_val, max_val, n_steps)
        
        # Create column names for the generated values (e.g., 'value1', 'value2', ..., 'valueN')
        col_names = [f"value{i+1}" for i in range(n_steps)]
        
        # Create a row dictionary for the current parameter with indexes and sequence values
        row = {
            'param': parameter,
            'index0': index0,
            'index1': index1,
            'index2': index2,
            'index3': index3
        }
        
        # Add the sequence values to the row
        row.update({col_name: val for col_name, val in zip(col_names, seq_values)})
        
        # Append the row to the list of rows
        rows.append(row)
    
    # Create a dataframe from the list of rows
    data_frame = pd.DataFrame(rows)
    
    return data_frame
