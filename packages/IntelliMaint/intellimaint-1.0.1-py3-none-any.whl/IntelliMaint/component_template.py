#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Component Template class definition

Author: rameshbk
Last modified: shweta, July 25nd, 2025
"""
from IntelliMaint.basemonitor import BaseMonitor

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from sklearn.preprocessing import PolynomialFeatures, RobustScaler, MinMaxScaler, StandardScaler
from sklearn.feature_selection import VarianceThreshold 
from sklearn.decomposition import PCA
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.cluster import AgglomerativeClustering, FeatureAgglomeration

class ComponentTemplate(BaseMonitor):
    """
    Enhanced template for creating component-specific monitoring systems
    with diagnostics and prognostics capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config (dict, optional): Configuration dictionary for initializing the component.

        Uses Config Parameters:
            Depends on specific derived implementations.

        Returns:
            None
        """
        super().__init__(config)
        
    def _initialize_components(self) -> None:
        """
        Initialize all monitoring and prognostic components for the workflow.

        Args:
            None

        Returns:
            None
        """
        # Monitoring components (from original template)
        self.data_acquisition = self._init_data_acquisition()
        self.signal_processing = self._init_signal_processing()
        self.feature_selection = self._init_feature_selection()
        self.feature_engineering = self._init_feature_engineering()
        self.anomaly_detection = self._init_anomaly_detection()
        self.health_indicator_construction = self._init_health_indicator_construction()
        self.degradation_detector = self._init_degradation_detector()
        
        # New diagnostic components
        self.fault_classifier = self._init_fault_classifier()
        self.diagnostic_evaluator = self._init_diagnostic_evaluator()
        
        # New prognostic components
        self.degradation_modeler = self._init_degradation_modeler()
        self.rul_estimation = self._init_rul_estimation()

    # Original initialization methods
    def _init_data_acquisition(self):
        """Initialize data loader - must be implemented by specific component."""
        raise NotImplementedError("Data acquisition initialization not implemented")

    def _init_signal_processing(self):
        """Initialize signal enhancement - must be implemented by specific component."""
        raise NotImplementedError("Signal enhancement initialization not implemented")

    def _init_feature_selection(self):
        """Initialize feature selection - must be implemented by specific component."""
        raise NotImplementedError("Feature Selection initialization not implemented")

    def _init_feature_engineering(self):
        """Initialize feature engineering - must be implemented by specific component."""
        raise NotImplementedError("Feature engineering initialization not implemented")

    def _init_anomaly_detection(self):
        """Initialize anomaly detection - must be implemented by specific component."""
        raise NotImplementedError("Anomaly detection initialization not implemented")

    def _init_health_indicator_construction(self):
        """Initialize Health Indicator Construction - must be implemented by specific component."""
        raise NotImplementedError("Health Indicator Construction initialization not implemented")

    def _init_degradation_detector(self):
        """Initialize feature extractor - implemented by specific component."""
        raise NotImplementedError("SOM Anomaly detection initialization not implemented")
    
    # Initialization methods for diagnostics
    def _init_fault_classifier(self):
        """Initialize fault classifier - must be implemented by specific component."""
        raise NotImplementedError("Fault classifier initialization not implemented")
    
    def _init_diagnostic_evaluator(self):
        """Initialize diagnostic evaluator - must be implemented by specific component."""
        raise NotImplementedError("Diagnostic evaluator initialization not implemented")
    
    # Initialization methods for prognostics
    def _init_degradation_modeler(self):
        """Initialize degradation modeler - must be implemented by specific component."""
        raise NotImplementedError("Degradation modeler initialization not implemented")
    
    def _init_rul_estimation(self):
        """Initialize RUL predictor - must be implemented by specific component."""
        raise NotImplementedError("RUL predictor initialization not implemented")
    
    def validate_config(self) -> bool:
        """Validate component configuration."""
        raise NotImplementedError("Configuration validation not implemented")

    def monitor(self) -> Dict[str, Any]:
        """
        Run the complete monitoring process using all initialized modules.

        Args:
            extra_args (dict): Additional arguments for feature engineering or health indicator construction.

        Uses Config Parameters:
            "numeric_only" (bool, optional): If true, restricts features to numeric-only data.

        Returns:
            dict: Results containing extracted features, anomaly detection,
                and health indicator for all input files.

        Raises:
            ValueError: If mandatory modules are not implemented.
            RuntimeError: If no input files or no features are found.
        """
        try:
            # ==== Data Acquisition ====
            if self.data_acquisition is None:
                raise ValueError("Data Acquisition not implemented")
            else:
                file_list = self.data_acquisition.get_file_list()

            if not file_list:
                msg = "No input files found for processing"
                self.logger.error(msg)
                raise RuntimeError(msg)                
            
            all_features = []
            all_file_data = []
            all_file_names = []

            for file_path in file_list:
                try:
                    data = self.data_acquisition.load_file_data(file_path)
                    if data is None:
                        self.logger.warning("File {} is empty".format(file_path))

                    if "numeric_only" in self.config and self.config.get("numeric_only"):
                        data = data.apply(pd.to_numeric, errors='coerce').dropna()  # Ensure numeric data

                    # ==== Feature Engineering ====
                    if self.feature_engineering:
                        features = self.feature_engineering.extract_features_from_file(data)
                    else:
                        raise ValueError("Feature engineering not implemented")

                    all_features.append(features)
                    all_file_data.append(data)
                    all_file_names.append(file_path) 

                except Exception as fe:
                    self.logger.error(f"Error processing file {file_path}: {str(fe)}", exc_info=True)
                    continue
            
            if not all_features:
                msg = "No features extracted from any files."
                self.logger.error(msg)
                raise RuntimeError(msg)
            
            # # Convert to DataFrame
            features_df = pd.DataFrame(all_features)
            self.logger.debug(f"Extracted features shape: {features_df.shape}")
            self.logger.debug(f"Extracted features columns: {features_df.columns.tolist()}")
            
            # === Feature Selection ===
            if self.feature_selection and self.feature_selection.feat_select:
                       
                # === Compute Monotonicity and select features based on that ===
                monotonic_score = self.feature_selection.calculate_monotonicity(features_df)
                
                # Sort features by monotonicity score (descending)
                sorted_monotonic = sorted(monotonic_score.items(), key=lambda x: x[1], reverse=True)

                # Print top N features (e.g., top 5)
                num_feat = 7
                for feature, score in sorted_monotonic[:num_feat]:
                    self.logger.info(f"Monotonic Feature: {feature}, Score: {score:.3f}")

                features_df = features_df[[col for col, _ in sorted_monotonic[:num_feat]]]
            
            features_df.insert(0, "TimeStamp", all_file_names)  # Optional: Store filenames

            # === Optional: Anomaly Detection ===
            if self.anomaly_detection:
                detection_results = self.anomaly_detection.set_baseline(features_df)
            else:
                detection_results = None

            # === Optional: Health Indicator Construction ===
            if self.health_indicator_construction:
                health_indicator = self.health_indicator_construction.construct_health_indicator(features_df)
            else:
                health_indicator = None


            return {
                'features': features_df,
                'detection': detection_results,
                'health_indicator': health_indicator
            }

        except Exception as e:
            self.logger.error(f"Error in monitoring process: {str(e)}")
            raise
     
    def predict_rul(self, hi):
        """
        Predict Remaining Useful Life (RUL) of the component using the selected estimator.

        Args:
            rul_args (dict): Arguments required for RUL prediction, e.g., monitoring and diagnostic results.

        Returns:
            dict: RUL prediction results, including intervals and expected failure mode.

        Raises:
            Exception: For any failures in RUL prediction workflow.
        """
        try:
            # Predict RUL
            if self.rul_estimation:
                if self.rul_estimation.prediction_method == "gpr":
                    rul_prediction = self.rul_estimation.predict_rul_gpr(hi)
                elif self.rul_estimation.prediction_method == "ensemble":
                    rul_prediction = self.rul_estimation.predict_rul_ensemble(hi)
                
                
            return rul_prediction
            
        except Exception as e:
            self.logger.error(f"Error in RUL prediction process: {str(e)}")
            raise
    
    def full_phm_analysis(self) -> Dict[str, Any]:
        """
        Perform a complete Prognostics and Health Management (PHM) analysis.
        This includes monitoring, diagnostics, and prognostics in one workflow.
        
        Returns:
            Dictionary containing comprehensive results from all PHM stages.
        """
        try:
            # Step 1: Monitoring
            monitoring_results = self.monitor()
            
            # Step 2: Diagnostics
            diagnostic_results = self.diagnose(monitoring_results)
            
            # Step 3: Prognostics (if fault detected)
            if diagnostic_results.get('fault_detected', False):
                prognostic_results = self.predict_rul(
                    monitoring_results, 
                    diagnostic_results
                )
            else:
                prognostic_results = {
                    'rul': None,
                    'message': 'No fault detected, RUL prediction skipped'
                }
            
            return {
                'monitoring': monitoring_results,
                'diagnostics': diagnostic_results,
                'prognostics': prognostic_results,
                'timestamp': pd.Timestamp.now(),
                'component_type': self.__class__.__name__.replace('Monitor', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error in PHM analysis: {str(e)}")
            raise