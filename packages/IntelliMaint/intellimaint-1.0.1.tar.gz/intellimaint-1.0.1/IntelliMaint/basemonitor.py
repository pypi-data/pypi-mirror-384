#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class definition

Author: rameshbk
Last modified: rachana, July 18th, 2025
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import kurtosis, skew
from scipy.fftpack import fft
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Tuple
import logging
import matplotlib.pyplot as plt


class BaseMonitor(ABC):
    """Base class for all monitoring implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {} # Store configuration
        self.logger = self._setup_logger()
        self._initialize_components()

    @abstractmethod
    def _initialize_components(self) -> None:
        """Initialize all required monitoring components (e.g., data loader)."""
        pass
    
    @abstractmethod
    def monitor(self) -> None:
        pass
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
