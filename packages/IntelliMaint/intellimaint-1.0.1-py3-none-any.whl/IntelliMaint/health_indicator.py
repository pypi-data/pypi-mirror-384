#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anomaly Detection core class definition

Author: rameshbk
Last modified: Shweta, 5th August, 2025
"""
import pandas as pd
import numpy as np
from scipy.spatial import distance
import logging
from IntelliMaint.utils import Utils

class HealthIndicatorConstructor:
    def __init__(self, config=None, verbose=False):
        """
        Initialize the health indicator constructor and set up methods and configuration.

        Args:
            config (dict, optional): Configuration for indicator weights, names, or methods.

        Returns:
            None
        """
        self.verbose = verbose

        ut = Utils(verbose=verbose)
        self.logger = ut.get_logger(self.__class__.__name__)
        self._print_debug = ut.print_debug

        if self.verbose:
            print(f"[DEBUG] HealthIndicatorConstructor initialized with config: {config}")
        self.logger.info(f"Initialized HealthIndicatorConstructor with config: {config}")

        # Use provided config or fallback to default
        self.config = config  # if config else default_config
        self.method = "fused"
        self.cumulative_method = None

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def construct_health_indicator(self, features_df, features_to_fuse=None, weights=None):
        """Construct a health indicator using the configured method.

        Args:
            features_df (pd.DataFrame): DataFrame of feature values.
            features_to_fuse (list of str, optional): Names of columns to fuse (for 'fused' method).
            weights (list of float, optional): Weights assigned to each feature for fusion.

        Uses Config Parameters:
            method (str): Specifies 'cumulative' or 'fused' HI computation.

        Returns:
            pd.DataFrame or np.ndarray: Health indicator result, format depends on method.
        """
        self.logger.info(f"Constructing health indicator using method='{self.method}'")

        if self.method == "cumulative":
            return self.compute_cumulative_hi(features_df)
        elif self.method == "fused":
            return self.compute_fused_hi(features_df, features_to_fuse, weights)
        else:
            self.logger.error(f"Unknown HI method: {self.method}")
            raise ValueError(f"Unknown HI method: {self.method}")

    def compute_cumulative_hi(self, feature_df):
        """
        Compute cumulative delta-based degrading health indicator (HI) ensuring a
        monotonic trend.

        Args:
            feature_df (pd.DataFrame): Feature data, with rows as samples.

        Uses Config Parameters:
            cumulative_method (str): If 'euclid', uses Euclidean; otherwise uses Mahalanobis.
            train_size (int, optional): Number of baseline rows (default is 20% of data).

        Returns:
            np.ndarray: 1D array of normalized cumulative HI, mapped from 1 (healthy) to 0 (degraded).
        """
        self.logger.info("Computing cumulative health indicator")

        if not hasattr(self, "train_size") or not self.train_size:
            self.logger.warning("train size not defined")
            self.train_size = int(0.2 * len(feature_df))
            self.logger.debug(f"train_size set to {self.train_size}")

        normal = feature_df.iloc[:self.train_size]
        test = feature_df.iloc[self.train_size:]

        if self.cumulative_method == "euclid":
            self.logger.debug("Using Euclidean distance method")
            raw_hi = np.linalg.norm(test.values - normal.mean().values, axis=1)
        else:
            self.logger.debug("Using Mahalanobis distance method")
            cov = np.cov(normal.values, rowvar=False)
            inv_cov = np.linalg.pinv(cov)
            mean_vec = normal.mean().values
            raw_hi = [distance.mahalanobis(x, mean_vec, inv_cov) for x in test.values]

        delta = np.abs(np.diff(raw_hi, prepend=raw_hi[0]))
        cum_hi = np.cumsum(delta)

        if np.max(cum_hi) == 0:
            self.logger.warning("No degradation detected — returning flat HI=1")
            return np.ones_like(cum_hi)  # flat, no degradation

        cum_hi_norm = cum_hi / np.max(cum_hi)
        final_hi = 1 - cum_hi_norm

        self.logger.debug(f"Computed cumulative HI shape: {final_hi.shape}")
        return final_hi

    def compute_fused_hi(self, feature_df, features_to_fuse, weights):
        """
        Compute a fused health indicator as a weighted sum of selected features.

        Args:
            feature_df (pd.DataFrame): Feature DataFrame with candidate HI components.
            features_to_fuse (list of str): List of column names to include in the fusion.
            weights (list of float): Weights for each feature in the fusion.

        Uses Config Parameters:
            None

        Returns:
            pd.DataFrame: Modified DataFrame with a new 'SK_Fused_HI' column.
        """
        self.logger.info("Computing fused health indicator")
        self.logger.debug(f"Features to fuse: {features_to_fuse}, Weights: {weights}")

        feature_df['fused_feature'] = 0
        for feat, w in zip(features_to_fuse, weights):
            self.logger.debug(f"Fusing feature '{feat}' with weight {w}")
            self._print_debug(f"Fusing: {feat} ({w})")
            feature_df['fused_feature'] += w * feature_df[feat]

        self.logger.info("Fused HI computation complete")
        return feature_df