#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Engineering core class definition

Author: rameshbk
Last modified: rachana, Aug 12th, 2025
"""
import pandas as pd
import os as os
import numpy as np
import sys
import math
import statistics as st
import scipy as sp
import scipy.stats as sps
from scipy.stats import kurtosis
from scipy.stats import skew
from scipy.signal import welch
from scipy.fft import fft, fftfreq
import logging

from IntelliMaint.utils import Utils

class TimeDomain:
    def __init__(self, config=None, verbose=False):
        """
        Initialize the TimeDomain class with configurable parameters.

        Args:
            config : dict, optional
                Dictionary containing configuration parameters such as window length, frame size, and frame shift.
                If not provided, default values will be used.

            Configurable Parameters:
                sampling_rate (int): Required. Sampling rate (in Hz) of the input signal.
 
                window_len(int): Length of the signal window to consider.
                    Default : Same as `sampling_rate` if not explicitly provided.

                frame_size(int): Size of each window frame.
                    Default :  Same as `sampling_rate` if not explicitly provided.
                              (use same value as window_len for 'no Overlap')

                frame_shift(int): Number of samples to shift between frames.
                    Default : 50
    
        """
        self.verbose = verbose

        ut = Utils(verbose=verbose)
        self.logger = ut.get_logger(self.__class__.__name__)
        self._print_debug = ut.print_debug

        # sampling_rate is required
        if not config or 'sampling_rate' not in config:
            msg = "sampling_rate must be specified in the configuration."
            self.logger.error(msg)
            raise ValueError(msg)

        sampling_rate = config['sampling_rate']

        default_config = {
            'window_len': sampling_rate,
            'frame_size': sampling_rate,
            'frame_shift': 50
        }

        # Merge provided config with default values
        self.config = {**default_config, **(config or {})}
        self.utils = Utils()

        if self.verbose:
            print(f"[DEBUG] Time Domain initialized with config: {self.config}")
        self.logger.debug(f"Intialized Time Domain with config: {self.config}")

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def extract_timefeatures_streaming(self, data):
        """
        Extract time-domain features for a streaming signal.

        Args:
            data (pandas.DataFrame or ndarray) : Input signal data.

        Returns:
            dict
                Extracted time-domain features: rms, mean, variance, crest factor, kurtosis, skewness,
                peak-to-peak, shape factor, impulse factor.
        """
        # Ensure data is a NumPy array
        # if isinstance(data, np.ndarray):
        #     data = data  # Already a NumPy array, no need to convert
        # else:
        #     data = np.array(data)  # Convert to NumPy array if it's not
        data = self.utils.ensure_column_vector(data)

        features = {
            "RMS": self.get_rms(data),
            "Mean": self.get_mean(data),
            "Variance": self.get_variance(data),
            "Crest Factor": self.get_crestfactor(data),
            "Kurtosis": self.get_kurtosis(data),
            "Skewness": self.get_skewness(data),
            "Peak-to-Peak": self.get_peak_to_peak(data),
            "Shape Factor": self.get_shape_factor(data),
            "Impulse Factor": self.get_impulse_factor(data),
        }
        return features

    def extract_timefeatures(self, data):
        """
        Extract time-domain features using 'Configurable Windowed Chunks'.

        Args:
            data(pandas.DataFrame) : Input signal data in dataframe format.

        Configurable Parameters:
            window_len(int): Length of the signal window to consider.
            frame_size(int): Size of each window frame.
            frame_shift(int): Number of samples to shift between frames.
            
        Returns: 
            dict
                Extracted time-domain features for each window.
        """
        # Ensure data is a NumPy array
        # if isinstance(data, np.ndarray):
        #     data = data  # Already a NumPy array, no need to convert
        # else:
        #     data = np.array(data)  # Convert to NumPy array if it's not
        data = self.utils.ensure_column_vector(data)
        
        window_len = self.config.get('window_len') 
        frame_shift = self.config.get('frame_shift', window_len)  #use same value as window_len for 'no Overlap')
        frame_size = self.config.get('frame_size')
        data = self.get_chunks(data, frame_size=frame_size, frame_shift=frame_shift)

        features = {
            "RMS": self.get_rms(data),
            "Mean": self.get_mean(data),
            "Variance": self.get_variance(data),
            "Crest Factor": self.get_crestfactor(data),
            "Kurtosis": self.get_kurtosis(data),
            "Skewness": self.get_skewness(data),
            "Peak-to-Peak": self.get_peak_to_peak(data),
            "Shape Factor": self.get_shape_factor(data),
            "Impulse Factor": self.get_impulse_factor(data),
        }
        return features

    def get_chunks(self, data, frame_size=100, frame_shift=50):
        """
        Split the data into overlapping or non-overlapping chunks.

        Args:
            data : np.ndarray
            frame_size(int): Size of each window frame.
            frame_shift(int): Number of samples to shift between frames.
            

        Returns:
            np.ndarray
                3D array where each frame is one window.
        """
        self.logger.info("Creating chunks of the data")
        chunks = []
        data = self.utils.ensure_column_vector(data)
        if data.shape[0] < frame_size:
            msg= "The length of input vector is smaller than the analysis window length."
            self.logger.error(msg)
            raise ValueError(msg)
        for j in range(0, len(data) - frame_size, frame_shift):
            chunks.append(data[j:j + frame_size, :])
        self.logger.info("Created chunks")
        return np.array(chunks)

    def get_rms(self, data):
        """
        Computes the Root Mean Square (RMS) value of the signal, which is an indicator of energy content.
        
        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            rms (numpy.ndarray): root mean squared values
        """
        self._print_debug(f"Computing the rms: The number of dimensions in the data is {data.ndim}")
        if data.ndim == 3:
            return np.sqrt(np.mean(data**2, axis=1))
        return np.sqrt(np.mean(data**2, axis=0))

    def get_mean(self, data):
        """
        Computes the mean (average) value of the signal over time.
        
        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            mean (numpy.ndarray): mean values
        """
        self._print_debug(f"Computing the mean: The number of dimensions in the data is {data.ndim}")
 
        if data.ndim == 3:
            return np.mean(data, axis=1)
        return np.mean(data, axis=0)

    def get_variance(self, data):
        """
        Computes the variance of the signal, which measures how much the signal deviates from the mean.
        
        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            (numpy.ndarray): variance values
        """
        self._print_debug(f"Computing the variance: The number of dimensions in the data is {data.ndim}")

        if data.ndim == 3:
            return np.var(data, axis=1)
        return np.var(data, axis=0)

    def get_crestfactor(self, data):
        """
        Computes the crest factor, which is the ratio of the peak value to the RMS value of the signal.
        
        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            (numpy.ndarray): crestfactor values
        """
        self._print_debug(f"Computing the crest factor: The number of dimensions in the data is {data.ndim}")

        if data.ndim == 3:
            peaks = np.max(data, axis=1) 
        else:
            peaks = np.max(data, axis=0)
        rms = self.get_rms(data)
        return np.divide(peaks, rms)

    def get_kurtosis(self, data):
        """
        Computes the kurtosis of the signal, indicating the presence of sharp peaks.

        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            numpy.ndarray: Kurtosis values for each segment of the signal.
        
        """
        self._print_debug(f"Computing the kurtosis: The number of dimensions in the data is {data.ndim}")

        if data.ndim == 3:
            return kurtosis(data, axis=1)
        return kurtosis(data, axis=0)

    def get_skewness(self, data):
        """
        Computes the skewness of the signal, measuring its asymmetry.
        
        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            numpy.ndarray: Skewness values for each segment of the signal.
        
        """
        self._print_debug(f"Computing the skewness: The number of dimensions in the data is {data.ndim}")

        if data.ndim == 3:
            return skew(data, axis=1)
        return skew(data, axis=0)

    def get_peak_to_peak(self, data):
        """
        Computes the peak-to-peak value, which is the difference between the maximum and minimum value of the signal.
        
        Args:
            data (pandas.DataFrame): input data in the dataframe format.

        Returns:
            numpy.ndarray: Peak-to-peak values for each segment of the signal.

        """   
        self._print_debug(f"Computing the peak to peak value: The number of dimensions in the data is {data.ndim}")

        if data.ndim == 3:
            return np.ptp(data, axis=1)
        return np.ptp(data, axis=0)

    def get_shape_factor(self, data):
        """
        Computes the shape factor, which is the ratio of the RMS value to the mean absolute value of the signal.

        Args:
            data (pandas.DataFrame): input data in the dataframe format.

        Returns:
            numpy.ndarray: Shape factor values for each segment of the signal.

        """ 
        self._print_debug(f"Computing the shape factor: The number of dimensions in the data is {data.ndim}")

        rms = self.get_rms(data)
        mean_abs = np.mean(np.abs(data), axis=1) if data.ndim == 3 else np.mean(np.abs(data), axis=0)
        return np.divide(rms, mean_abs + 1e-10)

    def get_impulse_factor(self, data):
        """
        Computes the impulse factor, which is the ratio of the peak value to the mean absolute value of the signal.

        Args:
            data (pandas.DataFrame): input data in the dataframe format

        Returns:
            numpy.ndarray: Impulse factor values for each segment of the signal.

        """
        self._print_debug(f"Computing the impulse factor: The number of dimensions in the data is {data.ndim}")

        max_abs = np.max(np.abs(data), axis=1) if data.ndim == 3 else np.max(np.abs(data), axis=0)
        mean_abs = np.mean(np.abs(data), axis=1) if data.ndim == 3 else np.mean(np.abs(data), axis=0)
        return np.divide(max_abs, mean_abs + 1e-10)

class FrequencyDomain:
    """
    A class to compute various frequency-domain features, including bearing-specific frequencies.
    """

    def __init__(self, config, verbose=False):
        """
        Initialize the FrequencyDomainFeatures class with configurable parameters.

        Args:
            config (dict): Configuration dictionary with the following keys:
                - 'sampling_rate': Sampling rate of the signal.
                - 'Bd': Ball diameter (in meters).
                - 'Pd': Pitch diameter (in meters).
                - 'Nb': Number of balls.
                - 's': Shaft speed (in RPM).
                - 'a': Contact angle (in radians).
                - 'welch_nperseg': Number of points per segment for Welch's method (optional).
            verbose (bool): If True, enables extra debug print messages.
        """
        self.verbose = verbose

        ut = Utils(verbose=verbose)
        self.logger = ut.get_logger(self.__class__.__name__)
        self._print_debug = ut.print_debug

        self.config = config
        self.sampling_rate = config['sampling_rate']
        self.utils = Utils()

        # Set default values for bearing parameters if not provided
        self.Bd = config.get('Bd', 0.331)  
        self.Pd = config.get('Pd', 2.815)  
        self.Nb = config.get('Nb', 16)  
        self.s = config.get('s', 2000/60)  
        self.a = config.get('a', np.radians(15.17)) 

        if self.verbose:
            print(f"[DEBUG] Frequency Domain initialized with config: {self.config}")
        self.logger.debug(f"Initialized Frequency Domain with config: {self.config}")

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def freq2index(self, freq, signal_length):
        """
        Map a frequency to its corresponding index in the FFT array.

        Args:
            freq (float): Frequency to map.
            signal_length (int): Length of the input signal. #look into this make it direct input length = signal length 

        Returns:
            int: Index corresponding to the frequency.
        """
        step = self.sampling_rate / (signal_length * 2)
        idx = math.floor(freq / step)
        self.logger.debug(f"Mapping frequency {freq} Hz to index {idx}")
        return idx

    def get_fft(self, signal):
        """
        Compute the Fast Fourier Transform (FFT) of the signal.

        Args:
            signal (array-like): Input time-domain signal.

        Returns:
            tuple: (xf, yf), where:
                - xf (array): Frequencies.
                - yf (array): Amplitudes of the FFT.
        """
        signal = np.asarray(signal)  # Converts Pandas Series/DataFrame to NumPy array safely
        N = len(signal)
        xf = np.fft.fftfreq(N, d=1/self.sampling_rate)
        yf = fft(signal)

        self.logger.debug(f"Computed FFT with {N} points")
        return xf, np.abs(yf)

    def get_power_spectral_density(self, signal):
        """
        Compute the Power Spectral Density (PSD) using Welch's method.

        Args:
            signal (array-like): Input time-domain signal.

        Returns:
            tuple: (freqs, psd), where:
                - freqs (array): Frequencies.
                - psd (array): Power Spectral Density.
        """
        freqs, psd = welch(signal, fs=self.sampling_rate, nperseg=min(256, len(signal)))
        self.logger.debug(f"Computed PSD with {len(freqs)} frequency bins")
        return freqs, psd

    def get_total_power(self, freqs, psd):
        """
        Calculate the total power of the signal from the Power Spectral Density.

        Args:
            freqs (array): Frequencies.
            psd (array): Power Spectral Density.

        Returns:
            float: Total power of the signal.
        """
        total_power = np.trapezoid(psd, freqs)
        self.logger.debug(f"Total power calculated: {total_power}")
        return total_power

    def get_mean_frequency(self, freqs, psd):
        """
        Compute the mean frequency of the signal.

        Args:
            freqs (array): Frequencies.
            psd (array): Power Spectral Density.

        Returns:
            float: Mean frequency of the signal.
        """
        mean_freq = np.average(freqs, weights=psd)
        self.logger.debug(f"Mean frequency: {mean_freq}")
        return mean_freq

    def get_peak_frequency(self, freqs, psd):
        """
        Find the frequency with the highest power in the Power Spectral Density.

        Args:
            freqs (array): Frequencies.
            psd (array): Power Spectral Density.

        Returns:
            float: Frequency with the highest power.
        """
        peak_freq = freqs[np.argmax(psd)]
        self.logger.debug(f"Peak frequency: {peak_freq}")
        return peak_freq

    def get_frequency_entropy(self, psd):
        """
        Calculate the frequency entropy of the signal.

        Args:
            psd (array): Power Spectral Density.

        Returns:
            float: Frequency entropy.
        """
        psd_norm = psd / np.sum(psd)
        entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
        self.logger.debug(f"Frequency entropy: {entropy}")
        return entropy

    def get_dominant_frequency(self, xf, yf):
        """
        Find the dominant frequency in the FFT spectrum.

        Args:
            xf (array): Frequencies from FFT.
            yf (array): Amplitudes from FFT.

        Returns:
            float: Dominant frequency in the FFT spectrum.
        """
        dom_freq = xf[np.argmax(yf)]
        self.logger.debug(f"Dominant frequency: {dom_freq}")
        return dom_freq

    def extract_frequency_features(self, signal):
        """
        Extract general frequency-domain features from the signal.

        Args:
            signal (array-like): Input time-domain signal.

        Returns:
            dict: Extracted general frequency-domain features, including:
                - "Dominant Frequency"
                - "Total Power"
                - "Mean Frequency"
                - "Peak Frequency"
                - "Frequency Entropy"
        """
        self.logger.info("Extracting general frequency-domain features")
        xf, yf = self.get_fft(signal)
        freqs, psd = self.get_power_spectral_density(signal)

        general_features = {
            "Dominant Frequency": self.get_dominant_frequency(xf, yf),
            "Total Power": self.get_total_power(freqs, psd),
            "Mean Frequency": self.get_mean_frequency(freqs, psd),
            "Peak Frequency": self.get_peak_frequency(freqs, psd),
            "Frequency Entropy": self.get_frequency_entropy(psd),
        }
        self.logger.debug(f"Extracted features: {general_features}")
        self._print_debug(f"General freq features: {general_features}")
        return general_features

    def extract_bearing_features(self, signal):
        """
        Calculate bearing fault frequencies and extract their corresponding amplitudes from the FFT.

        Args:
            signal (array-like): Input time-domain signal.

        Returns:
            dict: Extracted bearing-specific features, including:
                - "FTF Amplitude"
                - "BPFI Amplitude"
                - "BPFO Amplitude"
                - "BSF Amplitude"
        """
        if self.Bd == 0 or self.Pd == 0 or self.Nb == 0 or self.s == 0:
            self.logger.error("Bearing frequency parameters not set correctly")
            raise ValueError("Bearing frequency parameters are not properly set.")

        # Compute bearing fault frequencies
        ratio = self.Bd / self.Pd * math.cos(self.a)
        ftf = self.s / 2 * (1 - ratio)  # Fundamental Train Frequency
        bpfi = self.Nb / 2 * self.s * (1 + ratio)  # Ball Pass Frequency Inner
        bpfo = self.Nb / 2 * self.s * (1 - ratio)  # Ball Pass Frequency Outer
        bsf = self.Pd / self.Bd * self.s / 2 * (1 - ratio**2)  # Ball Spacing Frequency

        self._print_debug(f"FTF={ftf}, BPFI={bpfi}, BPFO={bpfo}, BSF={bsf}")

        xf, yf = self.get_fft(signal)
        amps = np.abs(yf)
        N = len(signal)

        bearing_features = {
            "FTF Amplitude": amps[self.freq2index(ftf, N)],
            "BPFI Amplitude": amps[self.freq2index(bpfi, N)],
            "BPFO Amplitude": amps[self.freq2index(bpfo, N)],
            "BSF Amplitude": amps[self.freq2index(bsf, N)],
        }
        self.logger.debug(f"Bearing features: {bearing_features}")
        self._print_debug(f"Bearing features: {bearing_features}")
        return bearing_features