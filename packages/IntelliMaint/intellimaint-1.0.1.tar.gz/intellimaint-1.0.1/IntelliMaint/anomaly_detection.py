#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anomaly Detection core class definition

Author: rameshbk
Last modified: rachana, July 25th, 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import glob
import os
from tqdm import tqdm
from sklearn.preprocessing import RobustScaler, MinMaxScaler
from grand.individual_anomaly.individual_anomaly_inductive import IndividualAnomalyInductive
from grand.individual_anomaly.individual_anomaly_transductive import IndividualAnomalyTransductive
from grand.group_anomaly.group_anomaly import GroupAnomaly
from IntelliMaint.utils import Utils
import pandas as pd
from scipy.stats import norm
from fpdf import FPDF
import logging

class COSMOAnomalyDetection:

    def __init__(self, w_martingale=15,k=50,non_conformity = "knn", ref_group=["hour-of-day"], verbose=False):
        """
        Initialize the COSMOAnomalyDetection with parameters for IndividualAnomalyTransductive model.

        Args:
            w_martingale (int): Window size for martingale.
            k (int): Number of neighbors for k-NN.
            non_conformity (str): Method name for non-conformity.
            ref_group (list of str): Reference group criteria.

        Returns:
            None
        """

        # Logging setup
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            self.logger.handlers = []

            file_handler = logging.FileHandler('core_classes.log')
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        self.verbose = verbose
        if self.verbose:
            print(f"[DEBUG] COSMOAnomalyDetection initialized with w_martingale={w_martingale}, k={k}, non_conformity={non_conformity}, ref_group={ref_group}")
        self.logger.info(f"Initialized COSMOAnomalyDetection with config: w_martingale={w_martingale}, k={k}, non_conformity={non_conformity}, ref_group={ref_group}")

        self.model = IndividualAnomalyTransductive(
                w_martingale = w_martingale,         # Window size for computing the deviation level
                ref_group = ref_group  # Criteria for reference group construction
                )
        
    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def deviation_detection(self, data, mu, sigma, l1 = 4, l2 = 8, l3 = 12):
        """
        Detect deviations using z-score thresholds and visualize anomaly scores.

        Args:
            data (pd.DataFrame): Input data to evaluate.
            mu (float or scaler): Mean value for normalization.
            sigma (float or scaler): Standard deviation for normalization.
            l1 (float): Threshold level 1 (default 4).
            l2 (float): Threshold level 2 (default 8).
            l3 (float): Threshold level 3 (default 12).

        Returns:
            tuple:
                z_s (np.array): Computed z-scores of input data.
                sigma (float or scaler): Input standard deviation.
       
        """
        self.logger.info("Starting deviation detection")
        util = Utils()
        z_s = util.zscore(data,mu,sigma)
        if(len(z_s.shape)>1):
            z_s = z_s.iloc[:,0]

        self.logger.debug(f"Computed z-score shape: {z_s.shape}")
        
        t = np.linspace(0,len(z_s)-1,len(z_s))
        thres1 = l1*sigma
        thres2 = l2*sigma
        thres3 = l3*sigma

        self.logger.debug(f"The three thresholds are thresh1: {thres1}, thresh2: {thres2}, thresh3: {thres3}")

        plt.scatter(t[np.where(z_s<=thres1)], z_s[z_s<=thres1], color='y', label='Normal', alpha=0.3, edgecolors='none')
        plt.scatter(t[np.where((z_s>thres1) & (z_s<=thres2))], z_s[(z_s>thres1) & (z_s<=thres2)], color='b', label='L1 Threshold', alpha=0.3, edgecolors='none')
        plt.scatter(t[np.where((z_s>thres2) & (z_s<=thres3))], z_s[(z_s>thres2) & (z_s<=thres3)], color='g', label='L2 Threshold', alpha=0.3, edgecolors='none')
        plt.scatter(t[np.where(z_s>thres3)], z_s[z_s>thres3], color='r', label='Anomalous points', alpha=0.3, edgecolors='none')
        plt.xlabel('Observation Signal (in samples)')
        plt.ylabel('Anomaly Score')
        plt.title('Anomaly Score Estimation')
        plt.legend()
        return z_s, sigma

    def train_cosmo(self,data, threshold=0.6, w_martingale = 15, non_conformity = "knn",k = 20):
        """
        Train the COSMO anomaly model using inductive learning.

        Args:
            data (pd.DataFrame): Training dataset.
            threshold (float): Deviation threshold (default 0.6).
            w_martingale (int): Window size for martingale (default 15).
            non_conformity (str): Non-conformity measure, e.g., "knn" (default "knn").
            k (int): Number of neighbors for k-NN (default 20).

        Returns:
            None

        """
        self.logger.info("Starting cosmo training")        
        self.model = IndividualAnomalyInductive(
            w_martingale = w_martingale,
            non_conformity = non_conformity,
            k = k)

        # Fit the model to a fixed subset of the data
        X_fit = data.to_numpy()
        self.model.fit(X_fit)
        self.model.dev_threshold = threshold
        self.logger.debug(f"Threshold from model: {threshold}")
        self.logger.info("Cosmo training completed")
        return

    def test_cosmo(self, data, debug=False):
        """
        Test new data using the trained COSMO anomaly model and return anomaly scores.

        Args:
            data (pd.DataFrame): Input test data.

        Returns:
            tuple:
                strangeness (np.array): Strangeness scores for each data point.
                p_values (np.array): P-values corresponding to strangeness.
        """
        self.logger.info("Started cosmo testing")
        cols = ['Strangeness', 'P-Values', 'Deviation']
        lst_dict = []
        df = data
        for t, x in zip(df.index, df.values):
            info = self.model.predict(t, x)
            lst_dict.append({'Strangeness': info.strangeness,
                             'P-Values':info.pvalue,
                             'Deviation':info.deviation})
            
        # Plot strangeness and deviation level over time
        # gr = self.model.plot_deviations(figsize=(12, 8), plots=["strangeness", "deviation", "pvalue", "threshold"])
        
        figsize=(12, 8)
        plots=["strangeness", "deviation", "pvalue", "threshold"]
        plots, nb_axs, i = list(set(plots)), 0, 0
        if "data" in plots:
            nb_axs += 1
        if "strangeness" in plots:
            nb_axs += 1
        if any(s in ["pvalue", "deviation", "threshold"] for s in plots):
            nb_axs += 1

        fig, axes = plt.subplots(nb_axs, sharex="row", figsize=figsize)
        if not isinstance(axes, (np.ndarray) ):
            axes = np.array([axes])

        if "data" in plots:
            axes[i].set_xlabel("Time")
            axes[i].set_ylabel("Feature 0")
            axes[i].plot(self.df.index, self.df.values[:, 0], label="Data")
            if debug:
                axes[i].plot(self.model.T, np.array(self.model.representatives)[:, 0], label="Reference")
            axes[i].legend()
            i += 1

        if "strangeness" in plots:
            axes[i].set_xlabel("Time")
            axes[i].set_ylabel("Strangeness")
            axes[i].plot(self.model.T, self.model.S, label="Strangeness")
            if debug:
                axes[i].plot(self.model.T, np.array(self.model.diffs)[:, 0], label="Difference")
            axes[i].legend()
            i += 1

        if any(s in ["pvalue", "deviation", "threshold"] for s in plots):
            axes[i].set_xlabel("Time")
            axes[i].set_ylabel("Deviation")
            axes[i].set_ylim(0, 1)
            if "pvalue" in plots:
                axes[i].scatter(self.model.T, self.model.P, alpha=0.25, marker=".", color="green", label="p-value")
            if "deviation" in plots:
                axes[i].plot(self.model.T, self.model.M, label="Deviation")
            if "threshold" in plots:
                axes[i].axhline(y=self.model.dev_threshold, color='r', linestyle='--', label="Threshold")
            axes[i].legend()

        fig.autofmt_xdate()
        df1 = pd.DataFrame(lst_dict, columns=cols)
        self.logger.info("Cosmo testing completed")
        
        return df1['Strangeness'].to_numpy(), df1['P-Values'].to_numpy()


    def test_cosmo_streaming(self, data):
        """
        Stream test data through COSMO model to obtain sequential anomaly scores.

        Args:
            data (pd.DataFrame): Streaming data to evaluate.

        Returns:
            tuple:
                strangeness (np.array): Strangeness scores.
                p_values (np.array): Corresponding p-values.
                deviation (np.array): Deviation scores.
        """
        self.logger.info("Starting cosmo training for streaming data")
        cols = ['Strangeness', 'P-Values', 'Deviation']
        lst_dict = []
        df = data
        for t, x in zip(df.index, df.values):
            info = self.model.predict(t, x)
            lst_dict.append({'Strangeness': info.strangeness,
                             'P-Values':info.pvalue,
                             'Deviation':info.deviation})
        df1 = pd.DataFrame(lst_dict, columns=cols)
        self.logger.info("Cosmo testing for streaming data completed")
        return df1['Strangeness'].to_numpy(), df1['P-Values'].to_numpy(), df1['Deviation'].to_numpy()
    
    def nonstationary_AD_cosmo(self,data):
        """
       Perform COSMO anomaly detection on non-stationary data.

        Args:
            data (pd.DataFrame): Input data.

        Returns:
            tuple:
                strangeness (float): Strangeness score of first data point.
                deviation (float): Deviation score of first data point.
                pvalue (float): P-value of first data point.
        """
        self.logger.info("Started COSMO anomaly detection on non-stationary data")
        df = data
        cols = ['Strangeness', 'P-Values', 'Deviation']
        lst_dict = []
        
        info = self.model.predict(df.index[0], df.values[0])
        self.logger.info("Completed COSMO anomaly detection on non-stationary data")

        return info.strangeness, info.deviation, info.pvalue


class SOMAnomalyDetection:
    """
    Implements SOM-based anomaly detection with improved robustness and 
    statistical validation.
    """
    def __init__(self, som, verbose=False):
        """
        Initialize the SOM anomaly detection with a SOM instance.

        Args:
            som (SOM): SOM model to be used for anomaly detection.

        Returns:
            None
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            self.logger.handlers = []

            file_handler = logging.FileHandler('core_classes.log')
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        self.verbose = verbose

        self.som = som
        self.baseline_model = None
        self.scaler = None
        self.threshold = None
        self.baseline_stats = None

        if self.verbose:
            print(f"[DEBUG] SOMAnomalyDetection initialized with SOM: {som}")
        self.logger.info(f"Initialized SOMAnomalyDetection with SOM: {som}")

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def train_baseline(self, features_df):
        """
        Train the SOM model on baseline data and compute robust anomaly detection thresholds.

        Args:
            features_df (pd.DataFrame): Baseline feature data.
 
        Returns:
            None
        """
        self.logger.info("Starting SOM baseline training")
        self.logger.debug(f"Training data shape: {features_df.shape}")

        self.scaler = RobustScaler(with_centering=True, 
                                   with_scaling=True, 
                                   quantile_range=(1, 99)) 

        features_arr = self.scaler.fit_transform(features_df.values)
        self.logger.debug(f"Features scaled: shape={features_arr.shape}")

        self.baseline_model, _ = self.som.train(features_arr)
        errors = self.som.predict(self.baseline_model, features_arr, self.scaler)
        self.logger.debug(f"Initial MQE errors computed: shape={errors.shape}")

        log_errors = np.log10(errors + 1e-10)
        median = np.median(log_errors)
        mad = np.median(np.abs(log_errors - median))
        
        # Use very conservative threshold (5.0 * MAD)
        log_threshold = median + 5 * mad 
        self.threshold = 10 ** log_threshold

        self.baseline_stats = {
            'log_errors_mean': np.mean(log_errors),
            'log_errors_std': np.std(log_errors),
            'errors_percentile_99': np.percentile(errors, 99),
            'baseline_median': median,
            'baseline_mad': mad, 
            'threshold': log_threshold
        }

        self.logger.info(f"SOM baseline trained with threshold={self.threshold:.3f}")
        self.logger.info(f"Baseline stats: {self.baseline_stats}")

    def detect_anomalies_onlyMQE(self, features_df):
        """
        Detect anomalies in feature data using only the Mean Quantization Error (MQE) threshold.

        Args:
            features_df (pd.DataFrame): Input features to test.
 
        Returns:
            tuple:
                smoothed_errors (np.array): Smoothed MQE errors.
                anomalies (np.array): Boolean array indicating anomalies.
                errors (np.array): Raw quantization errors.
        """
        self.logger.info("Detecting anomalies (MQE threshold only)")
        
        features_arr = self.scaler.transform(features_df.values)
        errors = self.som.predict(self.baseline_model, features_arr, self.scaler)
        
        self.logger.debug(f"Errors computed: shape={errors.shape}")

        smoothed_errors = pd.Series(errors).rolling(window=5, center=True).mean()\
                                           .fillna(method='bfill').fillna(method='ffill').values
        anomalies = smoothed_errors > self.threshold
         
        self.logger.info(f"Anomalies detected: {np.sum(anomalies)} instances")
        return smoothed_errors, anomalies, errors

    def detect_anomalies(self, features_df, window_size, short_window_size, min_consecutive):
        """
        Detect anomalies with multi-criteria validation: MQE thresholding, trend analysis, and consecutive anomaly filtering.

        Args:
            features_df (pd.DataFrame): Input feature data to analyze.
            window_size (int): Smoothing window size for long-term trend.
            short_window_size (int) : Window size for local fluctuations.
            min_consecutive (int) : Minimum number of consecutive anomalies to validate.
 
        Returns:
            tuple:
                errors (np.array): Raw quantization errors.
                validated_anomalies (np.array): Boolean mask of validated anomalies.
                log_errors (np.array): Log-transformed errors for analysis.
        """
        self.logger.info("Detecting anomalies (multi-criteria)")
        
        features_arr = self.scaler.transform(features_df.values)
        self.logger.debug(f"Scaled feature array created: shape={features_arr.shape}")

        errors = self.som.predict(self.baseline_model, features_arr, self.scaler)
        self.logger.debug(f"SOM prediction (errors) computed: shape={errors.shape}")

        # Convert to log space for better handling of variations
        log_errors = np.log10(errors + 1e-10)
        self.logger.debug(f"Log errors computed: shape={log_errors.shape}, min={np.min(log_errors):.4f}, max={np.max(log_errors):.4f}")
        self._print_debug(f"Log errors range: {np.min(log_errors):.4f} to {np.max(log_errors):.4f}")

        # Calculate long-term trend with larger window
        if window_size >= len(log_errors):
            msg = "The rolling window size is too large for the input. Use a smaller value"
            self.logger.warning(msg)
            return 

        trend = pd.Series(log_errors).rolling(window=window_size, center=True, min_periods=1).mean()
        self.logger.debug(f"Trend computed with window_size={window_size}")

        # Calculate short-term variations
        if short_window_size >= len(log_errors):
            msg = "The short rolling window size is too large for the input. Use a smaller value"
            self.logger.warning(msg)
            return

        short_term = pd.Series(log_errors).rolling(window=short_window_size, center=True, min_periods=1).std()
        self.logger.debug(f"Short-term variation computed with short_window_size={short_window_size}")

        # Multi-criteria anomaly detection with statistical validation
        potential_anomalies = np.zeros_like(errors, dtype=bool)

        for i in range(len(errors)):
            exceeds_threshold = errors[i] > self.threshold
            trend_increasing = (i > window_size and trend.iloc[i] > trend.iloc[i - window_size])
            high_variation = (short_term.iloc[i] > 3 * np.median(short_term))
            potential_anomalies[i] = (exceeds_threshold and trend_increasing and high_variation)

        self.logger.debug(f"Potential anomalies detected: {np.sum(potential_anomalies)} instances")

        # Additional validation with consecutive anomalies requirement
        validated_anomalies = np.zeros_like(potential_anomalies)

        for i in range(len(potential_anomalies) - min_consecutive + 1):
            if np.all(potential_anomalies[i:i + min_consecutive]):
                window_errors = errors[i:i + min_consecutive]
                if np.all(np.diff(window_errors) > 0):
                    validated_anomalies[i:i + min_consecutive] = True

        self.logger.info(f"Validated anomalies detected: {np.sum(validated_anomalies)} instances")

        return errors, validated_anomalies, log_errors
