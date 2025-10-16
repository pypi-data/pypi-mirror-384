import csv
import hashlib
import json
import os
import re
import shutil

import pandas as pd
from objectpath import Tree
from pandas.errors import EmptyDataError, ParserError

FILE_MARK = "file::"
STR_MARK = "str::"

MODEL_DIR_NAMES = {
    "IR": "Nominal_rates",
    "RIR": "Real_rates",
    "EQ": "Equity",
    "RE": "Real_estate",
    "CRED": "Credit",
    "FX": "FX_rate",
}

PARAM_KEYS_FOLDERS_MAPPING = {
    "param.dependence": "Correlation",
    "hist_corr.target_corr": "Correlation", # Kept for backward compatibility (Core <= 02.01.00)
    "corr.target.mkt": "Correlation",
    "param.table_format": "Formats",
    "param.roll_forward": "Roll_Forward",
    "param.aom": "Roll_Forward",
    "param.report.mt.weights": "Report",
    "param.report.mt.asset_shares": "Report",
    "param.report.mc.swaptions.weights": "Report",
    "param.report.mc.swaptions.thresholds": "Report",
    "param.report.mc.eq_re_options.weights": "Report",
    "param.report.mc.eq_re_options.thresholds": "Report",
    "param.report.mc.fx_options.weights": "Report",
    "param.report.mc.fx_options.thresholds": "Report",
}


def read_json_file(file_path):
    """Reads a json file and returns a dict

    Args:
        file_path (str): Path to the json file

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not a json file

    Returns:
        dict: The json file as a dict
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist. Unable to read json")

    with open(file_path, "r") as json_file:
        try:
            json_data = json.load(json_file)
        except ValueError as exc:
            raise ValueError(f"{file_path} is not a valid json file. {str(exc)}")

        return json_data


def find_file_in_directory(filename, dir):
    """Finds a file in a directory

    Args:
        filename (str): The name of the file to find
        dir (str): The directory to search

    Returns:
        str: The path to the file if found, None otherwise
    """
    if not os.path.exists(dir):
        return None

    for root, _, files in os.walk(dir):
        if filename in files:
            return os.path.join(root, filename).replace("\\", "/")

    return None


def read_csv_from_filepath(filepath):
    """Reads a csv file and returns a dataframe

    Args:
        filepath (str): Path to the csv file

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty, not valid, or contains reserved column names

    Returns:
        dataframe: The csv file as a dataframe
    """
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError("File does not exist. Unable to read csv")

    # Reads the content of the csv file to a single column and applies
    # a mapping to replace all ; inside "" to _SEMI_COL
    # .squeeze("columns") turns a dataframe with a single column
    # to a Series that which we verify is the result's type
    try:
        # Read the csv file as a series using '~' as the delimiter
        # which should not be present in the csv file
        sensi_file = pd.read_csv(filepath, sep=r"~", encoding="utf-8", header=None, quoting=csv.QUOTE_NONE).squeeze("columns")
        if not isinstance(sensi_file, pd.Series):
            raise ValueError('File contains the delimiter "~" which is not allowed in sensi csv files')
    except EmptyDataError:
        raise ValueError("File is empty")
    except ParserError:
        raise ValueError("File is not a valid csv file")

    # Replace all ; inside "" with _SEMI_COL and replace all " with nothing
    # And then split the whole csv using the remaining ; as delimiter
    # And add a '_count_sep' column to count the number of ; in each row
    try:
        sensi_file = sensi_file.map(lambda x: re.sub(r'"([^"]*)"', lambda m: re.sub(r";", "_SEMI_COL", m.group()), x))
        sensi_file = sensi_file.map(lambda x: re.sub(r'"', "", x))

        split_data = sensi_file.str.split(";", expand=True)

        # Check for reserved column names
        reserved_columns = {"_count_sep"}
        headers = split_data.iloc[0].tolist()
        overlapping_columns = reserved_columns.intersection(headers)
        if overlapping_columns:
            raise ValueError(f"Reserved column name(s) found in the CSV: {', '.join(overlapping_columns)}")

        sensi_file = pd.concat(
            [
                split_data,
                sensi_file.str.count(";").rename("_count_sep"),
            ],
            axis=1,
        )
        # Replace back all _SEMI_COL with ;
        sensi_file = sensi_file.replace("_SEMI_COL", ";", regex=True)
    except:
        raise ValueError("File is not a valid csv file")

    return sensi_file


def handle_duplicate_columns(df, handle_duplicates="drop"):
    """
    Handle duplicate columns in a dataframe where the headers are stored in the first row
    
    Args:
        df (dataframe): The dataframe to handle
        handle_duplicates (str): The method to handle duplicates. Options are "drop" or "rename" or "raise"

    Raises:
        ValueError: If headers are missing or if handle_duplicates is invalid
        ValueError: If handle_duplicates is set to "raise" and duplicates are found

    Returns:
        dataframe: The dataframe with duplicate columns handled
    """

    valid_duplicate_strategies = ["drop", "rename", "raise"]
    if handle_duplicates not in valid_duplicate_strategies:
        raise ValueError("Invalid value for handle_duplicates. Use 'drop', 'rename', or 'raise'.")

    if df.empty:
        return df

    # Extract headers from the first row
    headers = df.iloc[0].tolist()
    headers_index = pd.Index(headers)

    if headers_index.duplicated().any():
        duplicates = headers_index[headers_index.duplicated()].unique()
        duplicate_details = [
            f"{name} (indexes: {', '.join(str(idx+1) for idx in [i for i, val in enumerate(headers) if val == name])})"
            for name in duplicates
        ]

        if handle_duplicates == "raise":
            raise ValueError(f"Duplicate columns found: {', '.join(duplicate_details)}")
        elif handle_duplicates == "drop":
            non_duplicated_mask = ~headers_index.duplicated()
            df = df.iloc[:, non_duplicated_mask].copy()
            df.columns = range(len(df.columns))
        elif handle_duplicates == "rename":
            new_headers = []
            counts = {}
            for col in headers:
                if col not in counts:
                    counts[col] = 0
                    new_headers.append(col)
                else:
                    counts[col] += 1
                    new_headers.append(f"{col}.{counts[col]}")
            df.iloc[0] = new_headers

    return df


def copy_dir(base_rsrc_dir, sensi_rsrc_dir, exclude=None):
    """
    Copy the contents of base_rsrc_dir to sensi_rsrc_dir,
    recursively copying any linked directories and excluding specified files and directories.
    
    Args:
        base_rsrc_dir (str): The base directory to copy from
        sensi_rsrc_dir (str): The destination directory to copy to
        exclude (list): List of files and directories to exclude from the copy
    """
    if exclude is None:
        exclude = []

    for root, dirs, files in os.walk(base_rsrc_dir):
        # Exclude directories by name
        dirs[:] = [d for d in dirs if d not in exclude]

        for item in files + dirs:
            if item in exclude:
                continue

            path = os.path.join(root, item)
            real_path = os.path.realpath(path) if os.path.islink(path) else path

            # If the path is a symlink but doesn't point to an existing file/folder, skip it
            if not os.path.exists(real_path):
                continue

            dest_path = os.path.join(sensi_rsrc_dir, os.path.relpath(path, base_rsrc_dir))

            if os.path.islink(path) and os.path.isdir(real_path):
                # Recursive call to copy the linked directory
                os.makedirs(dest_path, exist_ok=True)
                copy_dir(real_path, dest_path)
            else:
                copy_file_or_directory(path, dest_path)


def copy_file_or_directory(src_path, dest_path):
    try:
        if os.path.isdir(src_path):
            os.makedirs(dest_path, exist_ok=True)
        else:
            # Ensure the destination directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
    except Exception as e:
        print(f"Exception while copying {src_path} to {dest_path}: {e}")


# Cache for query results
query_cache = {}

def generate_data_hash(data):
    """Generate a unique hash for the data
    
    Args:
        data (dict): data to generate hash for
    
    Returns:
        str: hash of the data
    """
    data_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()


def query(data, expression):
    """Queries data using expression

    Args:
        data (json): data to query from
        expression (str): expression to query with

    Raises:
        ValueError: if data is empty
        or expression is invalid or the query fails

    Returns:
        list: list of results (or a single result)
    """

    if data is None or expression is None:
        raise ValueError("Incorrect input. data or expression is None")
    expression = expression.strip()
    if not expression.startswith("$"):
        raise ValueError("Expression does not start with $")

    # Generate a unique key for caching the query result
    data_hash = generate_data_hash(data)
    cache_key = f"{data_hash}_{expression}"

    if cache_key in query_cache:
        return query_cache[cache_key]

    result = []
    try:
        tree = Tree(data)
        query_result = tree.execute(expression)
        if query_result:
            if isinstance(query_result, str):
                # Convert string to a list with one element
                result = query_result.split(None, -1)
            else:
                result = list(query_result)

    except Exception as e:
        raise ValueError(f"Failed to query for data")

    # Cache the result
    query_cache[cache_key] = result

    return result

def clear_query_cache():
    """Clears the query cache"""
    query_cache.clear()


def extract_eco_and_driver_from_expression(data, expression):
    """Extracts eco and driver from the expression"""

    if not expression:
        return None, None

    # Normalize the expression
    expression = expression.replace(" ", "")

    pattern = r"(eco_(\d+)|\[@\.nameis['\"](\w+)['\"]\])(.*?)(driver_(\d+)|\[@\.nameis['\"](\w+)['\"]\])"

    match = re.search(pattern, expression)
    if match:
        # Extract eco and driver values
        eco = match.group(2) or match.group(3)
        driver = match.group(6) or match.group(7)

        if eco.isdigit():
            eco_name_query = f"$.framework.sensi_1.eco_{eco}.name"
            try:
                eco_name = query(data, eco_name_query)[0]
            except (ValueError, IndexError) as e:
                return None, None
            if not eco_name:
                return None, None
        else:
            eco_name = eco

        if driver.isdigit():
            driver_name_query = f"$.framework.sensi_1..*[@.name is '{eco_name}'].driver_{driver}.name"
            try:
                driver_name = query(data, driver_name_query)[0]
            except (ValueError, IndexError) as e:
                return None, None
            if not eco_name or not driver_name:
                return None, None
        else:
            driver_name = driver

        # Check that the eco and driver names are valid by querying for driver name
        try:
            check = query(data, f"$..*[@.name is '{eco_name}']..*[@.name is '{driver_name}']")[0]
        except (ValueError, IndexError) as e:
            return None, None
        if not check:
            return None, None

        return eco_name, driver_name

    return None, None


def get_input_file_path(data, expression, env_dir):
    """Gets the input file path from the data using the expression

    Args:
        data (dict): data to query from
        expression (str): expression to query with
        env_dir (str): environment directory where the input file is located

    Raises:
        RuntimeError: if any of the queries fail

    Returns:
        str: input file path
    """

    # Query for input file (also validates that the expression is valid)
    try:
        filename = query(data, expression)[0]
    except (ValueError, IndexError) as e:
        raise RuntimeError("Error occurred while fetching input file path")
    if not filename:
        raise RuntimeError("Input file name is null or empty")

    # TODO: Check if this is needed for backward compatibility
    if not filename.endswith(".csv"):
        filename += ".csv"

    # Extract eco and driver from the expression
    eco_name, driver_name = extract_eco_and_driver_from_expression(data, expression)
    if eco_name and driver_name:
        # Get the eco_folder_id
        try:
            eco_folder_id = query(data, f"$..*[@.name is '{eco_name}'].folder_id")[0]
        except (ValueError, IndexError) as e:
            raise RuntimeError("Unable to get eco_folder_id")
        if eco_folder_id is None:
            raise RuntimeError(f"Unable to find eco_folder_id for eco_name: {eco_name}")

        # Get the driver_folder_name
        try:
            driver_data = query(data, f"$..*[@.name is '{eco_name}']..*[@.name is '{driver_name}']")[0]
            driver_name = driver_data.get("class", driver_data.get("subclass", None))
        except (ValueError, IndexError) as e:
            raise RuntimeError("Unable to get driver_folder_name")
        driver_folder_name = MODEL_DIR_NAMES.get(driver_name, None)
        if driver_folder_name is None:
            raise RuntimeError(f"Unable to find driver_folder_id for driver_name: {driver_name}")

        local_filepaths = [
            "/".join([eco_name, driver_folder_name, filename]),
            "/".join([eco_folder_id, driver_folder_name, filename])
        ]

    else:
        param_query = expression.replace(".filename", "").replace("$.framework.sensi_1.", "")

        # Use the KEY_FOLDER_MAPPING and construct the local path of the input file
        param_folder_name = PARAM_KEYS_FOLDERS_MAPPING.get(param_query, None)
        if param_folder_name is None:
            raise RuntimeError(f"The param key from the expression provided is not recognized")

        local_filepaths = ["/".join([param_folder_name, filename])]

    # Get the framework name and sensi_1 name and folder_id
    try:
        framework_name = query(data, "$.framework.name")[0]
        input_folder = framework_name + "_inputs"
        folder_name = query(data, "$.framework.sensi_1.name")[0]
        folder_id = query(data, "$.framework.sensi_1.folder_id")[0]
    except (ValueError, IndexError) as e:
        raise RuntimeError("Unable to get framework.name or framework.sensi_1.name from data")

    # In settings.json, resources_folder is specified with filename
    resources_folder_query = expression.replace(".filename", "") + ".resources_folder"
    try:
        resources_folder = query(data, resources_folder_query)[0]
    except IndexError as e:
        # For params.table_format, the filename is specified without resources_folder
        resources_folder = "resources_admin"
    except ValueError as e:
        raise RuntimeError("Unable to get resources_folder from data")

    # Construct the global path of the input file
    possible_glob_filepaths = []
    if resources_folder == "resources":
        for local_filepath in local_filepaths:
            possible_glob_filepaths.append(os.path.join(env_dir, resources_folder, folder_name, input_folder, local_filepath))
            possible_glob_filepaths.append(os.path.join(env_dir, resources_folder, folder_id, input_folder, local_filepath))
    else:
        for local_filepath in local_filepaths:
            possible_glob_filepaths.append(os.path.join(env_dir, resources_folder, input_folder, local_filepath))
            possible_glob_filepaths.append(os.path.join(env_dir, resources_folder, local_filepath))

    for filepath in possible_glob_filepaths:
        if os.path.exists(filepath):
            return filepath.replace("\\", "/")
    
    raise RuntimeError(f"Unable to find input file: {filename}")
