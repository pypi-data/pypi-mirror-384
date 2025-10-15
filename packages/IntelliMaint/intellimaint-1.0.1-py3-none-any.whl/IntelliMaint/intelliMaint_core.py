"""
IntelliMaint Core Module
------------------------

Provides a central entry point to IntelliMaint by exposing its core components,
including data acquisition, signal processing, feature engineering, feature selection, anomaly 
detection, health indicator construction, data analysis and RUL estimation.

Example:
    from intellimaint_core import DataAcquisition, TimeDomain, GPRDegradationModel
"""

from IntelliMaint.data_acquisition import DataAcquisition
from IntelliMaint.signal_processing import SignalSeparation, SignalEnhancement
from IntelliMaint.feature_engineering import TimeDomain, FrequencyDomain
from IntelliMaint.feature_selection import FeatureSelection
from IntelliMaint.anomaly_detection import COSMOAnomalyDetection, SOMAnomalyDetection
from IntelliMaint.health_indicator import HealthIndicatorConstructor
from IntelliMaint.data_analysis import SOM
from IntelliMaint.rul_estimation import GPRDegradationModel


__all__ = ['DataAcquisition', 'SignalSeparation', 'SignalEnhancement' ,'TimeDomain', 'FrequencyDomain', 'FeatureSelection', 'COSMOAnomalyDetection', 'SOMAnomalyDetection', 'HealthIndicatorConstructor', 'SOM', 'GPRDegradationModel']
