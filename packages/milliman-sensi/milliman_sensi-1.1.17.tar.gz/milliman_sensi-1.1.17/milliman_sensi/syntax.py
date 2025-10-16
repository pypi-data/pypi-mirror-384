import logging
import os
import re

import pandas as pd
from mpmath import mp

from milliman_sensi.utility import FILE_MARK, STR_MARK

PRECISION = 13

mp.dps = PRECISION
mp.pretty = False

logger = logging.getLogger(__name__)


# Custom Exception class for sensi validation
class SensiSyntaxError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)

    def __str__(self):
        return self.msg


class Syntax:
    def __init__(self, expression="", col="", condition="", value=""):
        """Initialize a Syntax object

        Args:
            expression (str, optional): The expression to be evaluated.
            col (str, optional): The column name.
            condition (str, optional): The condition to be evaluated.
            value (str, optional): The value to be evaluated.
        """
        self.expression = expression
        self.col = col
        self.condition = condition
        self.value = value

    def __str__(self):
        return f"Syntax(expression={self.expression}, col={self.col}, condition={self.condition}, value={self.value})"


def extract_value_from_equal(param_string):
    """Extracts syntax and value from param_string if param_string contains =

    Args:
        param_string (str): string to be parsed

    Raises:
        SensiSyntaxError: if param_string does not contain =

    Returns:
        tuple: (syntax (str), value (str))
    """
    logger.debug(f"Extracting value from {param_string}")

    if not "=" in param_string:
        logger.error(f'Incorrect syntax in param. Unable to find "=" in {param_string}')
        raise SensiSyntaxError('Incorrect syntax in param. Unable to find "="')

    # Check for STR_MARK in param_string and ensure it appears only once
    str_prefix_count = param_string.count(STR_MARK)
    if str_prefix_count > 1:
        logger.error(f"Incorrect usage of '{STR_MARK}' in {param_string}")
        raise SensiSyntaxError(f"Incorrect usage of '{STR_MARK}' in param_string (multiple occurrences)")

    if str_prefix_count == 1:
        # STR_MARK is present and appears only once
        str_prefix_pos = param_string.find(STR_MARK)
        equal_before_str_pos = param_string.rfind('=', 0, str_prefix_pos)
        if equal_before_str_pos == -1:
            logger.error(f"'=' must be present before '{STR_MARK}' in {param_string}")
            raise SensiSyntaxError(f"'=' must be present before '{STR_MARK}' when '{STR_MARK}' is used")
        if equal_before_str_pos != str_prefix_pos - 1:
            logger.error(f"'=' must be immediately before '{STR_MARK}' in {param_string}")
            raise SensiSyntaxError(f"'=' must be immediately before '{STR_MARK}' when '{STR_MARK}' is used")
        # Split using the '=' immediately before 'STR_MARK'
        syntax = param_string[:equal_before_str_pos].strip()
        value = param_string[equal_before_str_pos + 1:].strip()
        value = value[len(STR_MARK):].strip()
    else:
        # STR_MARK not present
        # Find the last '=' character
        equal_pos = param_string.rfind('=')
        syntax = param_string[:equal_pos].strip()
        value = param_string[equal_pos + 1:].strip()

    syntax = syntax.strip('"').strip()
    value = value.strip('"').strip()

    logger.debug(f"Extracted syntax: {syntax}, value: {value}")
    return syntax, value


def extract_target_column(param_string):
    """Extracts column from param_string if param_string contains
    [ and ends with ]

    Args:
        param_string (str): string to be parsed

    Raises:
        SensiSyntaxError: if param_string does not contain [ and ends with ]

    Returns:
        tuple: (syntax (str), column (str))
    """
    logger.info(f"Extracting target column from {param_string}")
    param_string = param_string.strip('"').strip()

    if not "[" in param_string or not param_string.endswith("]"):
        logger.error(f'Incorrect syntax in param. Unable to find "[" or "]" in {param_string}')
        raise SensiSyntaxError('Incorrect syntax in param. Unable to find "[" or "]"')

    logger.debug(f"Extracting target column from {param_string}")
    right_quote_position = param_string.rindex("]")
    left_quote_position = param_string.rindex("[")
    syntax = param_string[:left_quote_position].strip('"').strip()
    column = param_string[left_quote_position + 1 : right_quote_position].strip()

    if column == "":
        logger.error(f"Incorrect input syntax. Column cannot be empty")
        raise SensiSyntaxError("Incorrect input syntax. Column cannot be empty")

    logger.debug(f"Returned {syntax} and {column}.")
    return syntax, column


def parse_param(input_syntax):
    """Parses input syntax and returns Syntax object

    Args:
        input_syntax (str): input syntax

    Raises:
        SensiSyntaxError: if input_syntax is invalid

    Returns:
        Syntax: Syntax object
    """
    logger.info(f"Parsing param: {input_syntax}")

    if not input_syntax:
        logger.error("Empty input_syntax parameter passed to the parse_param function.")
        raise SensiSyntaxError("Empty input_syntax in parse_param function")

    logger.debug(f"Extracting syntax and value from {input_syntax}")
    param_string, param_value = extract_value_from_equal(input_syntax)

    # Check if param_string contains FILE_MARK
    if not FILE_MARK in param_string:
        logger.debug(f"param_string does not contain {FILE_MARK}.")
        logger.debug(f"Returning Syntax object with expression: {param_string}, value: {param_value}")
        return Syntax(expression=param_string, value=param_value)

    logger.debug(f"Input syntax contains {FILE_MARK}.")

    # Remove FILE_MARK from param_string
    param_string = param_string.replace(FILE_MARK, "").strip()

    logger.debug(f"Checking if param_string contains condition")
    # Checks if '.where' exists in param_string
    if ".where" in param_string:
        logger.debug(f".where exists in param_string.")
        if param_string.count(".where") > 1:
            logger.error(f'Incorrect input_syntax. Multiple ".where" in {param_string}')
            raise SensiSyntaxError('Incorrect input_syntax. Multiple ".where"')
        param_expression, param_condition = param_string.split(".where")
    else:
        logger.debug(f".where does not exist in param_string.")
        param_expression, param_condition = param_string, ""

    # Gets the column in the param_expressions
    logger.debug(f"Extracting target column from {param_expression}")
    param_expression, param_col = extract_target_column(param_expression)

    if "eco" in param_expression and "driver" in param_expression:
        # Construct the query for input file extraction under eco and driver
        logger.debug(f"Extracting economy from {param_expression}")
        eco_pattern = ""
        if re.search(r"eco_\d+\.", param_expression):
            eco_pattern = r"eco_\d+\."
            eco = re.search(r"eco_\d+(?=\.)", param_expression).group()  # Gets the 123 from "eco_123."
        elif re.search(r"eco\[\w+?\]\.", param_expression):
            eco_pattern = r"eco\[\w+?\]\."
            eco = re.search(r"(?<=eco\[)\w+(?=\]\.)", param_expression).group()  # Gets the EUR from "eco[EUR]."
        else:
            raise SensiSyntaxError("Unable to find a valid eco in the expression")

        logger.debug(f"Extracting driver from {param_expression}")
        driver_pattern = ""
        if re.search(r"driver_\d+\.", param_expression):
            driver_pattern = r"driver_\d+\."
            driver = re.search(r"driver_\d+(?=\.)", param_expression).group()  # Gets the 123 from "driver_123."
        elif re.search(r"driver\[\w+?\]\.", param_expression):
            driver_pattern = r"driver\[\w+?\]\."
            driver = re.search(r"(?<=driver\[)\w+(?=\]\.)", param_expression).group()  # Gets the IR from "driver[IR]"
        else:
            raise SensiSyntaxError("Unable to find a valid driver in the expression")

        # Remove eco and driver from param_expression
        param_expression = re.sub(eco_pattern, "", param_expression)
        param_expression = re.sub(driver_pattern, "", param_expression)

        result = (
            "$"
            + (f"..*['{eco}']" if "eco" in eco else f"..*[@.name is '{eco}']")
            + (f"..*['{driver}']" if "driver" in driver else f"..*[@.name is '{driver}']")
            + f".{param_expression}.filename"
        )
    else:
        # Construct the query for input file extraction under sensi_1
        result = f"$.framework.sensi_1.{param_expression}.filename"
    logger.debug(f"Constructed query for input file extraction: {result}")
    logger.debug(f"Returning Syntax object with expression: {result}, value: {param_value}, column: {param_col}, condition: {param_condition}")
    return Syntax(result, param_col, param_condition, param_value)


def select_with_column_and_row(dataframe, column=None, row=None):
    """Selects a column and row from a dataframe

    Args:
        dataframe (pd.dataframe): dataframe to select from
        column (str, optional): column to select. Defaults to None.
        row (str, optional): row to select. Defaults to None.

    Raises:
        SensiSyntaxError: if any of the queries fail

    Returns:
        pd.dataframe: selected dataframe
    """
    logger.debug(f"Selecting column: {column} and row: {row} from dataframe")
    if dataframe is None or dataframe.empty:
        return dataframe

    # Column Selection
    if column:
        column = column.strip()
        if column.isdigit():
            col_index = int(column) - 1
            if col_index < 0 or col_index >= len(dataframe.columns):
                logger.error(f"Column index out of range: {column}")
                raise SensiSyntaxError(f"Column index out of range: {column}")
            dataframe = dataframe.iloc[:, [col_index]]
        elif column.startswith("'") and column.endswith("'"):
            column = column.strip("'")
            if column not in dataframe.columns:
                logger.error(f"Column not found: {column}")
                raise SensiSyntaxError(f"Column not found: {column}")
            dataframe = dataframe[[column]]
        elif column != "*":
            logger.error(f"Invalid column: {column}")
            raise SensiSyntaxError(f"Invalid column: {column}")

    # Row Selection
    if row:
        row = row.strip()
        if row.isdigit():
            row_index = int(row) - 1
            if row_index < 0 or row_index >= len(dataframe):
                logger.error(f"Row index out of range: {row}")
                raise SensiSyntaxError(f"Row index out of range: {row}")
            dataframe = dataframe.iloc[[row_index], :]
        elif row.startswith("'") and row.endswith("'"):
            row = row.strip("'")
            if row not in dataframe.index:
                logger.error(f"Row not found: {row}")
                raise SensiSyntaxError(f"Row not found: {row}")
            dataframe = dataframe.loc[[row]]
        elif row != "*":
            logger.error(f"Invalid row: {row}")
            raise SensiSyntaxError(f"Invalid row: {row}")

    return dataframe


def get_selection_from_dataframe(selection, dataframe):
    """Gets the selection from the dataframe

    Args:
        selection (str): selection to get
        dataframe (pd.dataframe): dataframe to get selection from

    Raises:
        SensiSyntaxError: if selection is invalid

    Returns:
        pd.dataframe: selected dataframe
    """
    logger.debug(f"Getting selection from dataframe: {selection}")
    if dataframe is None or dataframe.empty:
        return dataframe

    selection = selection.strip().strip("[]")
    if "," in selection:
        if selection.count(",") > 1:
            logger.error(f"Invalid selection: {selection}")
            raise SensiSyntaxError("Invalid selection")
        column, row = map(str.strip, selection.split(","))
    else:
        column, row = selection, None

    try:
        return select_with_column_and_row(dataframe, column, row)
    except SensiSyntaxError as e:
        logger.error(f"Unable to get selection from dataframe: {e}")
        raise SensiSyntaxError("Unable to get selection from dataframe")


def convert_value_to_true_type(value):
    """Parses the value

    Args:
        value (str): value to parse

    Returns:
        str, float, bool, None: parsed value
    """
    logger.debug(f"Parsing value: {value}")

    if value is None:
        logger.debug("Value is None")
        return None

    value = str(value).strip().strip('"').strip("'")

    # Check for boolean values
    if value.lower() in {"true", "false"}:
        logger.debug("Value is boolean")
        return value.lower() == "true"

    # Check for integer
    try:
        int_value = int(value)
        logger.debug("Value is integer")
        return f"{int_value}.0"
    except ValueError:
        pass

    # Check for float
    try:
        float_value = float(value)
        logger.debug("Value is float")
        return str(float_value)
    except ValueError:
        pass

    # Default to string
    return value


def apply_condition_vectorized(column, operation, values):
    """Apply condition using vectorized operations.
    
    Args:
        column (pd.Series): column to apply condition on
        operation (str): operation to use for comparison
        values (str): values to compare with

    Raises:
        SensiSyntaxError: if operation is invalid

    Returns:
        pd.Series: series of boolean values
    """
    logger.debug(f"Applying vectorized condition: {column} {operation} {values}")
    condition_series = pd.Series([False] * len(column), index=column.index)

    # Normalize the values
    values = [convert_value_to_true_type(v.strip()) for v in values.split(",")]
    # Normalize the column
    normalized_column = column.apply(convert_value_to_true_type)

    if operation in {"==", "!="}:
        if operation == "==":
            condition_series = normalized_column.isin(values)
        elif operation == "!=":
            condition_series = ~normalized_column.isin(values)
    elif operation in {">", ">=", "<", "<="}:
        # For relational operations, expect a single value
        if len(values) != 1:
            logger.error(f"Multiple values are not allowed with operation '{operation}'")
            raise SensiSyntaxError(f"Multiple values are not allowed with operation '{operation}'")
        value = values[0]

        # Apply the operation using string comparison
        if operation == ">":
            condition_series = normalized_column > value
        elif operation == ">=":
            condition_series = normalized_column >= value
        elif operation == "<":
            condition_series = normalized_column < value
        elif operation == "<=":
            condition_series = normalized_column <= value
    else:
        logger.error(f"Unsupported operation: {operation}")
        raise SensiSyntaxError(f"Unsupported operation: {operation}")

    # Fill NaN values resulting from comparisons with False
    return condition_series.fillna(False)


def select_from_dataframe(condition, operation, dataframe):
    """Selects from the dataframe based on the condition and operation

    Args:
        condition (str): condition to select
        operation (str): operation to select
        dataframe (pd.dataframe): dataframe to select from

    Raises:
        SensiSyntaxError: if condition or operation is invalid

    Returns:
        pd.Series: boolean series indicating the rows satisfying the condition
    """
    logger.info(f"Selecting from dataframe: {condition}, {operation}")
    try:
        lvalue, rvalue = map(str.strip, condition.split(operation))
    except ValueError:
        logger.error(f"Invalid condition: {condition}")
        raise SensiSyntaxError("Condition must be in the form of 'lvalue operation rvalue'")

    if not lvalue:
        logger.error(f"lvalue from condition is empty: {condition}")
        raise SensiSyntaxError("lvalue from condition is empty")

    selected_df = get_selection_from_dataframe(lvalue, dataframe)
    if selected_df is not None and not selected_df.empty:
        if not rvalue:
            logger.error(f"rvalue from condition is empty: {condition}")
            raise SensiSyntaxError("rvalue from condition is empty")

        # Apply the condition to the selected column
        column = selected_df.columns[0]
        selected_column = selected_df[column]
        return apply_condition_vectorized(selected_column, operation, rvalue)
    else:
        logger.warning(f"Selection from dataframe using condition '{condition}' is empty")
        return pd.Series([False] * len(dataframe), index=dataframe.index)


def interpret_condition(condition, dataframe):
    """Interprets the condition and returns a boolean Series

    Args:
        condition (str): condition to interpret
        dataframe (pd.dataframe): dataframe to interpret condition from

    Raises:
        SensiSyntaxError: if condition is invalid

    Returns:
        pd.Series: A boolean Series indicating which rows satisfy the condition
    """
    logger.info(f"Interpreting condition: {condition}")
    if not condition.strip():
        return pd.Series([True] * len(dataframe), index=dataframe.index)

    operators = ["==", "!=", ">=", ">", "<=", "<"]
    for op in operators:
        if op in condition:
            condition_series = select_from_dataframe(condition, op, dataframe)
            return condition_series
    else:
        logger.error(f"Incorrect condition '{condition}'.")
        raise SensiSyntaxError(f"'{condition}' is not a correct condition")


def apply_value_to_selection(dataframe, selected_indexes, selected_columns, value_to_apply):
    """Applies the value to the selected dataframe.

    Args:
        dataframe (pd.dataframe): The original dataframe.
        selected_indexes (pd.Index): Indexes of the selected rows.
        selected_columns (list): List of selected columns.
        value_to_apply (str): Value or operation to apply.

    Raises:
        SensiSyntaxError: if value is invalid or unable to apply value to selection
    """
    logger.debug(f"Applying value to selection: {value_to_apply}")

    value = value_to_apply.strip()
    if value.startswith('(') and value.endswith(')'):
        # It's an operation
        operation_str = value[1:-1].strip()
        if operation_str[0] in {"+", "-", "*", "/"}:
            operation = operation_str[0]
            operand_str = operation_str[1:]
        else:
            # Default operation is addition
            operation = "+"
            operand_str = operation_str

        try:
            operand = float(operand_str.replace(",", "."))
        except ValueError:
            logger.error(f"Invalid operand value: {operand_str}")
            raise SensiSyntaxError(f"Invalid operand value: {operand_str}")

        # Apply the operation to the selected data
        for column in selected_columns:
            selected_series = dataframe.loc[selected_indexes, column]

            def convert_to_mpf(val):
                """Converts the value to mpf if possible, otherwise returns None."""
                try:
                    return mp.mpf(val)
                except (ValueError, TypeError):
                    return None # Return None for non-numeric values

            numeric_selected_series = selected_series.apply(convert_to_mpf)

            if numeric_selected_series.isnull().any():
                non_numeric_values = selected_series[numeric_selected_series.isnull()]
                logger.error(f"Non-numeric values encountered in column '{column}': {non_numeric_values.tolist()}")
                raise SensiSyntaxError(f"Non-numeric values encountered in column '{column}': {non_numeric_values.tolist()}")

            def apply_operation(val):
                """Applies the operation to the value."""
                if operation == "+":
                    result = val + operand
                elif operation == "-":
                    result = val - operand
                elif operation == "*":
                    result = val * operand
                elif operation == "/":
                    result = val / operand
                else:
                    raise SensiSyntaxError(f"Unsupported operation: {operation}")
                return mp.nstr(result, mp.dps)

            dataframe.loc[selected_indexes, column] = numeric_selected_series.apply(apply_operation)
    else:
        # Direct value assignment
        converted_value = convert_value_to_true_type(value)
        dataframe.loc[selected_indexes, selected_columns] = converted_value


# Cache for file reads
file_cache = {}

def read_file_cached(file_path, col_sep=';', dec_sep='.'):
    """Read and cache the CSV file.
    
    Args:
        file_path (str): path to the file
        col_sep (str, optional): column separator. Defaults to ','.
        dec_sep (str, optional): decimal separator. Defaults to '.'.

    Returns:
        pd.dataframe: dataframe read from the file
    """
    if file_path not in file_cache:
        logger.debug(f"Reading and caching file: {file_path}")
        converters = {i: str for i in range(100)} # Assume max 100 columns
        df = pd.read_csv(file_path, sep=col_sep, decimal=dec_sep, header=None, converters=converters)

        # Handle index base on the first cell
        first_cell = df.iloc[0, 0]
        if first_cell == "":
            df.set_index(df.columns[0], inplace=True, drop=True)
        else:
            df.reset_index(drop=True, inplace=True)

        df.columns = df.iloc[0]
        df.drop(df.index[0], inplace=True)

        file_cache[file_path] = df
    return file_cache[file_path]

def clear_file_cache():
    """Clear the file cache."""
    file_cache.clear()


# Cache for modified dataframes
modified_dataframes_cache = {}

def save_all_modified_dataframes(settings_json):
    """
    Saves all modified DataFrames in the modified_dataframes_cache to their respective files.

    Args:
        settings_json (dict): The settings JSON containing separator information.
    """
    logger.info("Saving all modified DataFrames to their respective files.")
    for file_path, df in modified_dataframes_cache.items():
        try:
            seps = settings_json.get("gen_param", {}).get("input_format", {})
            col_sep = seps.get("col_sep", ',')
            temp_path = f"{file_path}.tmp"
            logger.debug(f"Saving DataFrame to temporary file: {temp_path}")
            if df.index.name is not None:
                df.to_csv(temp_path, sep=col_sep, index=True, index_label='', float_format="%.18g")
            else:
                df.to_csv(temp_path, sep=col_sep, index=False, float_format="%.18g")
            os.replace(temp_path, file_path)
            logger.debug(f"Replaced original file with updated file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            raise SensiSyntaxError(f"Failed to save file {file_path}: {e}")

    clear_modified_dataframes_cache()

def clear_modified_dataframes_cache():
    """Clear the modified dataframes cache."""
    modified_dataframes_cache.clear()


def apply_syntax_to_file(input_path, syntax, settings_json):
    """Applies the syntax to the input file

    Args:
        input_path (str): path to the input file
        syntax (Syntax): syntax to apply
        settings_json (dict): settings to use

    Raises:
        SensiSyntaxError: if failed to apply syntax to file

    Returns:
        boolean: True if syntax was applied successfully, False otherwise
    """
    logger.info(f"Applying syntax to file: {input_path}")
    try:
        if not input_path:
            raise SensiSyntaxError("No input file specified.")
        if not syntax:
            raise SensiSyntaxError("No syntax specified.")
        if not syntax.col:
            raise SensiSyntaxError("No column specified.")
        if syntax.value is None:
            raise SensiSyntaxError("No value specified.")
        if not settings_json:
            raise SensiSyntaxError("No settings specified.")

        # Get separators from settings.json
        seps = settings_json.get("gen_param", {}).get("input_format", {})
        dec_sep = seps.get("dec_sep", '.')
        col_sep = seps.get("col_sep", ';')

        if not os.path.isfile(input_path):
            raise SensiSyntaxError(f"Input file not found: {input_path}")

        original_df = read_file_cached(input_path, col_sep=col_sep, dec_sep=dec_sep)

        # Get the dataframe from the cache or create a new one
        if input_path in modified_dataframes_cache:
            df = modified_dataframes_cache[input_path]
        else:
            df = original_df.copy()
            modified_dataframes_cache[input_path] = df

        # Apply conditions
        if syntax.condition:
            logger.debug(f"Applying condition: {syntax.condition}")
            condition = syntax.condition.strip("()")
            or_conditions = [cond.strip() for cond in condition.split("||") if cond.strip()]
            logger.debug(f"OR conditions: {or_conditions}")

            combined_condition = pd.Series(False, index=df.index) # Initialize with False for OR conditions
            for or_cond in or_conditions:
                and_conditions = [cond.strip() for cond in or_cond.split("&&") if cond.strip()]
                logger.debug(f"AND conditions: {and_conditions}")

                and_combined = pd.Series(True, index=df.index) # Initialize with True for AND conditions
                for and_cond in and_conditions:
                    condition_result = interpret_condition(and_cond, df)
                    and_combined &= condition_result

                # Combine with OR condition
                combined_condition |= and_combined

            # Select rows satisfying the combined condition
            selected_indexes = combined_condition[combined_condition].index
            df_selected = df.loc[selected_indexes]
            logger.debug(f"Total selected indexes after conditions: {len(selected_indexes)}")
        else:
            df_selected = df.copy()

        # Get the selection from the dataframe
        try:
            selected_df = get_selection_from_dataframe(syntax.col, df_selected)
            if selected_df is not None and not selected_df.empty:
                selected_columns = selected_df.columns.tolist()
                selected_indexes = selected_df.index
                logger.debug(f"Total selected indexes after selection: {len(selected_indexes)}")
            else:
                logger.warning(f"Selection from dataframe using column '{syntax.col}' is empty")
                return True
        except SensiSyntaxError as err:
            logger.error(f"{err} in file {input_path}")
            raise err

        # Apply value to the selection
        apply_value_to_selection(df, selected_indexes, selected_columns, syntax.value)

        modified_dataframes_cache[input_path] = df

        logger.info(f"Successfully applied syntax to file: {input_path}")
        return True

    except Exception as exc:
        logger.error(f"Failed to apply syntax to file: {input_path}: {exc}")
        temp_path = f"{input_path}.tmp"
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
