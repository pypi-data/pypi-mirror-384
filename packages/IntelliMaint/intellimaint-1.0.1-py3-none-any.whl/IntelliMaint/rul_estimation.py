#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anomaly Detection core class definition

Author: rameshbk
Last modified: Rachana, 18th August, 2025
"""
import os
import glob
import re
import scipy.io as sio
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.stats import skew, kurtosis, norm
from mpl_toolkits.mplot3d import Axes3D
import statsmodels.api as sm
import logging
from IntelliMaint.utils import Utils
# Set random seed for reproducibility


from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel, Matern, DotProduct
from sklearn.preprocessing import PolynomialFeatures, RobustScaler, MinMaxScaler, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


class GPRDegradationModel:
    """
    Generic Gaussian Process Regression (GPR) based degradation model for
    remaining useful life (RUL) prediction of industrial components.
    
    This model can be used for various types of components where degradation is
    monitored through MQE (Mean Quantization Error) or similar health indicators.
    
    Example usage:
    ```python
    # Initialize the model
    model = GPRDegradationModel(config={
        'window_size': 1.0,  # 1 second per window
        'adaptive_thresholds': True
    })
    
    # Run complete workflow
    results = model.run_workflow(
        health_indicator_scores=log_anomaly_scores,
        anomaly_point=first_anomaly_idx
    )
    
    # Get RUL prediction
    rul = results['rul']
    print(f"Predicted RUL: {rul} samples")
    print(f"Estimated time to failure: {results['remaining_time']['time_string']}")
    ```
    """

    def __init__(self, config=None, verbose=False):
        """
        Initialize the GPR Degradation Model
        
        Args:
            config (dict, optional): Configuration parameters including:
                - prediction_horizon: Number of time steps to predict ahead
                - window_size: Size of time window in seconds for displaying results
                - threshold_settings: Settings for incipient and failure thresholds
        """

        # Default configurations
        self.config = config

        self.verbose = verbose

        ut = Utils(verbose=verbose)
        self.logger = ut.get_logger(self.__class__.__name__)
        self._print_debug = ut.print_debug

        if self.verbose:
            print(f"[DEBUG] GPRDegradationModel initialized with config {self.config}")
        self.logger.info(f"Initialized GPRDegradationModel with config {self.config}")

        # Prediction parameters
        self.prediction_method = "gpr" # or ensemble
        self.prediction_horizon = self.config.get('prediction_horizon', 300)
        self.window_size = self.config.get('window_size',1.0)  # Default 1 second per window
        self.random_state = 42  # For reproducibility
        
        # Threshold settings - can be manually set or adaptively determined
        self.incipient_threshold = self.config.get('incipient_threshold', 0.3)
        self.failure_threshold = self.config.get('failure_threshold', 4.0)
        self.adaptive_thresholds = True 
        
        # Anomaly detection settings
        self.anomaly_offset = None  # Will be set during initialization or from external detection
        
        # Data storage
        self.scale_score = False
        self.raw_scores = None      # Original health indicator scores
        self.scaled_scores = None   # Normalized/scaled health indicator scores
        self.full_mqe_scores = None  # Same as scaled_scores, kept for backward compatibility
        self.degradation_method = "trend_analysis" # or static
        
        # Model storage
        self.gpr_model = None 
        self.poly_model = None       
        self.y_pred = None
        self.y_std = None
        self.kernels = RBF(length_scale=1.0) + Matern(length_scale=1.0, nu=1.5) + WhiteKernel(noise_level=1e-3)

    def _print_debug(self, msg):
        # Use ONLY occasionally and only for values useful to see in verbose mode
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def process_data(self, health_indicator_scores):
        """
        Process and scale health indicator data (e.g., MQE, anomaly scores)
        """
        self.logger.info("Processing and scaling health indicator data")

        # Store the raw scores
        self.raw_scores = np.array(health_indicator_scores)

        # Diagnostic output
        self.logger.debug(f"Input scores - min: {np.min(self.raw_scores)}, max: {np.max(self.raw_scores)}")
        self.logger.debug(f"Input scores - finite values: {np.isfinite(self.raw_scores).sum()} / {len(self.raw_scores)}")
            

        if self.scale_score: 
            self.logger.debug("Data will be scaled")
            
            # Remove any infinity or NaN values
            clean_scores = np.nan_to_num(
                self.raw_scores, 
                nan=np.min(self.raw_scores), 
                posinf=np.max(self.raw_scores), 
                neginf=np.min(self.raw_scores)
            )
            
            # Apply min-max scaling to get values in a 0-10 range for better visualization and modeling
            min_val = np.min(clean_scores)
            max_val = np.max(clean_scores)
            
            if min_val == max_val:
                scaled_scores = np.ones_like(clean_scores)
            else:
                scaled_scores = (clean_scores - min_val) / (max_val - min_val) * 10
            
            # Store the scaled scores
            self.scaled_scores = scaled_scores
            self.full_mqe_scores = scaled_scores  # For backward compatibility
            
            # Diagnostic output
            self.logger.debug(f"Scaled scores stats: min={np.min(scaled_scores)}, max={np.max(scaled_scores)}")
            self._print_debug(f"Scaled scores min: {np.min(scaled_scores)}, max: {np.max(scaled_scores)}")
        
        else:
            self.logger.debug("Data will not be scaled")
            scaled_scores = health_indicator_scores
            # Store the scaled scores
            self.scaled_scores = scaled_scores
            self.full_mqe_scores = scaled_scores  # For backward compatibility            

        self.logger.info("Scaled scores obtained")
        return scaled_scores
    
    def set_thresholds(self, incipient=None, failure=None):
        """
        Set degradation thresholds manually or compute them adaptively from data
        
        Args:
            incipient (float, optional): Manual incipient threshold
            failure (float, optional): Manual failure threshold
            
        Returns:
            tuple: (incipient_threshold, failure_threshold)
        """
        self.logger.info("Setting thresholds for incipient/failure detection")
        if incipient is not None:
            self.incipient_threshold = incipient
            self.logger.debug(f"Manually set incipient threshold: {self.incipient_threshold}")
        
        if failure is not None:
            self.failure_threshold = failure
            self.logger.debug(f"Manually set failure threshold: {self.failure_threshold}")
            return self.incipient_threshold, self.failure_threshold

        # If no thresholds provided and adaptive thresholds enabled, compute from data
        if self.adaptive_thresholds and self.scaled_scores is not None:
            self.logger.info("Computing thresholds from data")
            # Calculate percentiles for threshold setting
            percentiles = np.percentile(self.scaled_scores, [25, 50, 75, 90, 95, 99])
            
            # Set incipient threshold based on percentiles if not manually provided
            if incipient is None:
                self.incipient_threshold = percentiles[1]
                self.logger.debug(f"Adaptive incipient threshold: {self.incipient_threshold}")
            
            # Adaptive approach to set the failure threshold if not manually provided
            if failure is None:
                # Method 1: Mean of top values
                top_n = max(5, int(len(self.scaled_scores) * 0.01))  # Use at least 5 points or 1% of data
                sorted_scores = np.sort(self.scaled_scores)
                top_values = sorted_scores[-top_n:]
                mean_top_values = np.mean(top_values)
                
                # Method 2: High percentile
                high_percentile = percentiles[5]  # 99th percentile
                
                # Method 3: End of life focus
                end_window = min(50, len(self.scaled_scores) // 10)  # Last 50 points or 10% of data
                end_data = self.scaled_scores[-end_window:]
                end_max = np.max(end_data)
                end_mean = np.mean(end_data)
                end_75th = np.percentile(end_data, 75)

                self.logger.debug(f"Maximum score: {np.max(self.scaled_scores):.4f}")
                self.logger.debug(f"Mean of top {top_n} values: {mean_top_values:.4f}")
                self.logger.debug(f"99th percentile: {high_percentile:.4f}")
                self.logger.debug(f"End window maximum: {end_max:.4f}")
                self.logger.debug(f"End window mean: {end_mean:.4f}")
                
                # Choose the most appropriate method based on data characteristics
                if end_max > high_percentile * 0.8:
                    self.failure_threshold = max(end_75th, high_percentile * 0.7)
                    self.logger.debug(f"Failure threshold from end-of-life: {self.failure_threshold:.4f}")
                else:
                    self.failure_threshold = max(high_percentile, mean_top_values * 0.9)
                    self.logger.debug(f"Failure threshold from global stats: {self.failure_threshold:.4f}")
                
                # Safety check: ensure enough separation between thresholds
                if self.failure_threshold < self.incipient_threshold * 2:
                    old_threshold = self.failure_threshold
                    self.failure_threshold = self.incipient_threshold * 2
                    self.logger.warning(f"Adjusting failure threshold from {old_threshold:.4f} to {self.failure_threshold:.4f}")
        else:
            # Static Thresholds for cumulative health indicator scores
            self.incipient_threshold = 0.6
            self.failure_threshold = 0.8
            self.logger.info("Incipient and Failure thresholds set statically")

        return self.incipient_threshold, self.failure_threshold
    
    def detect_degradation_onset(self, anomaly_point=None):
        """
        Detect the onset of degradation using trend analysis or external anomaly detection
        
        Args:
            anomaly_point (int, optional): Externally detected anomaly index
            
        Returns:
            int: Detected degradation onset index
        """
        self.logger.info("Detecting degradation onset")
        # If an external anomaly point is provided, use it
        if anomaly_point is not None:
            self.anomaly_offset = anomaly_point
            self.logger.debug(f"Using provided anomaly point as degradation onset: {self.anomaly_offset}")
            return self.anomaly_offset
        
        if self.scaled_scores is not None:

            if self.degradation_method == 'static':
                # === Detect degradation onset ===
                # Define onset as first point where observed wear exceeds 60%
                onset_mask = self.scaled_scores >= self.incipient_threshold
                if np.any(onset_mask):
                    self.anomaly_offset = np.where(onset_mask)[0][0]
                else:
                    self.anomaly_offset = 0 # fallback if never crossed
                self.logger.debug(f"Static warning index: {self.anomaly_offset}")
            
            elif self.degradation_method == 'trend_analysis':
                # Otherwise use trend analysis to detect degradation onset

                # Calculate rolling mean to smooth the data
                window_size = min(31, len(self.scaled_scores) // 10)
                if window_size % 2 == 0:
                    window_size += 1 # Ensure odd window size
                
                if len(self.scaled_scores) > window_size:
                    rolling_mean = np.convolve(
                        self.scaled_scores,
                        np.ones(window_size) / window_size,
                        mode='valid'
                    )
                    
                    # Pad the beginning to maintain array size
                    pad_width = len(self.scaled_scores) - len(rolling_mean)
                    rolling_mean = np.pad(rolling_mean, (pad_width, 0), 'edge')
                    
                    # Calculate slope using finite differences
                    slopes = np.gradient(rolling_mean)
                    
                    # Find regions with consistent positive slope
                    pos_slope_regions = slopes > 0
                    
                    # Look for the first significant region of positive slope
                    kernel_size = min(15, len(pos_slope_regions) // 20)
                    if kernel_size > 0:
                        conv_result = np.convolve(
                            pos_slope_regions.astype(int), 
                            np.ones(kernel_size), 
                            mode='same'
                        )
                        
                        # Find the first point where we have several consecutive positive slopes
                        threshold = kernel_size * 0.8  # 80% of the kernel should be positive
                        significant_regions = conv_result > threshold
                        
                        degradation_candidates = np.where(significant_regions)[0]
                        
                        if len(degradation_candidates) > 0:
                            # Take the first significant point as degradation onset
                            self.anomaly_offset = degradation_candidates[0]
                            self.logger.debug(f"Trend analysis degradation onset: {self.anomaly_offset}")
                        else:
                            # Fallback: use a point 1/4 of the way through the data
                            self.anomaly_offset = len(self.scaled_scores) // 4
                    else:
                        # Not enough data for kernel analysis
                        self.anomaly_offset = len(self.scaled_scores) // 4
                else:
                    # Not enough data for rolling mean
                    self.anomaly_offset = len(self.scaled_scores) // 4
                    self.logger.debug(f"Not enough data for rolling mean. Using {self.anomaly_offset} as degradation onset.")

                # Ensure we have enough data for training
                if self.anomaly_offset > len(self.scaled_scores) - 10:
                    self.anomaly_offset = max(0, len(self.scaled_scores) - 20)
                    self.logger.warning(f"Adjusted degradation onset to {self.anomaly_offset} to ensure enough training data")
        else:
            # No data available, use a default value
            self.anomaly_offset = 0
            self.logger.warning("No data available for degradation onset detection.")
        
        return self.anomaly_offset
    

    def predict_rul_ensemble(self):
        """
        Predict the Remaining Useful Life (RUL) and wear percentage using an ensemble
        of GPR and polynomial regression, trained from degradation onset.

        Returns:
            dict: Dictionary with predicted wear, metrics, important times, and estimated RUL in hours.
        """
        
        self.logger.info("Training ensemble model (GPR + polynomial regression)")
        np.random.seed(self.random_state)  # For reproducibility
        hi = self.scaled_scores
        onset_idx = self.anomaly_offset

        # === Train GPR on cumulative wear directly ===
        X_train_size = onset_idx
        X_train = np.arange(0, X_train_size).reshape(-1, 1)
        y_train = hi[0:X_train_size]
        self.logger.debug(f"Size of the training dataset for gpr is {X_train_size} starting from {0}")
        
        # Test set
        test_idx = onset_idx
        X_pred = np.arange(test_idx, len(hi)).reshape(-1, 1)
        self.logger.debug(f"Size of predicted wear for gpr is {len(X_pred)} starting from {test_idx}")
        
        # === Linear Regression on Polynomial Feature === 
        poly_features = PolynomialFeatures(degree=2)
        X_poly = poly_features.fit_transform(X_train)
        self.poly_model = LinearRegression()
        self.poly_model.fit(X_poly, y_train)
        
        X_pred_poly = poly_features.transform(X_pred)
        y_poly_pred = self.poly_model.predict(np.vstack([X_poly, X_pred_poly]))

        self.gpr_model = GaussianProcessRegressor(
            kernel=self.kernels,
            alpha=1e-4,
            n_restarts_optimizer=15,
            normalize_y=True)
        self.gpr_model.fit(X_train, y_train)
        y_gpr_pred, y_gpr_std = self.gpr_model.predict(np.vstack([X_train, X_pred]), return_std=True)

        alpha = np.linspace(0.5, 1.0, len(X_pred) + len(X_train))
        self.y_pred = (1 - alpha) * y_poly_pred + alpha * y_gpr_pred
        self.y_std = y_gpr_std[X_train_size:]

        mae = mean_absolute_error(hi[onset_idx:], self.y_pred[onset_idx:])
        rmse = np.sqrt(mean_squared_error(hi[onset_idx:], self.y_pred[onset_idx:]))
        r2score = r2_score(hi[onset_idx:], self.y_pred[onset_idx:])
        
        for i, (fileidx, wear) in enumerate(zip(X_pred.flatten(), self.y_pred)):
            self._print_debug(f"File index {fileidx}: Predicted wear = {wear:.2f}")
    
        self.logger.info(f"Ensemble model - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2score:.4f}")
        self._print_debug(f"1st 5 GPR+poly preds: {self.y_pred[:5]}")
        
        ##########
        self.logger.info("Predicting RUL via ensemble")
        
        if self.gpr_model is None or self.poly_model is None:
            self.logger.error("Models not trained. Call train_ensemble_model() first.")
            raise ValueError("Models not trained. Call train_ensemble_model() first.")
        
        hi = self.scaled_scores
        predicted_wear = self.y_pred
        actual_critical = hi >= self.failure_threshold
        
        # Define critical as first point where wear crosses failure threshold
        if np.any(actual_critical):
            actual_critical_idx = np.where(actual_critical)[0][0]
        else:
            actual_critical_idx = 0

        predicted_wear = self.y_pred        
        # === Detect degradation ===
        # For predicted wear, obtain warning and critical points
        warning_mask = predicted_wear >= self.incipient_threshold
        if np.any(warning_mask):
            warning_idx = np.where(warning_mask)[0][0]
            # print(f" Warning Point: At hour {warning_time} (wear ≥ 80%) for file index {warning_idx}")
        else:
            self.logger.info("Predicted wear doesn't cross 60% threshold")

        # Find critical point
        failure_mask = predicted_wear >= self.failure_threshold
        if np.any(failure_mask):
            critical_idx = np.where(failure_mask)[0][0] 
            # print(f" Critical Point: At hour {critical_time} (wear ≥ 80%) for file index {critical_idx}")
        else:
            self.logger.info("No critical point found — fallback to failure")

        predicted_failure_idx = np.where(predicted_wear>=1)[0][0]
        
        # From degradation onset to failure
        rul_from_onset_idx = predicted_failure_idx - warning_idx
        
        # From critical point to failure
        rul_from_critical_idx = predicted_failure_idx - critical_idx
        
        # Logging
        self.logger.info(f" Predicted Warning index: at {warning_idx}")
        self.logger.info(f" Actual Critical index: at {actual_critical_idx}")
        self.logger.info(f" Predicted Critical index: at {critical_idx}")
        self.logger.info(f" Predicted Failure index: at {predicted_failure_idx}")
        self.logger.info(f" RUL from critical index: at {rul_from_critical_idx}")
        
        if predicted_failure_idx:
            self.logger.info(f" Predicted Failure Cycle: {predicted_failure_idx}")
            self.logger.info(f" Estimated RUL: {rul_from_onset_idx:.2f} indices") #changed rul_hours to rul_from_critical_hours
    
        self.calculate_remaining_time(rul_from_onset_idx)

        return (
            self.y_pred,               # Predicted values
            self.y_std**2,             # Variance
            rul_from_onset_idx, 
            None# RUL
        )        

    def predict_rul_gpr(self, hi=None):
        """
        Predict Remaining Useful Life using the trained GPR model
        
        Args:
            horizon (int, optional): Prediction horizon
        
        Returns:
            tuple: (predicted_values, variance, rul, future_indices)
        """
        self.logger.info("Training GPR model for RUL prediction")
        
        if self.scaled_scores is None:
            self.logger.error("No data available. Call process_data() first.")
            raise ValueError("No data available. Call process_data() first.")
        
        if self.anomaly_offset is None:
            self.logger.info("Degradation onset not detected; auto-detecting.")
            self.detect_degradation_onset()
        
        # Select data from degradation onset for training
        selected_scores = self.scaled_scores[self.anomaly_offset:]
        self.logger.debug(f"Selected {len(selected_scores)} points after anomaly offset {self.anomaly_offset}")
        self._print_debug(f"GPR training set length: {len(selected_scores)} points")
        
        # Prepare input data for GPR
        X = np.arange(len(selected_scores)).reshape(-1, 1)
        y = selected_scores
        
        # Initialize and fit GPR model
        self.gpr_model = GaussianProcessRegressor(
            kernel=self.kernels,
            n_restarts_optimizer=10,
            alpha=1e-10,
            random_state=self.random_state)
        
        # Fit the model
        self.gpr_model.fit(X, y)
        
        self.logger.info(f"GPR model trained (offset={self.anomaly_offset}, incipient={self.incipient_threshold}, failure={self.failure_threshold})")
        self._print_debug(f"GPR model fitted. X shape: {X.shape}, y shape: {y.shape}")
        

        ######
        self.logger.info("Predicting RUL using GPR model")
        
        horizon = None
        if self.gpr_model is None:
            self.logger.error("Model not trained. Call train_model() first.")
            raise ValueError("Model not trained. Call train_model() first.")
        # Use default or specified horizon
        horizon = horizon or self.prediction_horizon
        
        # Calculate distance to the end of our data to ensure we capture full degradation
        if self.scaled_scores is not None:
            data_length = len(self.scaled_scores)
            # Distance from anomaly onset to end of data
            distance_to_end = data_length - self.anomaly_offset
            # Add some margin (50% more)
            extended_horizon = int(distance_to_end * 1.5)
            # Use the larger of the specified horizon or the extended one
            horizon = max(horizon, extended_horizon)
            self.logger.debug(f"Prediction horizon auto-extended to {horizon}")
        
        # Generate future time steps
        X_pred = np.arange(0, horizon).reshape(-1, 1)
        
        # Predict health indicator values with uncertainty
        try:
            y_pred, y_std = self.gpr_model.predict(X_pred, return_std=True)
        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return np.zeros(horizon), np.zeros(horizon), 0, np.arange(horizon)
        
        # Find RUL when prediction crosses failure threshold
        rul_indices = np.where(y_pred >= self.failure_threshold)[0]
        
        # Determine RUL
        if len(rul_indices) > 0:
            rul = rul_indices[0] # First point crossing failure threshold
            self.logger.debug(f"RUL found by threshold crossing at {rul}")
        else:
            # If no crossing, try to find where the prediction starts to decline
            # after reaching a peak - this could indicate a different failure mode
            
            # Find the peak in the prediction
            if len(y_pred) > 30:  # Need enough points to identify a pattern
                # Smooth the prediction to avoid minor fluctuations
                window_size = min(15, len(y_pred) // 20)
                if window_size % 2 == 0:
                    window_size += 1  # Ensure odd window size
                
                # Apply smoothing
                smooth_pred = np.convolve(
                    y_pred, 
                    np.ones(window_size)/window_size, 
                    mode='valid'
                )
                # Pad to maintain size
                pad_width = len(y_pred) - len(smooth_pred)
                smooth_pred = np.pad(smooth_pred, (0, pad_width), 'edge')
                
                # Find the peak
                peak_idx = np.argmax(smooth_pred)
                
                if peak_idx > 0 and peak_idx < len(y_pred) - 20:
                    # Use peak as RUL if it's not at the very beginning or end
                    self.logger.debug(f"No threshold crossing found. Using prediction peak at index {peak_idx} as RUL")
                    rul = peak_idx
                else:
                    # If no meaningful peak, use 3/4 of the horizon
                    rul = horizon * 3 // 4
                    self.logger.debug(f"No threshold crossing or clear peak. Using {rul} as RUL")
            else:
                # Not enough points for analysis, use a default value
                rul = horizon - 1
                self.logger.debug(f"No threshold crossing found. Using {rul} as RUL")
        
        # Calculate time to data end (for comparison)
        if self.scaled_scores is not None:
            data_length = len(self.scaled_scores)
            time_to_data_end = data_length - self.anomaly_offset
            self.logger.debug(f"Time from anomaly onset to end of data: {time_to_data_end} samples")
            
            if rul < time_to_data_end * 0.7:
                self.logger.warning(f"PREDICTED RUL ({rul}) is much shorter than actual data length.")
        
        self.calculate_remaining_time(rul)
        self._print_debug(f"GPR-predicted RUL: {rul}")
        
        return (
            y_pred,               # Predicted values
            y_std**2,             # Variance
            rul,                  # RUL
            X_pred.flatten()      # Future indices
        )

    def calculate_remaining_time(self, rul):
        """
        Calculate remaining time in human-readable format
        
        Args:
            rul (int): Remaining useful life in samples
            
        Returns:
            tuple: (hours, minutes, seconds)
        """
        self.logger.info("Calculating Remaining Time")

        # Calculate remaining time based on window size
        remaining_time_seconds = rul * self.window_size
        
        # Convert to hours, minutes, seconds
        hours = remaining_time_seconds // 3600
        minutes = (remaining_time_seconds % 3600) // 60
        seconds = remaining_time_seconds % 60
        
        time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s" if hours > 0 else f"{int(minutes)}m {int(seconds)}s"
        
        self.logger.debug(f"RUL: {rul} samples (each sample = {self.window_size} second window)")
        self.logger.debug(f"Estimated Remaining Time: {time_str}")
        
        self.remaining_time = {
            "samples": rul,
            "seconds": remaining_time_seconds,
            "hours": hours,
            "minutes": minutes,
            "seconds_remainder": seconds,
            "time_string": time_str
        }
        
        return hours, minutes, seconds
    

    def get_results_dataframe(self, rul=None):
        """
        Create a DataFrame with RUL prediction results
        
        Args:
            rul (int, optional): RUL value (if not provided, will use last predicted RUL)
            
        Returns:
            pd.DataFrame: RUL prediction results
        """
        # If RUL not provided, try to get from stored values
        if rul is None:
            if hasattr(self, 'remaining_time') and 'samples' in self.remaining_time:
                rul = self.remaining_time['samples']
            else:
                self.logger.warning("No RUL value available. Run predict_rul() first.")
                return pd.DataFrame()
        
        # Get time estimates
        if not hasattr(self, 'remaining_time') or self.remaining_time['samples'] != rul:
            self.calculate_remaining_time(rul)
        
        results_df = pd.DataFrame({
            "rul": rul,
            "start_time": [self.anomaly_offset],
            "predicted_failure_time": [self.anomaly_offset + rul],
            "remaining_useful_life_samples": [rul],
            "incipient_threshold": [self.incipient_threshold],
            "failure_threshold": [self.failure_threshold],
            "remaining_time_seconds": [self.remaining_time["seconds"]],
            "remaining_time_hours": [self.remaining_time["hours"]],
            "remaining_time_minutes": [self.remaining_time["minutes"]],
            "window_size_seconds": [self.window_size]
        })

        self.logger.info("Results dataframe created")
        return results_df

    def run_workflow(self, health_indicator_scores, anomaly_point=None, process_data=False):
        """
        Run the complete RUL prediction workflow
        
        Args:
            health_indicator_scores (np.ndarray): Health indicator scores
            anomaly_point (int, optional): Externally detected anomaly index
            
        Returns:
            dict: Complete results including RUL prediction and plots
        """
        self.logger.info("Running the full RUL prediction workflow")

        # Step 1: Process the data
        self.process_data(health_indicator_scores)
        
        # Step 2: Set thresholds (adaptive by default)
        self.set_thresholds()
        
        # Step 3: Detect degradation onset (or use provided anomaly point)
        self.detect_degradation_onset(anomaly_point)
        
        # Step 4 & 5: Train the model and Predict rul
        if self.prediction_method == "gpr":
            # self.train_model()
            predicted_values, variance, rul, future_indices = self.predict_rul_gpr()
        elif self.prediction_method == "ensemble":
            # self.train_ensemble_model()
            predicted_values, variance, rul, future_indices = self.predict_rul_ensemble()        

        
        # # Step 6: Create visualization
        # self.plot_rul_prediction(
        #     time_indices=np.arange(len(health_indicator_scores)),
        #     actual_values=self.scaled_scores,
        #     predicted_values=predicted_values,
        #     variance=variance,
        #     future_indices=future_indices,
        #     rul=rul
        # )
        
        # Step 7: Get results DataFrame
        results_df = self.get_results_dataframe(rul)

        self.logger.info("Workflow complete")
        self._print_debug(f"Workflow RUL: {rul}")
        
        # Return all results in a dictionary
        return {
            "rul": rul,
            "predicted_values": predicted_values,
            "variance": variance, 
            "future_indices": future_indices,
            "results_df": results_df,
            "anomaly_offset": self.anomaly_offset,
            "incipient_threshold": self.incipient_threshold,
            "failure_threshold": self.failure_threshold,
            "remaining_time": self.remaining_time
        }