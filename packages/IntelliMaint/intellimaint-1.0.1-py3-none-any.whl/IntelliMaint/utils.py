#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Component Template class definition

Author: rameshbk
Last modified: Rachana, 13th August, 2025
"""

import numpy as np
import os, glob
import re
import pandas as pd
import json
import logging 
from logging.handlers import RotatingFileHandler

class Utils:
    """
    Utility helper functions for signal and statistical preprocessing tasks.

    This class provides small, reusable methods for:
    - Ensuring data shapes are consistent,
    - Counting positive/negative values in arrays,
    - Computing z-scores and their parameters,
    - Normalizing arrays.

    Designed for use in preprocessing pipelines such as health indicator
    computation, time/frequency-domain analysis, and other condition
    monitoring workflows.
    """
    def __init__(self, verbose=False):
        self.verbose = verbose

    def ensure_column_vector(self, data):
        """
        Validate and reshape input array to a column vector if needed.

        Ensures that:
            - Input is converted to a NumPy array (if list or other type),
            - Scalars are rejected,
            - Multi-dimensional arrays pass through unchanged.

        Args:
            data (np.ndarray or list): Input data array or 1D list-like structure.

        Returns:
            np.ndarray:
                Validated and reshaped data array, guaranteed to have
                at least 2 dimensions (column vector if originally 1D).

        Raises:
            ValueError: If `data` is scalar or has no dimensions.
        """
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        if data.ndim < 1:  # Scalar check
            raise ValueError("Input vector should have at least 1 dimension.")
        # elif data.ndim == 1:  # Convert row vector → column vector
        #     data = np.reshape(data, (data.shape[0], 1))
        return data
    
    def ensure_1d_vector(self, data):
        # Flatten 2D arrays to 1D; keep 1D as-is
        if data.ndim == 1:
            pass
        elif data.ndim == 2:
            data = data.flatten()
        else:
            raise ValueError("Only 1D or 2D input is supported.")
        return data

    def count_pos(self, data):
        """
        Count the number of positive (> 0) values in the data.

        Counts are computed per column if array is 2D.

        Args:
            data (np.ndarray): Input data array. Can be 1D or 2D.

        Returns:
            np.ndarray:
                Count of positive values.
                - Shape (1,) if input was 1D.
                - Shape (n_columns,) if input was 2D.
        """
        if len(data.shape) == 1:
            count = (data > 0).sum()
        else:
            count = [(column > 0).sum() for column in data.T]
        return np.asarray(count)

    def count_neg(self, data):
        """
        Count the number of negative (< 0) values in the data.

        Counts are computed per column if array is 2D.

        Args:
            data (np.ndarray): Input data array. Can be 1D or 2D.

        Returns:
            np.ndarray:
                Count of negative values.
                - Shape (1,) if input was 1D.
                - Shape (n_columns,) if input was 2D.
        """
        if len(data.shape) == 1:
            count = (data < 0).sum()
        else:
            count = [(column < 0).sum() for column in data.T]
        return np.asarray(count)

    def zscore(self, data, mu, sigma):
        """
        Compute the z-score for the data given mean and standard deviation.

        Formula:
            z = (data - mu) / sigma

        Args:
            data (np.ndarray): Input data array.
            mu (float or np.ndarray): Mean value(s) for normalization.
            sigma (float or np.ndarray): Standard deviation value(s) for normalization.

        Returns:
            np.ndarray:
                Z-score normalized data.
        """
        z_s = (data - mu) / sigma
        return z_s

    def zs_param(self, train, percentileScore=None):
        """
        Compute the mean and standard deviation (z-score parameters) from training data.

        Args:
            train (np.ndarray):
                Training dataset to derive parameters.
            percentileScore (float, optional):
                If provided, uses this percentile instead of the mean for `mu`.
                Default is None (use mean).

        Returns:
            tuple:
                - mu (float): Mean or percentile value of the data.
                - sigma (float): Standard deviation of the data.
        """
        if percentileScore is None:
            mu, sigma = np.mean(train), np.std(train)
        else:
            mu, sigma = np.percentile(train, percentileScore), np.std(train)
        return mu, sigma

    def normalize_data(self, data):
        """
        Normalize the input signal to zero mean and unit variance (z-score normalization).

        Formula:
            normalized = (data - mean) / (std + epsilon)

        Args:
            data (np.ndarray): Input signal or dataset to normalize.

        Returns:
            np.ndarray:
                Normalized signal with zero mean and unit variance.
        """
        mean = np.mean(data)
        std = np.std(data)
        return (data - mean) / (std + 1e-10)
    
    def get_logger(self, name):

        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.warning(f"Creating new logger for {name}")
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            
            # File handler
            file_handler = logging.FileHandler('intellimaint_core_classes.log') #RotatingFileHandler('intellimaint_core_classes.log', maxBytes=2000, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Stream handler
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
        return logger
    
    def print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")