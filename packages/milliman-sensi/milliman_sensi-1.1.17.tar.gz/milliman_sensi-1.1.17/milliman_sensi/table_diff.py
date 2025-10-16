import hashlib
import logging
import os

import numpy as np
import pandas as pd
from deepdiff import DeepDiff
from deepdiff.operator import BaseOperator

import milliman_sensi.utility as util

logger = logging.getLogger(__name__)

# Paths to exclude from the results of the diff
PATHS_TO_EXCLUDE_FROM_DIFF = [
    "root['gen_param']['name']",
    "root['gen_param']['path']",
    "root['framework']['sensi_1']['name']",
    "root['framework']['sensi_1']['folder_id']",
]
# Fields to exclude from the results of the interpret_diff
FIELDS_TO_EXCLUDE_FROM_INTERPRET_DIFF = ["folder_id"]


class TableHandler:
    """Class to handle the table directory and settings.json file

    Attributes
    ----------
    env_dir : str
        The path to the table directory
    settings : dict
        The settings.json file as a dictionary
    data : dict
        A dictionary with all the csv files in the table and their paths
    """

    def __init__(self, env_dir):
        self.env_dir = env_dir
        self.settings = self._load_settings()
        self.data = self._load_data()

    def _load_settings(self):
        """Load the settings.json file"""
        settings_path = os.path.join(self.env_dir, "resources", "settings.json")
        logger.debug("Loading settings: %s", settings_path)
        settings_data = {}
        try:
            settings_data = util.read_json_file(settings_path)
            logger.debug("Settings loaded successfully")
        except (FileNotFoundError, ValueError):
            logger.exception(f"Error loading settings: {settings_path}")

        return settings_data

    def _load_data(self):
        """Create a dictionary with all the csv files in the table and their paths"""

        # TODO: Need to redo this part to be more generic and because file names are not unique
        data = {}
        for root, dirs, files in os.walk(self.env_dir):
            for file in files:
                if file.endswith(".csv"):
                    data[file] = os.path.join(root, file)
        return data


class CsvHashComparator(BaseOperator):
    """Class to compare the hashes of the csv files

    Attributes
    ----------
    base_settings : dict
        The settings.json file of the base table
    other_settings : dict
        The settings.json file of the other table
    base_env_dir : str
        The path to the base table directory
    other_env_dir : str
        The path to the other table directory

    Methods
    -------
    give_up_diffing(level, diff_instance)
        Compare the hashes of the csv files
    hash_file(filename, buffer_size=8192, hash_algorithm=hashlib.sha256)
        Hash the csv file
    """

    def __init__(self, base_settings, other_settings, base_env_dir=None, other_env_dir=None):
        # super().__init__(types=[str, type(None)])
        super().__init__(regex_paths=[r".*\['filename'\]", r".*\['format'\]"])
        self.base_settings = base_settings
        self.other_settings = other_settings
        self.base_env_dir = base_env_dir if base_env_dir is not None else os.getcwd()
        self.other_env_dir = other_env_dir if other_env_dir is not None else os.getcwd()

    def give_up_diffing(self, level, diff_instance):
        base_filename = level.t1
        other_filename = level.t2
        if base_filename is None and other_filename is None:
            # If both filenames are None, no need to compare the hashes
            logger.debug("Giving up diffing because both filenames are None in %s", level.path())
            return True

        logger.info("Comparing hashes of csv files: %s vs %s", base_filename, other_filename)
        path = level.path().replace("root", "$")
        path = path.replace("['", ".")
        path = path.replace("']", "")

        base_file_path = base_filename_hash = None
        try:
            base_file_path = util.get_input_file_path(self.base_settings, path, self.base_env_dir)
            base_filename_hash = self.hash_file(base_file_path)
        except RuntimeError:
            base_filename_hash = "FILE_NOT_FOUND"
        hash_cmp_msg = f"{base_filename} hash: {base_filename_hash}"

        other_file_path = other_filename_hash = None
        try:
            other_file_path = util.get_input_file_path(self.other_settings, path, self.other_env_dir)
            other_filename_hash = self.hash_file(other_file_path)
        except RuntimeError:
            other_filename_hash = "FILE_NOT_FOUND"
        hash_cmp_msg = f"{hash_cmp_msg} => {other_filename} hash: {other_filename_hash}"

        if (
            base_filename_hash in ["FILE_NOT_FOUND", "ERROR_HASHING_FILE"]
            or other_filename_hash in ["FILE_NOT_FOUND", "ERROR_HASHING_FILE"]
            or base_filename_hash != other_filename_hash
        ):
            diff_instance.custom_report_result("csv_hash_mismatch", level, hash_cmp_msg)

        return False

    @staticmethod
    def hash_file(filename, buffer_size=8192, hash_algorithm=hashlib.sha256):
        logger.debug("Hashing file: %s", filename)
        try:
            file_hash = hash_algorithm()
            with open(filename, "rb") as f:
                while True:
                    data_chunk = f.read(buffer_size)
                    if not data_chunk:
                        break
                    data_chunk = data_chunk.replace(b"\r\n", b"\n")  # Normalize line endings
                    file_hash.update(data_chunk)
            logger.debug("File hashed successfully")
            return file_hash.hexdigest()
        except (IOError, FileNotFoundError):
            logger.exception(f"Error hashing file {filename}")
            return "ERROR_HASHING_FILE"


class TableDiff:
    """Class to compare two tables

    Attributes
    ----------
    comparer : deepdiff.DeepDiff
        The comparer to use to compare the settings.json files

    Methods
    -------
    compare(table_1, table_2, compare_csv_files=True, interpret_diff=True)
        Compare the two tables after loading the settings.json files
    """

    def __init__(self, comparer=DeepDiff):
        self.comparer = comparer

    def _filter_diff(self, diff, paths_to_exclude=None):
        """
        Filter out the fields that are not needed from the diff.
        """
        logger.debug("Filtering the diff based on paths to exclude: %s", paths_to_exclude)
        if paths_to_exclude:
            for field in paths_to_exclude:
                for change_type in diff:
                    if field in diff[change_type]:
                        del diff[change_type][field]

        return diff

    def _merge_iterable_changes(self, diff):
        """
        Merge the changes in the iterable items.
        """
        logger.debug("Merging changes in the iterable items")
        for change_type in ("iterable_item_added", "iterable_item_removed"):
            if change_type in diff:
                change_dict = diff[change_type]
                merged_changes = {}

                for path, value in change_dict.items():
                    # Split the path to extract the root/index
                    root, index = path.rsplit("[", 1)
                    index = index[:-1]

                    if root not in merged_changes:
                        merged_changes[root] = {}
                    merged_changes[root][index] = value

                diff[change_type] = merged_changes

        return diff

    def _compare_settings_files(
        self, base_table, other_table, compare_csv_files=True, paths_to_exclude=PATHS_TO_EXCLUDE_FROM_DIFF
    ):
        """
        Compare the settings.json files of the two tables.
        """
        logger.info("Comparing settings.files: %s vs %s", base_table.env_dir, other_table.env_dir)
        logger.debug("Using comparer: %s and compare_csv_files: %s", self.comparer, compare_csv_files)
        try:
            diffs = self.comparer(
                base_table.settings,
                other_table.settings,
                ignore_order=True,
                custom_operators=[
                    CsvHashComparator(
                        base_table.settings, other_table.settings, base_table.env_dir, other_table.env_dir
                    )
                ]
                if compare_csv_files
                else [],
                verbose_level=2,
            ).to_dict()
            logger.debug("Settings files compared successfully")

            # Merge the changes in the iterable items
            diffs = self._merge_iterable_changes(diffs)
            if paths_to_exclude:
                # Filter out the fields that are not needed from the diff.
                diffs = self._filter_diff(diffs, paths_to_exclude)

        except Exception as exc:
            logger.exception("Error comparing settings.files")
            raise RuntimeError("Error comparing settings.files") from exc

        return diffs

    def _extract_paths_from_settings(self, settings_data, parent_path=""):
        """
        Extract all the paths from the settings.json file.
        """
        logger.debug("Extracting paths from settings from path: %s", parent_path)
        paths = []
        if isinstance(settings_data, dict):
            # paths.extend([parent_path])
            for key, value in settings_data.items():
                current_path = f"{parent_path}['{key}']" if parent_path else f"root['{key}']"
                paths.extend(self._extract_paths_from_settings(value, current_path))
        else:
            paths.append(parent_path)

        return paths

    def _get_merged_paths_of_settings(self, base_settings_data, other_settings_data):
        """
        Get the paths that are in both settings.json files.
        """
        logger.debug("Merging paths from settings files %s and %s", base_settings_data, other_settings_data)
        base_paths = self._extract_paths_from_settings(base_settings_data)
        other_paths = self._extract_paths_from_settings(other_settings_data)

        hierarchy = {}
        for path in base_paths + other_paths:
            keys = path.strip("root").split("']['")
            d = hierarchy
            for key in keys:
                key = key.strip("[']")
                d = d.setdefault(key, {})

        merged_paths = []

        def flatten(d, current_path):
            if not d:
                merged_paths.append(current_path)
                return
            for key, value in d.items():
                new_path = f"{current_path}['{key}']" if current_path else f"['{key}']"
                flatten(value, new_path)

        flatten(hierarchy, "root")

        return merged_paths

    def _filter_paths(self, paths, field_filters):
        """
        Filter out the paths that are not needed.
        """
        logger.debug("Filtering paths based on field filters: %s", field_filters)
        filtered_paths = []

        if field_filters:
            for path in paths:
                if any(field in path for field in field_filters):
                    continue
                filtered_paths.append(path)
        else:
            filtered_paths = paths

        return filtered_paths

    def _get_value_from_path(self, data, path):
        """
        Get the value from a path in the settings.json file.
        """
        logger.debug("Getting value from path: %s", path)
        if not path.startswith("root"):
            path = "root" + path
        path = path.replace("root", "")
        path = path.replace("[", "")
        path = path.replace("'", "")
        path = path.replace('"', "")
        if path.endswith("]"):
            path = path.split("]")[:-1]

        for key in path:
            if isinstance(data, list):
                data = data[key]
            else:
                data = data.get(key, None)
            if data is None:
                break
        return data

    def _interpret_diff(
        self, base_settings, other_settings, diff, fields_to_exclude=FIELDS_TO_EXCLUDE_FROM_INTERPRET_DIFF
    ):
        """
        Interpret the diff of the settings.json files.
        """
        logger.debug("Interpreting the diff to determine the changes")

        # Get the paths that are in both settings.json files.
        base_and_other_settings_paths = self._get_merged_paths_of_settings(base_settings, other_settings)
        # Filter out the paths that are not needed.
        base_and_other_settings_paths = self._filter_paths(base_and_other_settings_paths, fields_to_exclude)

        interpret_diff = {
            "Type": [],
            "Name": [],
            "Base": [],
            "Other": [],
        }
        dict_item_added_list = list(diff.get("dictionary_item_added", {}).keys())
        dict_item_removed_list = list(diff.get("dictionary_item_removed", {}).keys())

        for path in base_and_other_settings_paths:
            csv_hash_mismatch = False
            if path in diff.get("csv_hash_mismatch", {}):
                # If path in csv_hash_mismatch, then insert two rows in the dataframe
                # First row is for the filename (Type: None, Name: path ends with .filename)
                # Second row is for the hash (Type: FILE_MARK, Name: path does not end with .filename)
                base_filename, base_hash, other_filename, other_hash = (
                    diff["csv_hash_mismatch"][path].replace("hash:", "=>").split(" => ")
                )
                interpret_diff["Base"] += [None if base_filename == "None" else base_filename, base_hash]
                interpret_diff["Other"] += [None if other_filename == "None" else other_filename, other_hash]
                csv_hash_mismatch = True

            elif path in diff.get("values_changed", {}) or path in diff.get("type_changes", {}):
                diff_type = "values_changed" if path in diff.get("values_changed", {}) else "type_changes"
                interpret_diff["Base"].append(diff[diff_type][path]["old_value"])
                interpret_diff["Other"].append(diff[diff_type][path]["new_value"])

            elif any(path.startswith(field) for field in dict_item_added_list + dict_item_removed_list):
                # dictionary_item_added has intermediate path to group the changes together
                # For example: root['framework']['sensi_1']['param']['seed'] while the paths that we get from the
                # _get_merged_paths_of_settings function are like root['framework']['sensi_1']['param']['seed']['name']
                # and root['framework']['sensi_1']['param']['seed']['driver_2']['name']
                interpret_diff["Base"].append(self._get_value_from_path(base_settings, path))
                interpret_diff["Other"].append(self._get_value_from_path(other_settings, path))

            elif path in diff.get("iterable_item_added", {}) or path in diff.get("iterable_item_removed", {}):
                interpret_diff["Base"].append(self._get_value_from_path(base_settings, path))
                interpret_diff["Other"].append(self._get_value_from_path(other_settings, path))

            else:
                # If the path is not in the diff, then continue
                continue

            path = path.replace("root", "")
            path = path.replace("[", "")
            path = path.replace("'", "")
            path = path.replace('"', "")
            if path.endswith("]"):
                path = path.split("]")[:-1]

            if path[0] == "framework" and path[1].startswith("sensi_"):  # Ignore framework and sensi_*
                path = path[2:]
            # if path[0].startswith("eco_") and path[1].startswith("driver_"): # Concatenate eco_* and driver_*
            #     path = [path[0] + "." + path[1]] + path[2:]

            interpret_diff["Type"].append(None)
            interpret_diff["Name"].append(".".join(path))
            if csv_hash_mismatch:
                # If path in csv_hash_mismatch, then two rows were inserted in the dataframe
                interpret_diff["Type"].append(util.FILE_MARK)
                interpret_diff["Name"].append(".".join(path[:-1]))

        df = pd.DataFrame(interpret_diff).astype({"Type": "object", "Name": str, "Base": "object", "Other": "object"})

        # Set column names
        base_name = other_name = None
        if base_settings.get("gen_param", {}).get("name") and base_settings.get("framework", {}).get("sensi_1", {}).get(
            "name"
        ):
            base_name = base_settings["gen_param"]["name"] + "/" + base_settings["framework"]["sensi_1"]["name"]
        if other_settings.get("gen_param", {}).get("name") and other_settings.get("framework", {}).get(
            "sensi_1", {}
        ).get("name"):
            other_name = other_settings["gen_param"]["name"] + "/" + other_settings["framework"]["sensi_1"]["name"]
        if base_name and other_name:
            df.rename(columns={"Base": base_name, "Other": other_name}, inplace=True)

        return df

    def compare(self, table_1, table_2, compare_csv_files=True, interpret_diff=True):
        """
        Compare the two tables after loading the settings.json files.
        """
        logger.info("Comparing tables: %s vs %s", table_1, table_2)
        # Load the table directories and settings.json files
        table_1 = TableHandler(table_1)
        table_2 = TableHandler(table_2)

        if not table_1.settings or not table_2.settings:
            logger.error("Error loading tables")
            return None

        # Clear the query cache
        util.clear_query_cache()

        try:
            # Compare the settings.json files
            settings_diff = self._compare_settings_files(table_1, table_2, compare_csv_files)
            logger.debug("Tables compared successfully")
            if not interpret_diff:
                return settings_diff

            # Interpret the diff to determine the changes
            interpreted_diff = self._interpret_diff(table_1.settings, table_2.settings, settings_diff)
            logger.debug("Diff interpreted successfully")
            return interpreted_diff
        except RuntimeError:
            logger.exception("Error comparing tables")
            return None
