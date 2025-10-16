import json
import logging
import os
import shutil
from collections import OrderedDict, defaultdict
from pathlib import Path

import time
import pandas as pd

import milliman_sensi.syntax as syn
import milliman_sensi.utility as util

pd.options.mode.chained_assignment = None  # Used to suppress panda warning
SENSI_CONFIG_HEADER = ["Scenario", "Stress name", "Apply stress"]
DESCRIPTION_MAX_LENGTH = 500 # 500 characters

logger = logging.getLogger(__name__)


def setup_syntax_logger(handler, level=None):
    """Sets up the syntax logger

    Args:
        handler (StreamHandler): The handler to use for the syntax logger
        level (int, optional): The level to log at. Defaults to None.
    """
    syn.logger.addHandler(handler)

    # To prevent setting the logger level multiple times
    if level:
        syn.logger.setLevel(level)


# Custom Exception class for sensi validation and modification
class SensiIOError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)

    def __str__(self):
        return self.msg


def sensi_config_is_valid(sensi_config):
    """Checks if the sensi config is valid

    Args:
        sensi_config (dataframe): The sensi config as a dataframe

    Raises:
        SensiIOError: If the sensi config is not a dataframe,
        if the header is not correct, if the number of columns is not correct
        a value in 'Apply stress' is incorrect, or a value in 
        'Description' is incorrect if it is present
    """
    logger.info(f"Validating sensi config")

    required_headers = set(SENSI_CONFIG_HEADER)
    # Check if the sensi config is a dataframe
    if not isinstance(sensi_config, pd.DataFrame):
        logger.error(f"Sensi config is not a dataframe")
        raise SensiIOError("Sensitivity configuration file cannot be validated. Please check the file is a valid csv file.")

    # Checking if the sensi config has the correct number of columns using the '_count_sep' column   
    logger.debug("Checking sensi config number of columns")
    expected_columns_num = len(sensi_config.columns) - 1 # Num of column except the _count_sep
    if not (sensi_config["_count_sep"] == expected_columns_num - 1).all():
        rows_with_wrong_number_of_columns = sensi_config[sensi_config["_count_sep"] != expected_columns_num - 1].index.tolist()
        logger.error(f"Sensi config has the wrong number of columns. Rows with wrong number of columns: {rows_with_wrong_number_of_columns}")
        raise SensiIOError(f"Sensitivity configuration file has the wrong number of columns. Rows with wrong number of columns: {rows_with_wrong_number_of_columns}")

    # Drop the '_count_sep' column
    sensi_config = sensi_config.drop(columns="_count_sep")

    # Handle duplicate columns case by dropping the duplicates
    try:
        sensi_config = util.handle_duplicate_columns(sensi_config, handle_duplicates="raise")
    except ValueError as exc:
        logger.error(f"{exc}")
        raise SensiIOError(f"{exc}")

    # Checking if the sensi config has the required header
    logger.debug("Checking sensi config header")
    sensi_config_header = sensi_config.iloc[0].dropna().values.tolist()
    if not required_headers.issubset(set(sensi_config_header)):
        logger.error(f"Sensi config is missing required headers. Expected {SENSI_CONFIG_HEADER}, got {sensi_config_header}")
        raise SensiIOError(f"Sensitivity configuration file is missing required headers. Expected {SENSI_CONFIG_HEADER}, got {sensi_config_header}")

    # Checking if the required 'Apply stress' column has the correct values
    logger.debug('Checking sensi config values in "Apply stress"')
    apply_stress_values = sensi_config.iloc[1:, sensi_config_header.index("Apply stress")]
    apply_stress_values_check = apply_stress_values.map(lambda x: isinstance(x, bool) or x.lower() in ["true", "false"])
    if not apply_stress_values_check.all():
        rows_with_wrong_apply_stress_values = apply_stress_values[~apply_stress_values_check].index.tolist()
        logger.error(f"Sensi config has the wrong values in 'Apply stress' Rows with wrong values: {rows_with_wrong_apply_stress_values}")
        raise SensiIOError(f"Sensitivity configuration file has the wrong values in 'Apply stress'. Rows with wrong values: {rows_with_wrong_apply_stress_values}")

    # Checking if the optional 'Description' column that is present has the correct values
    logger.debug('Checking sensi config values in "Description" if it is present')
    if 'Description' in sensi_config_header:
        description_index = sensi_config_header.index("Description")
        description = sensi_config.iloc[1:, description_index]
        # Truncate the description to DESCRIPTION_MAX_LENGTH
        description = description.map(lambda x: (str(x)[:DESCRIPTION_MAX_LENGTH]) if isinstance(x, str) else x)
        # Re-check the description after truncating
        description_check = description.map(lambda x: isinstance(x, str) and len(x) <= DESCRIPTION_MAX_LENGTH and "\\n" not in x)
        if not description_check.all():
            rows_with_wrong_description = description[~description_check].index.tolist()
            logger.error(f"Sensi config has the wrong values in 'Description'. Rows with wrong values: {rows_with_wrong_description}")
            raise SensiIOError(f"Sensitivity configuration file has the wrong values in 'Description'. Rows with wrong values: {rows_with_wrong_description}")
        else:
            sensi_config.iloc[1:, description_index] = description

    logger.info("Sensi config is valid")
    return sensi_config


def validate_sensi_config(filepath):
    """Validates the sensi config file

    Args:
        filepath (str): Path to the sensi config file

    Returns:
        dict: The sensi config file as a dict
    """
    logger.info(f"Validating sensi config file {filepath}")

    # Read the sensi config file as a dataframe
    logger.debug(f"Reading sensi config file {filepath}")
    try:
        start_time = time.time()
        sensi_config = util.read_csv_from_filepath(filepath)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Reading sensi config file {filepath} took {execution_time:.2f} seconds")
    except (FileNotFoundError, ValueError) as exc:
        # return the error message as a string
        logger.error(f"Error reading sensi config file {filepath}: {exc}")
        return str(exc)

    # Validate the sensi config file
    logger.debug(f"Validating sensi config file {filepath}")
    try:
        sensi_config = sensi_config_is_valid(sensi_config)
    except SensiIOError as exc:
        # return the error message as a string
        logger.error(f"Error validating sensi config file {filepath}: {exc}")
        return str(exc)

    # Use the first row as the header
    sensi_config.columns = sensi_config.iloc[0]
    sensi_config = sensi_config[1:]
    sensi_config.reset_index(drop=True, inplace=True)

    logger.debug(f"Returned sensi config: {sensi_config}")
    return sensi_config


def sensi_param_is_valid(sensi_param):
    """Validates the sensi param file

    Args:
        sensi_param (dataframe): The sensi param as a dataframe

    Raises:
        SensiIOError: If the sensi param is not a dataframe,
        if the first column is not the 'Name' column
        or if the sensi param has the wrong number of columns
    """
    logger.info(f"Validating sensi param")

    if not isinstance(sensi_param, pd.DataFrame):
        logger.error(f"Sensi param is not a dataframe")
        raise SensiIOError("Sensi param is not a dataframe")

    # Checking if the sensi param has the correct number of columns using the '_count_sep' column
    logger.debug(f"Checking sensi param number of columns")
    if not sensi_param["_count_sep"].nunique() == 1:
        # Get the rows with the wrong number of columns excluding the header
        rows_with_wrong_number_of_columns = sensi_param[sensi_param["_count_sep"] != sensi_param["_count_sep"].nunique()].index.tolist()[1:]
        logger.error(f"Sensi param has the wrong number of columns. Rows with wrong number of columns: {rows_with_wrong_number_of_columns}")
        raise SensiIOError(f"Sensitivities parameters file has the wrong number of columns. Rows with wrong number of columns: {rows_with_wrong_number_of_columns}")

    # Drop the '_count_sep' column
    sensi_param = sensi_param.drop(columns="_count_sep")

    # Handle duplicate columns case by dropping the duplicates
    try:
        sensi_param = util.handle_duplicate_columns(sensi_param, handle_duplicates="raise")
    except ValueError as exc:
        logger.error(f"{exc}")
        raise SensiIOError(f"{exc}")

    # Checking if the first column in the first row is the 'Name' column
    logger.debug(f"Checking sensi param first column")
    if not sensi_param.iloc[0, 0] == "Name":
        logger.error(f'Sensi param first column is not the "Name" column')
        raise SensiIOError('Sensitivity parameters file first column is not the "Name" column')

    logger.info("Sensi param is valid")
    return sensi_param


def validate_sensi_param(filepath):
    """Validates the sensi param file

    Args:
        filepath (str): Path to the sensi param file

    Returns:
        dict: The sensi param file as a dict
    """
    logger.info(f"Validating sensi param file {filepath}")

    # Read the sensi param file as a dataframe
    logger.debug(f"Reading sensi param file {filepath}")
    start_time = time.time()
    try:
        sensi_param = util.read_csv_from_filepath(filepath)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Reading sensi param file {filepath} took {execution_time:.2f} seconds")
    except (FileNotFoundError, ValueError) as exc:
        # return the error message as a string
        return str(exc)

    # Validate the sensi param file
    logger.debug(f"Validating sensi param file {filepath}")
    start_time = time.time()
    try:
        sensi_param = sensi_param_is_valid(sensi_param)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Validating sensi param file {filepath} took {execution_time:.2f} seconds")
    except SensiIOError as exc:
        # return the error message as a string
        return str(exc)

    # Use the first row as the header
    start_time = time.time()
    sensi_param.columns = sensi_param.iloc[0]
    sensi_param = sensi_param[1:]
    sensi_param.reset_index(drop=True, inplace=True)
    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug(f"Reset index for sensi param file {filepath} took {execution_time:.2f} seconds")
    return sensi_param


def get_sensi_and_param_lists(sensi_config, sensi_param):
    """Gets the sensi list, sensi descriptions and param list
    from the sensi config and sensi param files

    Args:
        sensi_config (dataframe): The sensi config file as a dataframe
        sensi_param (dataframe): The sensi param file as a dataframe

    Raises:
        SensiIOError: If the sensi config and sensi param files
        do not have the same number of rows

    Returns:
        tuple: (sensi_list(dict), sensi_descriptions(ordered dict), param_list(dict))
    """
    logger.debug(f"Checking if sensi config and sensi param are valid...")
    # Check if the values in the 'Stress name' column are a subset of
    # the columns in the sensi param file except the 'Name' column
    start_time = time.time()
    if not set(sensi_config["Stress name"]).issubset(set(sensi_param.columns.tolist()[1:])):
        # Get the values in the 'Stress name' column that are not a subset
        # of the columns in the sensi param file except the 'Name' column
        sensi_config_stress_names_not_in_sensi_param = set(sensi_config["Stress name"]) - set(sensi_param.columns.tolist()[1:])
        logger.error(
            "Stress names in the sensi config file are not a subset of the stress names in the sensi param file. "
            f"Stress names not in the sensi param file: {sensi_config_stress_names_not_in_sensi_param}"
        )
        raise SensiIOError(
            "Stress names in the Sensitivity configuration file are not a subset "
            "of the stress names in the Sensitivity parameters file. Stress names "
            f"not in the Sensitivity parameters file: {sensi_config_stress_names_not_in_sensi_param}"
        )
    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug(f"Checking if 'Stress name' in the header took {execution_time:.2f} seconds")
    # Get the dict sensi_list
    start_time = time.time()
    sensi_names = sensi_config["Scenario"].unique().tolist()
    # Filter rows where 'Apply stress' equals 'true' (case insensitive)
    mask_true = sensi_config["Apply stress"].str.lower() == "true"
    # Group by 'Scenario', collecting 'Stress name' as a list where condition is met
    filtered = sensi_config[mask_true].groupby("Scenario")["Stress name"].apply(list)
    # Create final dict, filling empty values for scenarios if needed
    sensi_list = {name: filtered.get(name, []) for name in sensi_names}
    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug(f"Checking if 'Scenario' in the header took {execution_time:.2f} seconds")
    # Get the dict sensi_descriptions
    logger.debug(f"Getting sensi descriptions")
    start_time = time.time()
    if 'Description' in sensi_config.columns:
        sensi_config_non_empty_descriptions = sensi_config[(sensi_config['Description'] != '') & (sensi_config['Description'].notna())]
        descriptions = sensi_config_non_empty_descriptions.groupby('Scenario')['Description'].first()
    else:
        descriptions = pd.Series(dtype=str)
    sensi_descriptions = OrderedDict((name, descriptions.get(name, 'no description')) for name in sensi_names) 
    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug(f"Checking if 'Description' in the header took {execution_time:.2f} seconds")
    # Get the list param_list

    start_time = time.time()
    stress_names = list(sensi_param.columns)[1:]
    #logger.debug(f"sensi_param names: {stress_names}")
    param_map_unsorted = {
        col: (sensi_param.loc[sensi_param[col] != '', 'Name'] + '=' +
              sensi_param.loc[sensi_param[col] != '', col].astype(str)).tolist()
        for col in stress_names
    }

    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug(f"Adding params to list took {execution_time:.2f} seconds")
    # Get the list param_map
    # Sort the param map unsorted by the order of the stress names in the 'Stress name' column
    # of the sensi config file where 'Apply stress' is True or 'true' (case insensitive)
    start_time = time.time()
    param_map = {
        stress_name: param_map_unsorted[stress_name]
        for stress_name in sensi_config[sensi_config["Apply stress"].str.lower() == "true"]["Stress name"].tolist()
    }
    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug(f"Apply 'Apply stress' to param to list took {execution_time:.2f} seconds")

    return sensi_list, sensi_descriptions, param_map, 


def read_sensitivities(env_dir):
    """Reads the sensitivities files

    Args:
        env_dir (str): Path to the environment directory

    Raises:
        SensiIOError: If either the sensi config
        or sensi param file is not valid

    Returns:
        tuple: (sensi_list(dict), sensi_descriptions (ordered dict), param_list(dict))
    """
    logger.info(f"Reading sensitivities from {env_dir}")

    # Read sensi_config.csv and validate using validate_sensi_config
    logger.debug(f"Reading sensi_config.csv")
    result = validate_sensi_config(util.find_file_in_directory("Sensi_config.csv", env_dir))
    if isinstance(result, str):
        logger.error(result)
        raise SensiIOError(result)
    sensi_config = result

    # Read sensi_param.csv and validate using validate_sensi_param
    logger.debug(f"Reading sensi_param.csv")
    result = validate_sensi_param(util.find_file_in_directory("Sensi_param.csv", env_dir))
    if isinstance(result, str):
        logger.error(result)
        raise SensiIOError(result)
    sensi_param = result

    return get_sensi_and_param_lists(sensi_config, sensi_param)


def create_dir_for_one_sensi_from_base(sensi_name, sensi_path, base_dir, exclude=None):
    """Creates a directory for one sensitivity from the base directory

    Args:
        sensi_name (str): Name of the sensitivity.
        sensi_path (str): Path to the sensitivity directory
        base_dir (str): Path to the base directory
        exclude (list, optional): List of files or directories to exclude from copying
            Defaults to ["settings_calibration.json", "settings_simulation.json", "RN_outputs", "RW_outputs"]

    Returns:
        (str or SensiIOError): Path to the sensitivity directory if successful, SensiIOError if not
    """
    if exclude is None:
        exclude = ["settings_calibration.json", "settings_simulation.json", "RN_outputs", "RW_outputs"]

    logger.info(f"Creating directory for one sensitivity from base directory {base_dir}")
    sensi_path = sensi_path.replace("\\", "/")
    base_dir = base_dir.replace("\\", "/")

    logger.info(f"Creating directory {sensi_path} from base directory {base_dir}")

    # Check if the base directory exists
    if not os.path.exists(base_dir):
        logger.error(f"Base directory {base_dir} does not exist")
        return SensiIOError(f"Base directory does not exist")

    # Copy 'resources' and 'resources_admin' from base directory to sensi directory
    logger.debug(f"Copying resources and resources_admin from base directory to sensi directory")
    try:
        sensi_rsrc_dir = os.path.join(sensi_path, "resources").replace("\\", "/")
        sensi_rsrc_admin_dir = os.path.join(sensi_path, "resources_admin").replace("\\", "/")
        base_rsrc_dir = os.path.join(base_dir, "resources").replace("\\", "/")
        base_rsrc_admin_dir = os.path.join(base_dir, "resources_admin").replace("\\", "/")

        if os.path.exists(sensi_rsrc_dir):
            shutil.rmtree(sensi_rsrc_dir, ignore_errors=True)
        logger.info(f"Copying {base_rsrc_dir} to {sensi_rsrc_dir}")
        util.copy_dir(base_rsrc_dir, sensi_rsrc_dir, exclude)
        if os.path.exists(sensi_rsrc_admin_dir):
            shutil.rmtree(sensi_rsrc_admin_dir, ignore_errors=True)
        logger.info(f"Copying {base_rsrc_admin_dir} to {sensi_rsrc_admin_dir}")
        util.copy_dir(base_rsrc_admin_dir, sensi_rsrc_admin_dir, exclude)
        logger.debug("Copy completed")
    except OSError as err:
        logger.error(f"Unable to copy resources/resources_admin from base directory: {err}")
        return SensiIOError(f"Unable to copy resources/resources_admin from base directory")
    except Exception as e:
        logger.error(f"Error while copying resources/resources_admin from base directory: {e}")
        return SensiIOError(f"Error while copying resources/resources_admin from base directory")

    # Write values of the sensi to settings.json
    logger.debug(f"Writing values of the sensi to settings.json")
    try:
        settings_path = os.path.join(sensi_path, "resources", "settings.json").replace("\\", "/")
        settings_json = util.read_json_file(settings_path)
        settings_json["gen_param"]["name"] = "{}_{}".format(settings_json["gen_param"]["name"], sensi_name)
        settings_json["gen_param"]["path"] = sensi_path
        settings_json["framework"]["sensi_1"]["name"] = sensi_name
        # Save the settings.json file
        with open(settings_path, "w") as f:
            json.dump(settings_json, f, indent=4)
    except Exception as e:
        logger.error(f"Error writing values of the sensi to settings.json: {e}")
        return SensiIOError(f"Error writing values of the sensi to settings.json")

    return sensi_path


class SensiConfig:
    def __init__(self, env_dir):
        """The SensiConfig class

        Args:
            env_dir (str): The path to the environment directory

        Raises:
            SensiIOError: If the environment directory does not exist
        """
        logger.info(f"Creating SensiConfig object with env_dir: {env_dir}")
        if not os.path.exists(env_dir):
            logger.error(f"Failed to find Base table {env_dir}")
            raise SensiIOError("Base table {} does not exist".format(env_dir))

        self.base_dir = env_dir
        try:
            self.settings_json = util.read_json_file(f"{env_dir}/resources/settings.json")
            (
                self.sensi_list,
                self.sensi_descriptions,
                self.param_map,
            ) = read_sensitivities(self.base_dir)
        except Exception as e:
            logger.error(f"Error creating SensiConfig object: {e}")
            raise SensiIOError(f"Error creating SensiConfig object: {e}")

    def get_stress_desc(self, sensi_name):
        """Gets the stress description for a sensitivity

        Args:
            sensi_name (str): The name of the sensitivity

        Returns:
            str: The stress description
        """
        logger.info(f"Get stress description for sensi in {sensi_name}")
        param_list = self.sensi_list.get(sensi_name, [])
        start_time = time.time()
        ret = "".join([">>".join(self.param_map.get(p, [""])) for p in param_list])
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Join stress string took: {execution_time:.2f} seconds")
        return ret

    def create_tables(self, sensi_dirs={}):
        """Creates the sensitivity tables

        Args:
            sensi_dirs (dict, optional): The dictionary of sensitivity directories. Defaults to {}.

        Returns:
            dict: The dictionary of sensitivity directories processed or error messages
        """
        # For Seni_config.csv
        # To new create directory from the name of the Scenario
        # Copy env_dir to each directory of the name of the Scenario
        # Replace gen_param.name = name of the Scenario in the settings.json of the newly copied directory
        # Replace gen_param.path = newly created path
        # Input sensi_dirs can be provided by the API as dict { "<SENSI_NAME>":"<TABLE_ENV_PATH>" }
        # If sensi_dirs is provided, only the tables for the Sensi there are created
        # Else all the tables are created for every sensi in sensi_list
        # Dict that contains the list of sensi and their dirs
        logger.debug(f"Creating sensitivity tables")

        processed_sensi_dirs = {}
        if len(self.sensi_list) <= 0:
            logger.info(f"No sensitivities found")
            return processed_sensi_dirs

        # Only create tables for the sensi in the sensi_dirs
        if len(sensi_dirs) > 0:
            logger.info(f"Creating tables for sensi_dirs: {sensi_dirs}")
            for sensi in self.sensi_list.keys():
                # Checks that it is a sensi in the specified sensi lists (i.e. sensi_dirs)
                # or that there is at least one stress name to apply for it.
                if sensi in sensi_dirs.keys() and len(self.sensi_list[sensi]) > 0:
                    logger.debug(f"Creating table for sensi: {sensi}")
                    res = create_dir_for_one_sensi_from_base(sensi, sensi_dirs[sensi], self.base_dir)
                    processed_sensi_dirs[sensi] = res
        else:
            logger.debug(f"Creating tables for all sensi in sensi_list")
            path = Path(self.base_dir)
            parent_dir = path.parent
            for sensi in self.sensi_list.keys():
                if len(self.sensi_list[sensi]) > 0:
                    logger.debug(f"Creating table for sensi: {sensi}")
                    res = create_dir_for_one_sensi_from_base(sensi, os.path.join(parent_dir, sensi), self.base_dir)
                    processed_sensi_dirs[sensi] = res

        logger.info(f"Processed sensitivity directories: {processed_sensi_dirs.keys()}")
        return processed_sensi_dirs

    def _get_sensi_dirs_to_process(self, sensi_dirs={}):
        """Gets the sensitivity directories to process

        Args:
            sensi_dirs (dict): The dictionary of sensitivity directories

        Returns:
            dict: The dictionary of sensitivity directories to process
        """
        logger.debug(f"Getting sensitivity directories to process")

        sensi_dirs_to_process = {}

        if len(sensi_dirs) > 0:
            logger.info(f"Applying sensitivities to sensi_dirs: {sensi_dirs}")
            for sensi in self.sensi_list.keys():
                if sensi in sensi_dirs.keys():
                    logger.debug(f"Applying sensitivities to sensi: {sensi}")
                    sensi_dirs_to_process[sensi] = sensi_dirs[sensi].replace("\\", "/")
        else:
            logger.info(f"Applying sensitivities to all sensi in {self.base_dir}")
            path = Path(self.base_dir)
            parent_dir = path.parent
            for sensi in self.sensi_list.keys():
                logger.debug(f"Applying sensitivities to sensi: {sensi}")
                sensi_dirs_to_process[sensi] = os.path.join(parent_dir, sensi).replace("\\", "/")

        return sensi_dirs_to_process

    def _parse_stresses(self, sensi_dirs_to_process=[]):
        """Parses the stresses for each sensitivity that needs to be processed.

        Organizes stresses by sensitivity and groups commands by file to minimize I/O operations.
        Args:
            sensi_dirs_to_process (dict): Dictionary of sensitivity directories to process.
        """
        logger.debug("Parsing stresses for specified sensitivities.")
        self.parsed_stresses = {}

        for sensi_name in sensi_dirs_to_process:
            logger.debug(f"Parsing stresses for sensitivity: {sensi_name}")
            settings_modif_express = []
            settings_modif_values = []
            stresses_by_file_expression = defaultdict(list)

            for stress_name in self.sensi_list[sensi_name]:
                logger.debug(f"Processing stress: {stress_name}")
                for command in self.param_map[stress_name]:
                    # Parse the command
                    try:
                        logger.debug(f"Parsing command: {command}")
                        syntax = syn.parse_param(command)
                    except syn.SensiSyntaxError as e:
                        logger.error(f"Error parsing command '{command}' for stress '{stress_name}': {e}")
                        raise SensiIOError(f"Unable to parse command '{command}' for stress '{stress_name}'.")

                    if syntax.expression.startswith("$"):
                        # Store the syntax with the file expression (will resolve the path later)
                        stresses_by_file_expression[syntax.expression].append(syntax)
                    else:
                        # Handle settings modifications
                        try:
                            settings_path = os.path.join(sensi_dirs_to_process[sensi_name], "resources", "settings.json").replace("\\", "/")
                            settings_json = util.read_json_file(settings_path)
                            table_name = util.query(settings_json, "$.framework.sensi_1.name")[0]
                            expression = (
                                syntax.expression
                                if syntax.expression.startswith("framework") or syntax.expression.startswith("gen_param")
                                else f"framework.sensi[{table_name}].{syntax.expression}"
                            )
                            settings_modif_express.append(expression)
                            settings_modif_values.append(syntax.value)
                            logger.debug(f"Added settings modification: {expression} = {syntax.value}")
                        except Exception as e:
                            logger.error(f"Unable to add '{syntax.expression}' to settings modifications of '{sensi_name}': {e}")
                            raise SensiIOError(f"Unable to add '{syntax.expression}' to settings modifications of '{sensi_name}'.")

            self.parsed_stresses[sensi_name] = {
                'stresses_by_file_expression': stresses_by_file_expression,
                'settings_modif_express': settings_modif_express,
                'settings_modif_values': settings_modif_values,
            }

    def _apply_stress_to_sensi(self, sensi_name, sensi_dirpath):
        """Applies the stress to the specified sensitivity.

        Args:
            sensi_name (str): Name of the sensitivity.
            sensi_dirpath (str): Path to the sensitivity directory.

        Returns:
            str or SensiIOError: Result message or error.
        """
        logger.info(f"Applying stress to sensitivity: {sensi_name}")
        message = ""
        total_applied = 0

        # Retrieve parsed data for the sensitivity
        parsed_data = self.parsed_stresses.get(sensi_name, {})
        stresses_by_file_expression = parsed_data.get('stresses_by_file_expression', {})
        settings_modif_express = parsed_data.get('settings_modif_express', [])
        settings_modif_values = parsed_data.get('settings_modif_values', [])

        # Resolve file paths for stresses
        stresses_by_file = defaultdict(list)
        for expression, syntaxes in stresses_by_file_expression.items():
            try:
                file_path = util.get_input_file_path(self.settings_json, expression, sensi_dirpath)
                stresses_by_file[file_path].extend(syntaxes)
            except RuntimeError as e:
                logger.error(f"Error resolving file path for expression '{expression}' in sensitivity '{sensi_name}': {e}")
                return SensiIOError(f"Unable to resolve file path for expression '{expression}' in sensitivity '{sensi_name}'.")

        # Apply all stresses grouped by file
        for file_path, syntaxes in stresses_by_file.items():
            logger.info(f"Applying {len(syntaxes)} stresses to file: {file_path}")
            for syntax in syntaxes:
                applied = syn.apply_syntax_to_file(file_path, syntax, self.settings_json)
                if applied:
                    total_applied += 1
                    logger.debug(f'Applied syntax on file {file_path}: col="{syntax.col}, condition="{syntax.condition}", value="{syntax.value}"')
                else:
                    logger.error(f'Unable to apply syntax on input file {file_path}')
                    return SensiIOError(f"Failed to apply '{sensi_name}' stress on '{os.path.basename(file_path)}'")

        # Save modified dataframes
        try:
            syn.save_all_modified_dataframes(self.settings_json)
            logger.info("Successfully saved all modified DataFrames.")
        except Exception as e:
            logger.error(f"Failed to save modified DataFrames: {e}")
            return SensiIOError("An error occurred while saving the modified data files.")

        # Saving settings_modif commands to settings_modif.csv
        if settings_modif_express and settings_modif_values:
            try:
                settings_modif_pd = pd.DataFrame({"id": settings_modif_express, "value": settings_modif_values})
                settings_modif_path = os.path.join(sensi_dirpath, "resources", "settings_modif.csv")
                settings_modif_pd.to_csv(settings_modif_path, sep=";", index=False)
                total_applied += len(settings_modif_express)
                logger.debug(f"Saved settings modifications to {settings_modif_path}")
            except Exception as e:
                logger.error(f"Failed to save settings modifications: {e}")
                return SensiIOError("An error occurred while saving the settings modifications.")

        message = f"Applied {total_applied} modification(s) on '{sensi_name}'."
        logger.info(message)
        return message

    def apply(self, sensi_dirs={}):
        """Applies the sensitivities to the tables

        Args:
            sensi_dirs (dict, optional): The dictionary of sensitivity
            directories. Defaults to {}.

        Returns:
            dict: The dictionary of sensitivity directories processed
        """
        # For Sensi_param.csv
        # Iterate over sensi_list and apply the stress in the param_map
        # When interate param_map:
        # Build the good correct path from the json query
        # Call syntax.apply_sentax_to_file(path, syntax) in the syntax.py
        # Input sensi_dirs can be provided by the API as dict { "<SENSI_NAME>":"<TABLE_ENV_PATH>" }
        # If sensi_dirs is provided, only Sensi in sensi_dirs are stress applied
        # Else all the sensis are stress applied
        # Dict that contains the list of sensi and their dirs
        logger.info(f"Applying sensitivities to tables")

        processed_sensi_messages = {}

        if not self.sensi_list or not self.param_map:
            logger.error("Sensi list or param map is empty.")
            return {}

        # Update sensi_dirs to process
        sensi_dirs_to_process = self._get_sensi_dirs_to_process(sensi_dirs)

        # Parse all stresses before applying
        try:
            self._parse_stresses(sensi_dirs_to_process)
        except SensiIOError as e:
            logger.error(f"Error during stress parsing: {e}")
            return {}

        # Clear caches before applying stress
        util.clear_query_cache()
        syn.clear_file_cache()
        syn.clear_modified_dataframes_cache()

        # Applying the stress to the sensi
        for sensi_name, sensi_dirpath in sensi_dirs_to_process.items():
            if not os.path.exists(sensi_dirpath):
                logger.error(f"Sensitivity directory does not exist: {sensi_dirpath}")
                processed_sensi_messages[sensi_name] = SensiIOError("Sensitivity path does not exist")
                continue

            if self.settings_json is None:
                logger.error(f"No settings_json found for {sensi_name}")
                processed_sensi_messages[sensi_name] = SensiIOError("No settings file found")
                continue

            # Applying the stress to the sensi
            logger.debug(f"Applying stress to sensi: {sensi_name}")
            processed_sensi_messages[sensi_name] = self._apply_stress_to_sensi(sensi_name, sensi_dirpath)

        return processed_sensi_messages
