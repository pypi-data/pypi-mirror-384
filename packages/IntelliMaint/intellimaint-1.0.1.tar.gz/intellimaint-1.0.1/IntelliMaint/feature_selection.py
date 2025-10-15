#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Component Template class definition

Author: rameshbk
Last modified: Shweta, 5th August, 2025
"""
from IntelliMaint.data_analysis import SOM
from IntelliMaint.utils import Utils
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from scipy import signal
import logging

class FeatureSelection:
    """
    This block provides the various metrics to identify the suitable Health indicators.
    Given a numpy matrix with each column representing some degrading features, this block provides the scores for 
    each features in relation to degradation. The score value will be between 0 and 1.
    """
    def __init__(self, chunk_size=None, order=1, verbose=False):
        """
        Initialize the FeatureSelection object.

        Args:
            chunk_size (int, optional): Window size for filtering and chunk-wise scoring.
            order (int, optional): Order of median filter if smoothing is applied.
            verbose (bool, optional): If True, enables extra print debug messages.

        Returns:
            None
        """
        self.chunk_size = chunk_size
        self.order = order

        self.verbose = verbose

        ut = Utils(verbose=verbose)
        self.logger = ut.get_logger(self.__class__.__name__)
        self._print_debug = ut.print_debug

        if self.verbose:
            print(f"[DEBUG] FeatureSelection initialized with chunk_size={self.chunk_size}, order={self.order}")
        self.logger.info(f"Initialized FeatureSelection with chunk_size={self.chunk_size}, order={self.order}")

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def calculate_monotonicity(self, data):
        """
        Calculate monotonicity score for each feature in the given DataFrame.
        Monotonicity score measures how consistently increasing or decreasing a feature is.

        Args:
            data (pd.DataFrame or np.ndarray): Input Data where each column is a feature vector over time.
 
        Returns:
            dict[str, float]: Mapping from feature names to monotonicity scores (0 to 1).
        """
        self.logger.info("Calculating monotonicity scores")

        monotonicity_scores = {}
        if isinstance(data, np.ndarray):
            self.logger.debug("Data is a numpy array")
            data = pd.DataFrame(data, columns=[f"col_{i}" for i in range(data.shape[1])])

        for col in data.columns:
            values = data[col].values
            if not isinstance(values[0], tuple):
                diff = np.diff(values)
                pos = np.sum(diff > 0)
                neg = np.sum(diff < 0)
                n = len(values)
                score = abs(pos - neg) / (n - 1) if n > 1 else 0
                monotonicity_scores[col] = score
                self._print_debug(f"Monotonicity: Column {col}: score={score}")
        return monotonicity_scores

    def pos_monotonicity(self, data):
        """
		Calculate positive prognosability: measures increasing monotonic trend in features.

        Reference:
        Liao, Linxia, Wenjing Jin, and Radu Pavel.
        "Enhanced restricted Boltzmann machine with prognosability regularization for prognostics and health assessment."
        IEEE Transactions on Industrial Electronics 63.11 (2016): 7076-7083.

        Args:
            data (pd.DataFrame or np.ndarray): Feature data.
 
        Returns:
            np.ndarray: Scores measuring positive monotonicity per feature.
		"""
        self.logger.info("Calculating positive monotonicity")
        utils = Utils()
        temp1 = np.diff(data, axis=0)
        temp2 = np.diff(data, 2, axis=0)
        score = (utils.count_pos(temp1)/(data.shape[0]-1) + utils.count_pos(temp2)/(data.shape[0]-2))/2
        self.logger.debug(f"Positive monotonicity score: {score}")
        return score

    def neg_monotonicity(self, data):
        """
		Calculate negative prognosability: measures decreasing monotonic trend in features.

        Reference:
        Liao, Linxia, Wenjing Jin, and Radu Pavel.
        "Enhanced restricted Boltzmann machine with prognosability regularization for prognostics and health assessment."
        IEEE Transactions on Industrial Electronics 63.11 (2016): 7076-7083.

        Args:
            data (pd.DataFrame or np.ndarray): Feature data.
 
        Returns:
            np.ndarray: Scores measuring negative monotonicity per feature.
		"""
        self.logger.info("Calculating negative monotonicity")
        utils = Utils()
        temp1 = np.diff(data, axis=0)
        temp2 = np.diff(data, 2, axis=0)
        score = (utils.count_neg(temp1)/(data.shape[0]-1) + utils.count_neg(temp2)/(data.shape[0]-2))/2
        self.logger.debug(f"Negative monotonicity score: {score}")
        return score

    def linear_trendability(self, data):
        """
		Calculate linear trendability score for features using Pearson correlation with time.

		Args:
			data (pandas.DataFrame or np.ndarray): input data 

		Returns:
			scores (np.numpy.ndarray): Array of Pearson correlation coefficients per feature,
                                 or single value if input is 1D 

		"""
        self.logger.info("Calculating linear trendability")
        t = np.linspace(0, len(data) - 1, num=len(data))
        if len(data.shape) == 1:
            score = np.asarray(pearsonr(t, data)[0])
            self.logger.debug(f"Linear trendability score (1D): {score}")
            return score
        elif isinstance(data, pd.DataFrame):
            scores = [pearsonr(t, data[col].values)[0] for col in data.columns]
        else:
            scores = [pearsonr(t, data[:, i])[0] for i in range(data.shape[1])]
        scores = np.asarray(scores)
        self.logger.debug(f"Linear trendability scores: {scores}")
        return scores

    def nonlinear_trendability(self, data):
        """
		Calculates nonlinear trendability using Spearman correlation with time.

        Args:
            data (pd.DataFrame or np.ndarray): Input features with time as rows.
 
        Returns:
            np.ndarray or float: Spearman correlation coefficients for each feature or a single value if input is 1D.
		"""
        self.logger.debug("Calculating nonlinear trendability")
        t = np.linspace(0, len(data)-1, num=len(data))
        if len(data.shape) == 1:
            score = np.asarray(spearmanr(t, data)[0])
            self.logger.debug(f"Nonlinear trendability score (1D): {score}")
            return score
        elif isinstance(data, pd.DataFrame):
            scores = [spearmanr(t, data[column])[0] for column in data]
        else:
            scores = [spearmanr(t, data[:, i])[0] for i in range(data.shape[1])]
        scores = np.asarray(scores)
        self.logger.debug(f"Nonlinear trendability scores: {scores}")
        return scores

    def computeScore(self, data, method='mon'):
        """ 
		Compute the specified score metric on the data.

        Args:
            data (pd.DataFrame or np.ndarray): Feature data to score.
            method (str): Scoring method, options are:
                'mon' - monotonicity score,
                'pos_mon' - positive monotonicity,
                'neg_mon' - negative monotonicity,
                'lin_trend' - linear trendability,
                'nonlin_trend' - nonlinear trendability.
 
        Returns:
            np.ndarray, dict, or other: Computed score(s) according to method.
        
		"""
        self.logger.info(f"Computing score using method='{method}'")
        if method == 'mon':
            score = self.calculate_monotonicity(data)
        elif method == 'pos_mon':
            score = self.pos_monotonicity(data)
        elif method == 'neg_mon':
            score = self.neg_monotonicity(data)
        elif method == 'lin_trend':
            score = self.linear_trendability(data)
        elif method == 'nonlin_trend':
            score = self.nonlinear_trendability(data)
        else:
            msg = f"Valid option {{'mon','pos_mon','neg_mon', 'lin_trend','nonlin_trend'}} NOT selected."
            self.logger.error(msg)
            score = None
            raise ValueError(msg)
        self.logger.debug(f"Score result: {score}")
        return score

    def computeHIScore(self, data, method='mon'):
        """ 
		Compute Health Indicator (HI) score with optional chunking and median filtering.

        Args:
            data (np.ndarray or pd.DataFrame): Feature data.
            method (str): Scoring method, same options as computeScore.

        Uses Config Parameters:
            chunk_size (int): If set, computes scores over chunks/windows.
            order (int): Median filter order for smoothing chunked data.

        Returns:
            dict or np.ndarray:
            - Returns a dict if no chunking is used (full data is scored).
            - Returns a 1D NumPy array if chunking is applied (one score per chunk).
		"""
        self.logger.info(f"Computing HI score using method='{method}' with chunk_size={self.chunk_size}")
        if self.chunk_size is None:
            return self.computeScore(data, method)
        if self.order % 2 == 0:
            self.order = self.order + 1
            self.logger.debug(f"Adjusted order for median filter: {self.order}")
            data = signal.medfilt(data, self.order)
        score = []
        for i in range(0, len(data), self.chunk_size):
            chunk_score = self.computeScore(data[i:i+self.chunk_size], method=method)
            score.append(chunk_score)
        result = np.asarray(score).reshape(1, len(score))
        self.logger.debug(f"HI score result: {result}")
        return result