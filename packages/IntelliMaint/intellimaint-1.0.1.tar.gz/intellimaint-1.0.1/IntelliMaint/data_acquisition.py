#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Analysis core class definition

Author: rameshbk
Last modified: rachana, Aug 12th, 2025
"""
import os
import glob
import pandas as pd
import numpy as np
import scipy.io
import re
import logging
from IntelliMaint.utils import Utils

class DataAcquisition:
    """
    Manage flexible data acquisition from CSV, TXT, or MAT files in a directory.

    Args:
        config (dict): Configuration dictionary containing:
            - DATA_DIR_PATH (str): Directory path containing data files.
            - file_pattern (str): Filename pattern for filtering files (e.g., '*.csv', '*.mat', '200*').
            - delimiter (str, optional): Delimiter for CSV/TXT files. Defaults to ','.
            - header (int or None, optional): Header row index for CSV files. Defaults to None.
            - skiprows (int, optional): Rows to skip in CSV files. Defaults to 0.
            - mat_variable (str, optional): Variable name to extract from .mat files if specified.

    Uses Config Parameters:
        DATA_DIR_PATH (str): Directory containing the data files.
        file_pattern (str): File matching pattern for scanning files.
        delimiter (str): Delimiter for CSV loading.
        header (int or None): Header row for CSV loading.
        skiprows (int): Rows skipped for CSV loading.
        mat_variable (str or None): Target variable name in .mat files.

    Returns:
        None
    """

    def __init__(self, config, verbose=False):
        """
        Initialize DataAcquisition with a single flexible config.

        Args:
            config (dict): Configurations like:
                - DATA_DIR_PATH (str): Directory containing data files.
                - file_pattern (str): Pattern for filenames (e.g., "*.csv", "*.mat", "200*").
                - delimiter (str, optional): Delimiter for CSV files (default: ',').
                - header (int or None, optional): Row number for CSV headers (default: None).
                - skiprows (int, optional): Rows to skip in CSV files (default: 0).
                - mat_variable (str, optional): Variable to extract from .mat files (if needed).
        Returns:
            None
        """
        self.config = {
            "DATA_DIR_PATH": config.get("DATA_DIR_PATH", "."),
            "file_pattern": config.get("file_pattern", "*"),  # Allow files with no extension
            "delimiter": config.get("delimiter", ","),
            "header": config.get("header", None),
            "skiprows": config.get("skiprows", 0),
            "mat_variable": config.get("mat_variable", None)  # Used for .mat
        }

        self.verbose = verbose

        ut = Utils(verbose=verbose)
        self.logger = ut.get_logger(self.__class__.__name__)
        self._print_debug = ut.print_debug

        if self.verbose:
            print(f"[DEBUG] DataAcquisition initialized with config: {self.config}")
        self.logger.info(f"Initialized DataAcquisition with config: {self.config}")
        

    def get_file_list(self):
        """
        Get a sorted list of files matching the configured pattern from the data directory.

        Args:
            None

        Uses Config Parameters:
            DATA_DIR_PATH (str): Directory to search for files.
            file_pattern (str): Glob pattern to match files.

        Returns:
            list of str: Sorted list of matching file paths.

        Raises:
            RuntimeError: If DATA_DIR_PATH is actually a file, not a directory.
            FileNotFoundError: If no files match the pattern.
        """
        path = self.config["DATA_DIR_PATH"]
        pattern = self.config["file_pattern"]

        self.logger.info(f"Searching for files in '{path}' with pattern '{pattern}'")

        # Check if path is the path to a folder
        if os.path.isfile(path):
            msg = "The path should point to a folder."
            self.logger.error(msg)
            raise RuntimeError(msg)
        
        files = sorted(glob.glob(os.path.join(path, pattern)))

        if not files:
            msg = f"No files matching {pattern} found in {path}."
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        self.logger.info(f"Found {len(files)} file(s)")
        self._print_debug(f"Found files: {files}")
        return files

    def is_mat_file(self, file_path):
        """
        Determine if the given file is a MATLAB .mat file by attempting to load it.

        Args:
            file_path (str): Path to the file to check.

        Returns:
            bool: True if file can be loaded as .mat, False otherwise.
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension != ".mat":
            return False  # Quick check based on extension
        return True
        

        # try:
        #     scipy.io.loadmat(file_path)  # If successful, it's a .mat file
        #     self.logger.debug(f"{file_path} detected as .mat file")
        #     return True
        # except:
        #     self.logger.debug(f"{file_path} is not a .mat file")
        #     return False  # If loading fails, assume it's a CSV-like file

    def load_all_data(self):
        """
        Load data from all files matching the configured pattern, dynamically handling file types.

        Args:
            None

        Returns:
            dict: Keys are filenames, values are loaded data (pd.DataFrame for CSV; dict or np.array for .mat).
        """
        files = self.get_file_list()
        data = {}

        self.logger.info("Starting to load all files")
        for file in files:
            try:
                data[file] = self.load_file_data(file)
                self.logger.debug(f"Loaded file: {file}")
            except Exception as e:
                self.logger.exception(f"Skipping {file}: {e}")
        
        self.logger.info("All files loaded")
        return data

    def load_all_csv_data(self, files):
        """
        Load and concatenate all CSV or TXT files from a provided list.

        Args:
            files (list of str): List of CSV/TXT file paths to load.

        Uses Config Parameters:
            delimiter (str): Delimiter for CSV parsing.
            header (int or None): Header row for CSV parsing.
            skiprows (int): Rows to skip in CSV files.

        Returns:
            pd.DataFrame or None: Concatenated DataFrame of all CSVs, or None if no files loaded.
        """
        dataframes = []
        for file in files:
            try:
                df = pd.read_csv(
                    file,
                    sep=self.config["delimiter"],
                    header=self.config["header"],
                    skiprows=self.config["skiprows"]
                )
                self.logger.debug(f"Loaded CSV {file} with shape {df.shape}")
                dataframes.append(df)
            except Exception as e:
                self.logger.exception(f"Skipping {file} due to error: {e}")
        self.logger.info("All files loaded")

        return pd.concat(dataframes, ignore_index=True) if dataframes else None

    def load_all_mat_data(self, files):
        """
        Load all MATLAB .mat files in the list, extracting specified variable or all variables.

        Args:
            files (list of str): List of .mat file paths to load.

        Uses Config Parameters:
            mat_variable (str or None): Name of variable to extract from .mat files.

        Returns:
            dict: Mapping from filename to dictionaries of variable arrays.
        """
        mat_data_dict = {}
        for file in files:
            try:
                mat_data = scipy.io.loadmat(file)
                available_vars = [key for key in mat_data.keys() if not key.startswith("__")]

                selected_vars = [self.config["mat_variable"]] if self.config["mat_variable"] in available_vars else available_vars

                if not selected_vars:
                    self.logger.warning(f"Warning: No valid variables found in {file}. Available: {available_vars}")
                    continue

                mat_data_dict[file] = {var: np.array(mat_data[var]) for var in selected_vars}

                self.logger.debug(f"Loaded MAT {file} with variables {selected_vars}")
            except Exception as e:
                self.logger.exception(f"Skipping {file} due to error: {e}")
        self.logger.info("All files loaded")

        return mat_data_dict

    def load_file_data(self, file_path):
        """
        Load data from a single file, dynamically detecting and reading as .mat or CSV format.

        Args:
            file_path (str): Full path to file.

        Uses Config Parameters:
            delimiter (str): CSV delimiter.
            header (int or None): CSV header row.
            skiprows (int): Rows to skip in CSV.
            mat_variable (str or None): Variable to extract from .mat files.

        Returns:
            pd.DataFrame or np.array or dict:
                - pd.DataFrame: For CSV or TXT files.
                - np.array: For specified variable extracted from .mat file.
                - dict: For all variables extracted from .mat if no variable specified.
        
        Raises:
            KeyError: If specified mat_variable not found in .mat file.
        """
        if self.is_mat_file(file_path):  # First, try as .mat file
            mat_data = scipy.io.loadmat(file_path)
            self.logger.debug(f"Loaded mat file {file_path}")
            if self.config["mat_variable"]:
                if self.config["mat_variable"] in mat_data:
                    arr = np.array(mat_data[self.config["mat_variable"]])
                    self.logger.debug(f"Extracted variable '{self.config['mat_variable']}' from MAT with shape {arr.shape}")
                    return arr
                else:
                    msg = f"Variable '{self.config['mat_variable']}' not found in {file_path}. Available: {list(mat_data.keys())}"
                    self.logger.error(msg)
                    raise KeyError(msg)
            else:
                return {k: np.array(mat_data[k]) for k in mat_data if not k.startswith("__")}

        else:  # If not .mat, assume CSV/TXT
            df = pd.read_csv(
                file_path,
                sep=self.config["delimiter"],
                header=self.config["header"],
                skiprows=self.config["skiprows"]
            )
            self._print_debug(f"Loaded csv/txt {file_path} with shape {df.shape}")
            return df
        
    def parse_date_from_filename(self, filename, date_patterns=None):
        """
        Extract date from a filename using configurable regex patterns and datetime formats.

        Args:
            filename (str): Filename to parse.
            date_patterns (list of tuples, optional):
                List of (regex_pattern (str), datetime_format (str)) to try for matching dates.
                Defaults to common date formats: YYYYMMDD, YYYY-MM-DD, and YYYY_MM_DD.

        Returns:
            pd.Timestamp or None: Parsed datetime object if extraction succeeds, else None.
        """
        basename = os.path.basename(filename)
        if date_patterns is None:
            date_patterns = [
                (r'(\d{8})', '%Y%m%d'),
                (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
                (r'(\d{4}_\d{2}_\d{2})', '%Y_%m_%d'),
            ]
        for regex, fmt in date_patterns:
            match = re.search(regex, basename)
            if match:
                date_str = match.group(1)
                try:
                    date_obj = pd.to_datetime(date_str, format=fmt)
                    self.logger.debug(f"Extracted date {date_obj} from {filename}")
                    return date_obj
                except Exception:
                    continue
        self.logger.warning(f"No date found in filename {filename}")
        return None