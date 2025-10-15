#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anomaly Detection core class definition

Author: rameshbk
Last modified: Rachana, 18th August, 2025
"""
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import fft
from scipy.signal import butter, lfilter, savgol_filter, hilbert
from scipy.stats import zscore, skew, kurtosis
import logging
from IntelliMaint.utils import Utils

class SignalSeparation:
    """
    A comprehensive data preprocessing class that handles signal filtering,
    smoothing, and normalization for vibration data analysis.
    """
    def __init__(self, config=None, verbose=False):
        """
        Initialize the preprocessing pipeline with configurable Parameters.

        Args:
            config : dict, optional
                Dictionary containing necessary parameters for signal preprocessing.
                Any provided values will overwrite the defaults.

        Configurable Parameters:
            sampling_rate(int) : Sampling rate of the signal in Hz.
                Default    : 20480

            low_cutoff_freq(int) : Low cutoff frequency for filtering.
                Default    : 50

            high_cutoff_freq(int) : High cutoff frequency for filtering.
                Default    : 100

            lowpass_filter_order(int) : Order of the Butterworth low pass filter.
                Default    : 4

            highpass_filter_order(int) : Order of the Butterworth high passfilter.
                Default    : 4

            bandpass_filter_order(int) : Order of the bandpass filter.
                Default    : 4

            ar_filter_order(int) : Order of the autoregressive filter.
                Default    : 4

            savgol_window(int) : Window size for Savitzky-Golay filter.
                Default    : 51

            savgol_polyorder(int) : Polynomial order for Savitzky-Golay filter.
                Default    : 3

            outlier_method(str) : Method for handling outliers ('zscore' or 'iqr').
                Default    : 'zscore'

            outlier_threshold(int) : Threshold value for outlier detection.
                Default    : 3
        """
        default_config = {
            "sampling_rate": 20480,
            "low_cutoff_freq": 50,
            "high_cutoff_freq": 100,
            "lowpass_filter_order": 4,
            "highpass_filter_order": 4,
            "bandpass_filter_order": 4,
            "ar_filter_order": 4,
            "savgol_window": 51,
            "savgol_polyorder": 3,
            "outlier_method": 'zscore',
            "outlier_threshold": 3
        }
        self.config = {**default_config, **(config or {})}

        self.verbose = verbose

        self.ut = Utils(verbose=verbose)
        self.logger = self.ut.get_logger(self.__class__.__name__)
        self._print_debug = self.ut.print_debug

        if self.verbose:
            print(f"[DEBUG] SignalSeparation initialized with config: {self.config}")
        self.logger.info(f"Initialized SignalSeparation with config: {self.config}")

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def preprocess(self, signal, operations=None, **kwargs):
        """
        Main preprocessing pipeline that handles signal processing operations.

        Args:
            signal: Input signal (DataFrame or numpy array)
            operations: List of preprocessing operations to apply
            kwargs: Additional Args: for each operation
        """
        self.logger.info(f"Starting preprocessing with operations={operations}")
        if operations is None:
            operations = ['lowpass_filter', 'smooth', 'normalize']

        if isinstance(signal, pd.DataFrame):
            self.logger.debug("Signal is a Dataframe")
            processed_df = pd.DataFrame()
            for column in signal.columns:
                self.logger.debug(f"Processing column: {column}")
                processed_channel = self.preprocess(signal[column].values, operations, **kwargs)
                processed_df[column] = processed_channel
            return processed_df

        processed_signal = signal.copy()
        for operation in operations:
            self.logger.debug(f"Applying operation: {operation}")
            if operation == 'lowpass_filter':
                processed_signal = self.lowpass_filter(processed_signal, **kwargs)
            elif operation == 'smooth':
                processed_signal = self.apply_savgol_filter(processed_signal, **kwargs)
            elif operation == 'normalize':
                processed_signal = self.normalize_data(processed_signal, **kwargs)
        
        self.logger.info(f"Preprocessing with operations={operations} complete")
        return processed_signal

    def lowpass_filter(self, signal):
        """
        Apply Butterworth low-pass filter to remove high-frequency noise.

        Args:
            signal: Input signal to filter

        Uses Config Parameters:
            lowpass_filter_order: Order of the Butterworth lowpass filter
            cutoff_frequency: Cutoff frequency in Hz
            sampling_rate: Sampling rate in Hz

        Returns:
            Filtered signal
        """
        self._print_debug("Applying low-pass filter")

        low_cutoff_freq = self.config['low_cutoff_freq']
        sampling_rate = self.config['sampling_rate']
        order = self.config['lowpass_filter_order']

        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Low Pass Filter: Signal is a Dataframe")
            signal = signal.values

        signal = np.asarray(signal)
        
        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        normalized_cutoff = low_cutoff_freq / (sampling_rate / 2)
        b, a = butter(order, normalized_cutoff, btype='low', analog=False)
        filtered_data = lfilter(b, a, signal)

        self._print_debug(f"Low-pass filter applied: cutoff={low_cutoff_freq}Hz, order={order}")

        return filtered_data
    
    def highpass_filter(self, signal):
        """
        Apply a high-pass filter to remove low-frequency components.

        Args:
            signal: Input signal to filter

        Uses Config Parameters:
            high_cutoff_freq: High cutoff frequency in Hz
            sampling_rate: Sampling rate in Hz
            order: Order of the high pass filter

        Returns:
            Filtered signal
        """
        self._print_debug("Applying high-pass filter")

        cutoff_frequency = self.config['high_cutoff_freq']
        sampling_rate = self.config['sampling_rate']
        order = self.config['highpass_filter_order']

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("High pass filter: Signal is a Dataframe")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        normalized_cutoff = cutoff_frequency / (sampling_rate / 2)
        b, a = butter(order, normalized_cutoff, btype='high', analog=False)
        filtered_signal = lfilter(b, a, signal)

        self._print_debug(f"High-pass filter applied: cutoff={cutoff_frequency}Hz, order={order}")

        return filtered_signal

    def bandpass_filter(self, signal):
        """
        Apply a band-pass filter to retain only frequencies between the specified bounds.

        Args:
            signal: Input signal to filter

        Uses Config Parameters:
            low_cutoff_freq: Low cutoff frequency in Hz
            high_cutoff_freq: High cutoff frequency in Hz
            sampling_rate: Sampling rate in Hz
            order: Order of the filter

        Returns:
            Filtered signal
        """
        self._print_debug("Applying band-pass filter")

        low_cutoff_freq = self.config['low_cutoff_freq']
        high_cutoff_freq = self.config['high_cutoff_freq']
        sampling_rate = self.config['sampling_rate']
        order = self.config['bandpass_filter_order']

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Band pass filter: Signal is a Dataframe")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        normalized_low_cutoff = low_cutoff_freq / (sampling_rate / 2)
        normalized_high_cutoff = high_cutoff_freq / (sampling_rate / 2)
        b, a = butter(order, [normalized_low_cutoff, normalized_high_cutoff], btype='band', analog=False)
        filtered_signal = lfilter(b, a, signal)

        self._print_debug(f"Band-pass filter applied: low cutoff={normalized_low_cutoff}Hz, high cutoff={normalized_high_cutoff}Hz, order={order}")
        return filtered_signal
    
    def apply_savgol_filter(self, signal):
        """
        Apply Savitzky-Golay filter for smooth signal denoising.

        Args:
            data: Input signal to smooth

        Uses Config Parameters:
            window_length: Length of the filter window
            polyorder: Order of the polynomial

        Returns:
            Smoothed signal
        """
        self.logger.debug("Applying Savgol filter")

        window_length = self.config['savgol_window']
        polyorder = self.config['savgol_polyorder']

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Savgol Filter: Signal is a Dataframe")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)


        # Ensure window length is odd
        if window_length % 2 == 0:
            window_length += 1

        # Ensure window length is not too large for the data
        if window_length > len(signal):
            window_length = len(signal) - 1 if len(signal) % 2 == 0 else len(signal)
            polyorder = min(polyorder, window_length - 1)
        
        self._print_debug(f"Savgol filter applied")
        return savgol_filter(signal, window_length, polyorder)
    
    def normalize_data(self, signal):
        """
        Normalize data using robust scaling method.

        Args:
            data: Input signal to normalize

        Returns:
            Normalized signal
        """
        self._print_debug("Normalize data")
        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Normalize data: Signal is Dataframe")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)
        
        mean = np.mean(signal)
        std = np.std(signal)
        self._print_debug(f"After normalizing, Mean={mean} and standard deviation={std}")
        return (signal - mean) / (std + 1e-10)

    def ar_filter(self, signal):
        """
        Apply an Auto-Regressive (AR) filter to the signal for noise reduction 
        and feature enhancement by identifying the AR model with the highest 
        kurtosis in the residual.
    
        Args:
            signal (ndarray): Input signal array.

        Uses Config Parameters:
            ar_filter_order : Order of the autoregressive filter
    
        Returns:
            ndarray: Residual signal after applying the AR filter.
        """
        self._print_debug("Applying AR filter")
        max_order = self.config['ar_filter_order']
        best_order = None
        max_kurtosis = -np.inf

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("AR filter: Signal is Dataframe")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        for order in range(1, max_order + 1):
            ar_coeffs = np.polyfit(signal[:-1], signal[1:], order)
            residual = signal[order:] - np.polyval(ar_coeffs, signal[:-order])
            k = kurtosis(residual)

            if k > max_kurtosis:
                max_kurtosis = k
                best_order = order

        ar_coeffs = np.polyfit(signal[:-best_order], signal[best_order:], best_order)
        residual = signal[best_order:] - np.polyval(ar_coeffs, signal[:-best_order])
        
        self._print_debug(f"AR Filter, ar coefficient={ar_coeffs}")
        return residual

    def handle_outliers(self, signal):
        """
        Handle outliers in the signal data.

        Args:
            signal: Input signal or DataFrame

        Uses Config Parameters:
            method: Method for outlier detection ('zscore' or 'iqr' supported)
            threshold: Threshold for outlier detection

        Returns:
            Tuple of (cleaned_data, outlier_mask)
        """
        self._print_debug("Handling Outliers")
        method = self.config['outlier_method']
        threshold = self.config['outlier_threshold']
        
        if not isinstance(signal, pd.DataFrame):
            self.logger.debug("Handling Outliers: Signal is a Dataframe")
            signal = pd.DataFrame(signal)

        cleaned_data = pd.DataFrame()
        outliers = pd.DataFrame()

        # Process each channel independently
        for column in signal.columns:
            channel_data = signal[column].values

            if method == 'zscore':
                #channel_data = pd.to_numeric(data[column], errors='coerce')
                # Calculate z-scores for current channel
                z_scores = np.abs(zscore(channel_data, nan_policy='omit'))
                channel_outliers = z_scores > threshold

            elif method == 'iqr':
                # Calculate IQR for current channel
                q1 = np.percentile(channel_data, 25)  # First quartile (Q1)
                q3 = np.percentile(channel_data, 75)  # Third quartile (Q3)
                iqr = q3 - q1  # Interquartile range
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                channel_outliers = (channel_data < lower_bound) | (channel_data > upper_bound)

            else:
                self.logger.error("Unsupported method for outlier handling. Use 'zscore' or 'iqr'.")
                raise ValueError("Unsupported method for outlier handling. Use 'zscore' or 'iqr'.")

            # Clean and interpolate outliers
            channel_cleaned = channel_data.copy()
            channel_cleaned[channel_outliers] = np.nan

            # Interpolate missing values
            channel_cleaned = pd.Series(channel_cleaned).interpolate(
                method='linear',
                limit_direction='both'
            ).values

            # Store results
            cleaned_data[column] = channel_cleaned
            outliers[column] = channel_outliers

        self._print_debug(f"Outliers handled, outliers: {outliers.head}")
        return cleaned_data, outliers

class SignalEnhancement:
    def __init__(self, config=None, verbose=False):
        """
        Initialize the SignalEnhancement class with configuration parameters.

        Args:
            config : dict, optional
                Dictionary containing necessary parameters for signal processing. 
                Any provided values will overwrite the defaults.

        Configurable Parameters:
            sampling_rate (int) : Sampling rate of the signal in Hz.  
                Default    : 25600

            segment_length (int) : Length of each signal segment for analysis.  
                        Default    : 50

            filter_length (int) : Length of the filter used in preprocessing.  
                        Default    : 11

            iterations (int) : Number of iterations for enhancement processes.  
                        Default    : 10

            spectral_kurtosis_window_lengths (int) : Window length for spectral kurtosis computation.  
                        Default    : 256

            bearing_frequencies (list of int) : List of example bearing fault frequencies in Hz.  
                        Default    : [20, 40, 60]

            rpm (int) : Rotations per minute (RPM) of the machinery.  
                        Default    : 2000

            num_sidebands (int) : Number of sidebands to filter in difference signal calculation.  
                        Default    : 2
        """
        default_config = {
            'sampling_rate': 25600,
            'segment_length': 50,
            'filter_length': 11,
            'iterations': 10,
            'spectral_kurtosis_window_lengths': 256,
            'bearing_frequencies': [20, 40, 60],
            'rpm': 2000,
            'num_sidebands': 2
        }
        self.config = {**default_config, **(config or {})}

        self.verbose = verbose

        self.ut = Utils(verbose=verbose)
        self.logger = self.ut.get_logger(self.__class__.__name__)
        self._print_debug = self.ut.print_debug
        
        if self.verbose:
            print(f"[DEBUG] SignalEnhancement initialized with config: {self.config}")
        self.logger.info(f"Initialized SignalEnhancement with config: {self.config}")

    def _print_debug(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def dephase(self, signal):
        """
        Perform synchronous averaging to remove periodic components from the signal.
        
        Args:
            signal(np.ndarray) : Input signal to be dephased.

        Uses Config Parameters:
            segment_length (int) : Length of each signal segment for analysis.
            
            
        Returns:
            Dephased signal with periodic components removed.
        """
        self._print_debug("Performing dephase (synchronous averaging) operation")
        segment_length = self.config['segment_length']

        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Dephase: Signal is a Dataframe or Series")
            signal = signal.values
        
        signal = np.asarray(signal)
        
        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        n_segments = len(signal) // segment_length
        self.logger.debug(f"Dephase: Number of segments: {n_segments}, segment_length={segment_length}")
        
        segments = signal[:n_segments * segment_length].reshape(n_segments, segment_length)
        sync_avg = np.mean(segments, axis=0)
        sync_signal = np.tile(sync_avg, n_segments)
        result = signal[:len(sync_signal)] - sync_signal

        self._print_debug(f"Dephase Operation complete with result: {result}")
        return result

    def minimum_entropy_deconvolution(self, signal):
        """
        Apply an iterative minimum entropy deconvolution (MED) filter to enhance fault signatures.

        Args:
            signal (np.ndarray) : Input signal to be filtered.

        Uses Config Parameters:
            filter_length (int) : Length of the filter used in preprocessing.  
            iterations (int) : Number of iterations for enhancement processes. 
                
        Returns:
            Filtered signal after MED.
        """
        self._print_debug("Applying Minimum Entropy Deconvolution")
        
        filter_length = self.config['filter_length']
        iterations = self.config['iterations']
        
        self._print_debug(f"MED params: filter_length={filter_length}, iterations={iterations}")

        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("MED: Signal is a Dataframe or Series")
            signal = signal.values
        
        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)
        
        x = signal.copy()
        h = np.zeros(filter_length)
        h[0] = 1.0
        for _ in range(iterations):
            y = np.convolve(x, h, mode='valid')
            norm_factor = np.sum(y**2)
            if norm_factor > 0:
                h_new = np.correlate(y**3, x) / norm_factor
                h = h_new / np.sqrt(np.sum(h_new**2))
        result = np.convolve(x, h, mode='valid')

        self._print_debug(f"MED operation complete with result: {result}")
        
        return result

    def angular_resample(self, signal):
        """
        Resamples the signal to achieve angular uniformity based on shaft frequency. The vibration signal is periodic relative to the phase of the rotating shaft and not to the
        time, as the rotational speed is never constant due to small speed fluctuations. To overcome this issue, angular resampling can be employed 
        as a transformation between two domains: time domain and cycle domain.
                
        Args:
            signal (np.ndarray) : Input signal to be resampled.

        Uses Config Parameters:
            sampling_rate (int) : Sampling rate of the signal in Hz.
            rpm (int) : Rotations per minute (RPM) of the machinery.
        
        Returns:
            Angularly resampled signal.
        """
        self._print_debug("Performing angular resampling")
        sampling_rate = self.config['sampling_rate']
        rpm = self.config.get('rpm', None)

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Angular Resample: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)
        
        if rpm is not None:
            shaft_frequency = rpm / 60
        else:
            spectrum = np.abs(np.fft.fft(signal))
            freqs = np.fft.fftfreq(len(signal), 1 / sampling_rate)
            shaft_frequency = freqs[np.argmax(spectrum[1:]) + 1]

        self.logger.debug(f"Angular resample: Shaft frequency: {shaft_frequency}")

        time = np.arange(len(signal)) / sampling_rate
        angles = 2 * np.pi * shaft_frequency * time
        uniform_angles = np.linspace(angles[0], angles[-1], len(signal))
        result = np.interp(uniform_angles, angles, signal)

        self._print_debug(f"Angular resampling operation complete with result: {result}")
        
        return result

    def calculate_envelope(self, signal):
        """
        Compute the envelope of the signal using the Hilbert transform.

        Args:
            signal (np.ndarray) : Input signal for envelope calculation.

        Returns:
            Envelope of the input signal.
        """     
        self._print_debug("Performing envelope calculation")  
        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Calculate envelope: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)
        
        envelope = np.abs(hilbert(signal))

        self._print_debug(f"Envelope calculated, shape: {envelope.shape}")
        
        return envelope

    def envelope_analysis(self, signal):
        """
        Performs envelope analysis on the signal to detect faults in rotating components 
        such as bearings and gears. This method extracts high-frequency modulations 
        caused by defects, computes the envelope spectrum, and marks characteristic 
        fault frequencies.
        
        Args:
            signal : np.ndarray
                Input signal array.

        Uses Configurable Parameters :  
            sampling_rate(int): Sampling rate of the signal in Hz.  
            bearing_frequencies(list): List of known fault frequencies (e.g., bearing defect frequencies, gear mesh frequencies).

        Returns:  
            None: Displays the envelope spectrum plot with fault frequency markers. 
        """
        self._print_debug("Performing envelope analysis")
        sampling_rate = self.config['sampling_rate']
        bearing_frequencies = self.config['bearing_frequencies']

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Envelope analysis: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        self._print_debug(f"Envelope Analysis: Bearing frequencies: {bearing_frequencies}")
        
         # Step 1: Get analytic signal and envelope
        analytic_signal = hilbert(signal)
        envelope_signal = np.abs(analytic_signal)
    
        # Step 2: Remove DC offset for spectrum analysis (not affecting the return value)
        envelope_for_fft = envelope_signal - np.mean(envelope_signal)
    
        # Step 3: Compute FFT of envelope
        fft_envelope = np.abs(fft(envelope_for_fft)) / len(envelope_for_fft) * 2
        fft_envelope = fft_envelope[:len(fft_envelope) // 2]
    
        # Step 4: Create frequency axis
        freq_axis = np.arange(len(fft_envelope)) / len(envelope_for_fft) * sampling_rate
    
        self._print_debug(f"Envelope analysis complete, freq_axis length={len(freq_axis)}")
        
        return envelope_signal
    
    
    def spectral_kurtosis_simplified(self, signal):
        """
        Compute the spectral kurtosis of the signal.
        
        Args:
            signal(np.ndarray) : Input signal for spectral kurtosis calculation.

        Uses Config Parameters:
            sampling_rate (int) : Sampling rate of the signal in Hz.
            spectral_kurtosis_window_lengths (int) : Window length for spectral kurtosis computation.
            
        Returns:
            tuple
                - spec_kurtosis (np.ndarray): Spectral kurtosis values.
                - freqs (np.ndarray): Corresponding frequency values.
        """
        self._print_debug("Performing spectral kurtosis-simpified")
        sampling_rate = self.config['sampling_rate']
        window_length = self.config['spectral_kurtosis_window_lengths']
        
        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Spectral Kurtosis Simplified: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        
        window = np.hanning(window_length)
        overlap = window_length // 2
        num_segments = (len(signal) - window_length) // overlap + 1
        spec_kurtosis = np.zeros(window_length // 2 + 1)

        for j in range(num_segments):
            segment = signal[j * overlap : j * overlap + window_length]
            segment = segment * window
            spectrum = np.abs(np.fft.fft(segment))[:window_length // 2 + 1]
            self._print_debug(f"SK Simplified: spectrum shape: {spectrum.shape}, mean shape: {(spectrum**2).mean().shape}")

            spec_kurtosis += (spectrum**4) / ((spectrum**2).mean()**2)

        spec_kurtosis /= num_segments
        freqs = np.arange(window_length // 2 + 1) * sampling_rate / window_length
        
        self._print_debug(f"Spectral Kurtosis - simplified complete, with freqs: {freqs}")

        return spec_kurtosis, freqs
    

    def spectral_kurtosis(self, signal):
        """
        Compute the spectral kurtosis of the signal.
        
        Args:
            signal(np.ndarray) : Input signal for spectral kurtosis calculation.

        Uses Config Parameters:
            sampling_rate (int) : Sampling rate of the signal in Hz.
            spectral_kurtosis_window_lengths (int) : Window length for spectral kurtosis computation.
            
        Returns:
            tuple
                - spec_kurtosis (np.ndarray): Spectral kurtosis values.
                - freqs (np.ndarray): Corresponding frequency values.
        """      
        self._print_debug("Performing spectral kurtosis")
        fs = self.config['sampling_rate']
        window_size = self.config['spectral_kurtosis_window_lengths']
        
        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Spectral Kurtosis: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)


        nseg = len(signal) // window_size
        if nseg < 1:
            self.logger.warning("Not enough data for spectral kurtosis calculation")
            return np.array([]), np.array([])

        v = signal[:nseg * window_size]
        segments = v.reshape(nseg, window_size)
        window = np.hanning(window_size + 1)[:-1]
        norm_factor = np.sqrt(np.sum(window**2))
        segments = segments * window[None, :] / norm_factor
        fft_segments = np.fft.fft(segments, axis=1)

        freqs = np.fft.fftfreq(window_size, d=1/fs)
        pos_mask = freqs >= 0
        freqs = freqs[pos_mask]
        fft_segments = fft_segments[:, pos_mask]
        psd = np.abs(fft_segments)**2

        mean_psd = np.mean(psd, axis=0)
        mean_psd2 = np.mean(psd**2, axis=0)
        SK = mean_psd2 / (mean_psd**2) - 2

        self._print_debug(f"Spectral kurtosis calculated, bins={len(freqs)}")
        return SK, freqs

    def convert_to_order_domain(self, signal):
        """
        Convert the signal to the order domain using the Fourier transform.

        Args:
            signal(np.ndarray) : Input signal array.
            
        Returns:
            tuple
                - orders (np.ndarray): Orders of the frequency components.
                - magnitude_spectrum (np.ndarray): Corresponding magnitude spectrum.
        """  
        self._print_debug("Convert signal to order")    
        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Signal to Order: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        spectrum = np.fft.fft(signal)
        orders = np.fft.fftfreq(len(signal)) * len(signal)
        
        self._print_debug(f"Order domain conversion complete, length={len(orders)}")
        return orders, np.abs(spectrum)

    def synchronous_average(self, signal):
        """
        Perform synchronous averaging to reduce noise and extract periodic components.

        Args:
            signal(np.ndarray) : Input signal for averaging.

        Uses Config Parameters:
            sampling_rate (int) : Sampling rate of the signal in Hz.
            rpm (int) : Rotations per minute (RPM) of the machinery.
            
        Returns:
            Synchronously averaged signal.
        """
        self._print_debug(f"Synchronous average calculation")
        rpm = self.config['rpm']
        sampling_rate = self.config['sampling_rate']

        # Convert pandas DataFrame or Series to NumPy array
        if isinstance(signal, (pd.DataFrame, pd.Series)):
            self.logger.debug("Sync Average: Signal is a Dataframe or Series")
            signal = signal.values

        # Ensure input is a NumPy array
        signal = np.asarray(signal)

        # Flatten 2D arrays to 1D; keep 1D as-is
        signal = self.ut.ensure_1d_vector(signal)

        cycle_length_in_time = 60 / rpm
        cycle_length = int(cycle_length_in_time * sampling_rate)
        num_cycles = len(signal) // cycle_length
        reshaped_signal = signal[:num_cycles * cycle_length].reshape(num_cycles, cycle_length)
        avg_signal = np.mean(reshaped_signal, axis=0)
        
        self._print_debug(f"Synchronous average complete, cycles: {num_cycles}")
        return avg_signal

    def calculate_difference_signal(self, averaged_signal):
        """
        Calculate the difference signal by filtering out specific sidebands.

        Args:
            averaged_signal(np.ndarray): Synchronously averaged signal.
 
        Uses Config Parameters:
            num_sidebands (int) : Number of sidebands to filter in difference signal calculation.

        Returns:
            Difference signal with sidebands removed.
        """        
        num_sidebands = self.config['num_sidebands']
        fft_spectrum = np.fft.fft(averaged_signal)
        freqs = np.fft.fftfreq(len(averaged_signal))
        filtered_spectrum = np.copy(fft_spectrum)
        for harmonic in range(1, num_sidebands + 1):
            harmonic_indices = np.where(np.abs(freqs - harmonic) < 0.05)
            filtered_spectrum[harmonic_indices] = 0
        result = np.fft.ifft(filtered_spectrum).real
        
        self._print_debug(f"Difference signal calculation complete, result: {result}")
        return result
