import os
import re
from typing import Callable

import pandas as pd
from amplpy import AMPL, Environment, ampl_notebook

from energyscope.datasets import Dataset
from energyscope.models import Model, monthly
from energyscope.result import parse_result, Result


class Energyscope:
    __es_model = None

    def __init__(self, model: Model = monthly, solver_options: dict = {'solver': 'gurobi'}, notebook: bool = False, license_uuid: str = None, modules: list = []):
        self.model = model
        self.solver_options = solver_options
        self.notebook = notebook
        self.license_uuid = license_uuid
        self.modules = modules

    @property
    def es_model(self) -> AMPL:
        if self.__es_model is None:
            if self.notebook:
                self.__es_model = ampl_notebook(license_uuid=self.license_uuid, modules=self.modules)
            else:
                try:
                    self.__es_model = AMPL(Environment(os.environ["AMPL_PATH"]))
                except SystemError:
                    # Try to create the object a second time to prevent errors when starting `ampl_lic`
                    self.__es_model = AMPL()
        return self.__es_model

    def _load_model_files(self, ds: Dataset = None):
        """
        Loads the model and data files into the given AMPL instance.

        Args:
            ds (Dataset, optional): An optional dataset to set specific data in the model.
        """
        # Read the model and data files
        for file in self.model.files:
            if file[0] == 'mod':
                self.es_model.read(file[1])
            elif file[0] == 'dat':
                self.es_model.read_data(file[1])

        # Set dataset-specific data if provided
        if ds:
            self.es_model.set_data(ds.technologies, set_name='technologies')
            self.es_model.set_data(ds.demands, set_name='demands')
            self.es_model.set_data(ds.resources, set_name='resources')

    def _initial_run(self, ds: Dataset = None) -> None:
        """
        Calls AMPL with `df` as .dat.
        """

        # Load the model files
        self._load_model_files(ds=ds)

        # Set solver options if provided
        for name, value in self.solver_options.items():
            self.es_model.set_option(name, value)

    def calc(self, ds: Dataset = None, parser: Callable[[AMPL], Result] = parse_result) -> Result:
        """
        Calls AMPL with `df` as .dat and returns the parsed result.
        """
        if self.es_model.getSets().__len__() == 0:  # Check if AMPL instance is empty
            self._initial_run(ds=ds)

        # Solve the model
        self.es_model.solve()
        if self.es_model.solve_result_num > 99:
            raise ValueError(f"No optimal solution found, see error: ", self.es_model.solve_result_num)

        return parser(self.es_model, id_run=0)

    def export_ampl(self, mod_filename: str = 'tutorial_output/AMPL_infrastructure_ch_2050.mod',
                    dat_filename: str = 'tutorial_output/AMPL_infrastructure_ch_2050.dat'):
        """
        Exports the model and data to .mod and .dat files for AMPL.

        Args:
            mod_filename (str): Path to the .mod file to export the model.
            dat_filename (str): Path to the .dat file to export the data.
        """
        # Reset the AMPL model
        self.es_model.reset()

        # Load the model and data files
        for file_type, file_path in self.model.files:
            if file_type == 'mod':
                self.es_model.read(file_path)
            elif file_type == 'dat':
                self.es_model.read_data(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        # Export the model and data
        self.es_model.export_model(mod_filename)
        self.es_model.export_data(dat_filename)

    def export_glpk(self, mod_filename: str, dat_filename: str):
        """
        Exports the model and data to files for GLPK.

        Args:
            mod_filename (str): Path to the .mod file to export the model.
            dat_filename (str): Path to the .dat file to export the data.
        """
        # Reset the AMPL model
        self.es_model.reset()

        # Read the model and data files
        for file_type, file_path in self.model.files:
            if file_type == 'mod':
                self.es_model.read(file_path)
            elif file_type == 'dat':
                self.es_model.read_data(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        # Export the base model and data files
        self.es_model.export_model(mod_filename)
        self.es_model.export_data(dat_filename)

        # Perform modifications for GLPK compatibility on the exported .mod file
        with open(mod_filename, 'r') as file:
            mod_content = file.read()

        # Extract content between ###model-start and ###model-end
        mod_match = re.search(r'###model-start(.*?)###model-end', mod_content, re.DOTALL)
        if not mod_match:
            raise ValueError("Markers '###model-start' and '###model-end' not found in the .mod file.")

        # Get the content between markers
        mod_between_content = mod_match.group(1)

        # Remove newlines followed by a space (\n\s)
        mod_between_content = re.sub(r'\n\s', '', mod_between_content)

        # Replace parameter and set definitions with ":=" definitions
        mod_between_content = re.sub(r'(param\s+\w+(\{[^}]+\})?\s*)=\s*(.*?);', r'\1:= \3;', mod_between_content)
        mod_between_content = re.sub(r'(set\s+\w+(\{[^}]+\})?\s*)=\s*(.*?);', r'\1:= \3;', mod_between_content)
        mod_between_content = re.sub(r' = ', r' := ', mod_between_content)

        # Reconstruct the .mod file content
        modified_mod_content = f'###model-start{mod_between_content}###model-end'

        # Write the modified content back to the .mod file
        with open(mod_filename, 'w') as file:
            file.write(modified_mod_content)
            file.write('\nsolve;')

        # Perform modifications for GLPK compatibility on the exported .dat file
        with open(dat_filename, 'r') as file:
            dat_content = file.read()

        # Extract content between ###data-start and ###data-end
        dat_match = re.search(r'###data-start(.*?)###data-end', dat_content, re.DOTALL)
        if not dat_match:
            raise ValueError("Markers '###data-start' and '###data-end' not found in the .dat file.")

        # Get the content between markers
        dat_between_content = dat_match.group(1)

        # Remove data; and model; instructions
        dat_between_content = re.sub(r'\ndata;', '', dat_between_content)
        dat_between_content = re.sub(r'\nmodel;', '', dat_between_content)

        # Reconstruct the .dat file content
        modified_dat_content = f'###data-start{dat_between_content}###data-end'

        # Write the modified content back to the .dat file
        with open(dat_filename, 'w') as file:
            file.write(modified_dat_content)

    def calc_sequence(self,
                      data: pd.DataFrame,
                      parser: Callable[[AMPL], Result] = parse_result,
                      ds: Dataset = None
                      ) -> list[Result]:
        """
        Calls AMPL `n` times, varying parameters based on `sequence` with `data` as .dat.

        Parameters:
        -----------
        data : pd.DataFrame
            A DataFrame containing the parameters and their associated values to be used
            in the AMPL model. The DataFrame should have the following structure:
                - 'param': (str) The name of the parameter to be varied in the AMPL model.
                - 'index0', 'index1', 'index2', 'index3': (str or None)
                  Index columns used to identify the parameter configuration
                  (optional, can be NA).
                - 'value1', 'value2', ..., 'valueN': (float or int)
                  One or more columns containing the numerical values for each model run.

            Rows with all index columns = NA will be treated as scalar parameters.
            Rows with at least one non-NA index column will be set via .set_values(...).

        parser : Callable[[AMPL], Result], optional
            A function that parses the AMPL model results. It should accept an AMPL object
            as input and return a Result object. Defaults to parse_result.

        ds : Dataset, optional
            An optional dataset object that can be used during the initial run of the model.

        Returns:
        --------
        list[Result]
            A list of results obtained after each model run. Each element in the list
            corresponds to the result of one iteration of the model.

        Raises:
        -------
        ValueError
            - If the DataFrame is missing required columns.
            - If 'param' has missing values.
            - If there are no 'value' columns.
        TypeError
            If any 'value' column is not numeric.
        """

        # Check for required columns
        required_columns = ['param', 'index0', 'index1', 'index2', 'index3']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(
                f"DataFrame is missing the following required columns: {missing_columns}"
            )

        # Identify all 'value' columns
        value_columns = [col for col in data.columns if col.startswith('value')]
        if not value_columns:
            raise ValueError(
                "No 'value' columns found in the DataFrame. At least one 'value' column is required."
            )

        # Check for missing values in 'param' but do NOT enforce that 'index0' must be non-NA
        if data['param'].isnull().any():
            raise ValueError(
                "Missing values found in the 'param' column."
            )

        # Ensure all 'value' columns have numeric data
        for col in value_columns:
            # Coerce the column to numeric, converting non-numeric values to NaN
            data[col] = pd.to_numeric(data[col], errors='coerce')
            # Check if the column is numeric after coercion
            if not pd.api.types.is_numeric_dtype(data[col]):
                raise TypeError(f"Column '{col}' should contain numeric data, but found non-numeric values.")
            # Optionally, check for NaN values introduced by coercion
            if data[col].isnull().any():
                raise ValueError(f"Column '{col}' contains non-numeric values that could not be converted.")
        

        # If AMPL has not been initialized, do so now
        if self.es_model.getSets().__len__() == 0:
            self._initial_run(ds=ds)

        # Map each unique 'param' to the AMPL parameter object
        unique_params = data['param'].unique()
        parameters = {param: self.es_model.get_parameter(param) for param in unique_params}

        # Gather the index columns for convenience
        data_index_columns = data.columns[data.columns.str.startswith('index')].to_list()

        # Container for merged results across runs
        results_n = {}

        # Loop over each 'value' column => each separate model run
        for j in range(len(value_columns)):
            col_name = value_columns[j]

            for row_idx, row in data.iterrows():
                param_name = row['param']
                param_val = row[col_name]

                # Extract only non-NA entries among index0..index3
                idx_data = {idx_col: row[idx_col]
                            for idx_col in data_index_columns
                            if pd.notnull(row[idx_col])}

                if len(idx_data) == 0:
                    # No valid index => treat as a scalar
                    parameters[param_name].set(param_val)
                else:
                    # At least one valid index => build a small DataFrame and set via set_values
                    row_slice = row[data_index_columns + [col_name]].dropna()
                    param_df = pd.DataFrame([row_slice.values], columns=row_slice.index)

                    # Identify which columns actually function as indices here
                    index_cols = [ic for ic in data_index_columns if ic in param_df.columns]
                    param_df.set_index(index_cols, inplace=True)

                    parameters[param_name].set_values(param_df)

            # Solve model after all parameters for this run have been updated
            self.es_model.solve()
            print(f"Run {j + 1} complete.")

            # Check solver status
            if self.es_model.solve_result_num > 99:
                print("No optimal solution found, solver status:", self.es_model.solve_result_num)

            # Parse this run's results
            results_current = parser(self.es_model, id_run=j + 1)

            # Merge with previous runs or store as first
            if j == 0:
                results_n = results_current
            else:
                # Merge new data into results_n
                for var_name in results_n.variables.keys():
                    results_n.variables[var_name] = pd.concat(
                        [results_n.variables[var_name], results_current.variables[var_name]]
                    )
                for par_name in results_n.parameters.keys():
                    results_n.parameters[par_name] = pd.concat(
                        [results_n.parameters[par_name], results_current.parameters[par_name]]
                    )
                for obj_name in results_n.objectives.keys():
                    results_n.objectives[obj_name] = pd.concat(
                        [results_n.objectives[obj_name], results_current.objectives[obj_name]]
                    )

        return results_n

    def add_technology(self, tech_parameters: dict, output_dir: str, tech_sets: dict = None):
        """
        Adds a new technology to the energy system model, assigns the technology to sets,
        and defines all parameters including layers_in_out for the technology.

        Parameters:
        -----------
        tech_parameters : dict
            Dictionary containing all technology parameters, including:
                - Name of the technology (required)
                - Optional parameters: If not provided, default values will be used.
                    - ref_size (default: 0.001)
                    - c_inv (default: 0.000001)
                    - c_maint (default: 0)
                    - lifetime (default: 20)
                    - f_max (default: 300000)
                    - f_min (default: 0)
                    - fmax_perc (default: 1)
                    - fmin_perc (default: 0)
                    - c_p_t (default: 1 for all periods)
                    - c_p (default: 1)
                    - gwp_constr (default: 0)
                    - trl (default: 9)
                    - layers_in_out (default: 0 for all layers like 'ELECTRICITY_MV', 'HEAT_LOW_T_DHN', 'COAL')

        output_dir : str
            Directory where the output `.dat` file will be saved.

        tech_sets : dict, optional
            A dictionary of sets that the technology belongs to, in the format:
                {
                    'TECHNOLOGIES_OF_END_USES_TYPE': ['ELECTRICITY_MV'],
                    'TECHNOLOGIES_OF_END_USES_TYPE': ['HEAT_LOW_T_DHN']
                }
            Default: {'INFRASTRUCTURE': True} when nothing is declared.

        Returns:
        --------
        None
        """
        try:
            tech_name = tech_parameters.get('name')
            if not tech_name:
                raise ValueError("Technology name is required in tech_parameters.")

            # Step 2: Assign default values to optional parameters if they are not provided
            default_params = {
                'ref_size': 0.001,
                'c_inv': 0.000001,
                'c_maint': 0,
                'lifetime': 20,
                'f_max': 300000,
                'f_min': 0,
                'fmax_perc': 1,
                'fmin_perc': 0,
                'c_p_t': {i: 1 for i in range(1, 13)},  # Default capacity factor for each month (1 for all)
                'c_p': 1,
                'gwp_constr': 0,
                'trl': 9,
                'layers_in_out': {
                    'ELECTRICITY_MV': 0,
                    'HEAT_LOW_T_DHN': 0,
                    'COAL': 0
                }
            }

            for attr in default_params.keys():
                if attr not in tech_parameters:
                    print(f"{attr} is not defined, default value: {default_params[attr]} will be used.")

            # Update default_params with any values provided in tech_parameters
            for param, default_value in default_params.items():
                tech_parameters[param] = tech_parameters.get(param, default_value)

            # Step 3: Validate all technology parameters
            required_params = [
                'ref_size', 'c_inv', 'c_maint', 'lifetime', 'f_max',
                'f_min', 'fmax_perc', 'fmin_perc',
                'c_p_t', 'c_p', 'gwp_constr', 'trl', 'layers_in_out'
            ]
            for param in required_params:
                if param not in tech_parameters:
                    raise ValueError(f"Missing required parameter: {param}")

            # Step 4: Create a .dat file for the technology, including layers_in_out
            output_file = os.path.join(output_dir, f"{tech_parameters['name']}.dat")

            with open(output_file, 'w') as f:
                tech_abbreviation = tech_parameters['name']
                f.write(f"### Technology: {tech_abbreviation}\n")

                # Add the technology to the relevant sets
                tech_sets = tech_sets or {'INFRASTRUCTURE': True}
                for set_type, set_values in tech_sets.items():
                    if isinstance(set_values, list):
                        for value in set_values:
                            f.write(
                                f"let {set_type}['{value}'] := {set_type}['{value}'] union '{{{tech_abbreviation}}}';\n")
                    else:
                        f.write(f"let {set_type} := {set_type} union {{'{tech_abbreviation}'}};\n")

                # Write layers_in_out
                for layer, value in tech_parameters['layers_in_out'].items():
                    f.write(f"let layers_in_out['{tech_abbreviation}','{layer}'] := {value}; #\n")

                # Write other parameters in the specified format
                f.write(f"let ref_size['{tech_abbreviation}'] := {tech_parameters['ref_size']} ; # [GW]\n")
                f.write(f"let c_inv['{tech_abbreviation}'] := {tech_parameters['c_inv']} ; #\n")
                f.write(f"let c_maint['{tech_abbreviation}'] := {tech_parameters['c_maint']} ; # [MCHF/GW/year]\n")
                f.write(f"let gwp_constr['{tech_abbreviation}'] := {tech_parameters['gwp_constr']} ; # ktCO2-eq./GW\n")
                f.write(f"let lifetime['{tech_abbreviation}'] := {tech_parameters['lifetime']} ; # year\n")
                f.write(f"let c_p['{tech_abbreviation}'] := {tech_parameters['c_p']} ; # -\n")
                f.write(f"let fmin_perc['{tech_abbreviation}'] := {tech_parameters['fmin_perc']} ; #\n")
                f.write(f"let fmax_perc['{tech_abbreviation}'] := {tech_parameters['fmax_perc']} ; #\n")
                f.write(f"let f_min['{tech_abbreviation}'] := {tech_parameters['f_min']} ; # [GW]\n")
                f.write(f"let f_max['{tech_abbreviation}'] := {tech_parameters['f_max']} ; # [GW]\n")

                # Write capacity factors for each period (c_p_t)
                for month, value in tech_parameters['c_p_t'].items():
                    f.write(f"let c_p_t['{tech_abbreviation}',{month}] := {value} ; #\n")

            # Step 5: Append the technology to the model's dataset (e.g., infrastructure)
            self.model.files.append(('dat', output_file))

            print(f"Technology '{tech_abbreviation}' successfully added and saved in {output_file}")

        except Exception as e:
            # Handle errors, print a message, and prevent further processing.
            print(f"Error while adding technology: {e}")
            return None
