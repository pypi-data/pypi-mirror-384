#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Analysis core class definition

Author: rameshbk
Last modified: rachana, Aug 12th, 2025
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import os as os
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import warnings
import logging
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from sklearn import linear_model

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input

from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import tensorflow as tf
from minisom import MiniSom
import scipy.signal
from IntelliMaint.utils import Utils

class AutoEncoder:
	"""AutoEncoder model for unsupervised feature extraction and anomaly detection."""

	def __init__(self, verbose=False):
		"""Initialize AutoEncoder with optional verbose flag."""
		
		self.verbose = verbose

		ut = Utils(verbose=verbose)
		self.logger = ut.get_logger(self.__class__.__name__)
		self._print_debug = ut.print_debug
		
		if self.verbose:
			print(f"[DEBUG] DataAnalysis initialized")
		self.logger.debug(f"Initialized DataAnalysis")


	def _print_debug(self, msg):
		if self.verbose:
			print(f"[DEBUG] {msg}")

	def train(self, x, L1=100, L2=100, e_dim=2, a_func='relu', b_size=30, epochs=100, random_state=None):
		"""
		Train an autoencoder with two encoding and two decoding dense layers.

		Args:
			x (np.array or pd.DataFrame): Input raw data for training.
			L1 (int): Number of neurons in first dense layer (default 100).
			L2 (int): Number of neurons in second dense layer (default 100).
			e_dim (int): Dimension of latent representation (default 2).
			a_func (str): Activation function (default 'relu').
			b_size (int): Batch size (default 30).
			epochs (int): Number of training epochs (default 100).
			random_state (int, optional): Seed for random operations for reproducibility. Defaults to None.

		Returns:
			tuple:
				AE: Training history object.
				model: Trained Keras autoencoder model.
				scaler: Scaler object used for data normalization.
		"""
		if random_state is not None:
			np.random.seed(random_state)
			tf.random.set_seed(random_state)
			self.logger.debug(f"Set random seed to {random_state} for numpy and tensorflow")

		self.logger.info("Starting autoencoder training")
		self.logger.debug(f"Training parameters: L1={L1}, L2={L2}, e_dim={e_dim}, a_func={a_func}, batch_size={b_size}, epochs={epochs}")
		self._print_debug(f"Training parameters: L1={L1}, L2={L2}, e_dim={e_dim}, a_func={a_func}, batch_size={b_size}, epochs={epochs}")

		x_train, x_test = train_test_split(x, test_size=0.2, random_state=random_state)
		self.logger.debug(f"Training data shape: {x_train.shape}, Test data shape: {x_test.shape}")
		self._print_debug(f"Training data shape: {x_train.shape}, Test data shape: {x_test.shape}")

		scaler = preprocessing.StandardScaler().fit(x_train)
		x_train = scaler.transform(x_train)
		x_test = scaler.transform(x_test)

		ncol = x_train.shape[1]
		input_dim = Input(shape=(ncol, ))

		# DEFINE THE ENCODER LAYERS
		encoded1 = Dense(L1, activation='linear')(input_dim)
		encoded2 = Dense(L2, activation=a_func)(encoded1)
		encoded3 = Dense(e_dim, activation=a_func)(encoded2)

		# DEFINE THE DECODER LAYERS
		decoded1 = Dense(L2, activation=a_func)(encoded3)
		decoded2 = Dense(L1, activation=a_func)(decoded1) 
		decoded3 = Dense(ncol, activation='linear')(decoded2)

		model = Model(inputs=input_dim, outputs=decoded3)
		model.compile(optimizer='SGD', loss='mse', metrics=['accuracy'])

		AE = model.fit(x_train, x_train, epochs=epochs, batch_size=b_size,
					   shuffle=True, validation_data=(x_test, x_test))
		training_loss = AE.history['loss']
		test_loss = AE.history['val_loss']

		self.logger.info("Finished autoencoder training")

		plt.figure()
		plt.plot(training_loss, 'r--')
		plt.plot(test_loss, 'b-')
		plt.legend(['Training Loss', 'Test Loss'])
		plt.xlabel('Epoch')
		plt.ylabel('Loss')
		plt.title('encoding_dim=' + str(e_dim))

		return AE, model, scaler

	def predict(self, model, scaler, data):
		"""
		Predicting target data from autoencoder model. \n
		
		Args:
			model : Pre trainedAutoencoder model\n
			scaler : Scaler used for scaling input data \n
			data : Data from csv/xlsx file \n

		Returns:
			RE(numpy.ndarray): Reconstruction error from the target data \n
		"""
		self.logger.info("Starting prediction")
		x = scaler.transform(data)
		pred = model.predict(x)
		RE = np.abs(pred - x)
		self.logger.info("Prediction completed")
		return RE


class SOM:

	def __init__(self, verbose=False):
		"""
		Initialize SOM with optional verbose flag and logging.
		"""
		self.verbose = verbose

		ut = Utils(verbose=verbose)
		self.logger = ut.get_logger(self.__class__.__name__)
		self._print_debug = ut.print_debug

		if self.verbose:
			print(f"[DEBUG] DataAnalysis initialized")
		self.logger.debug(f"Initialized DataAnalysis")


	def _print_debug(self, msg):
		if self.verbose:
			print(f"[DEBUG] {msg}")

	def train(self, x, w1=50, w2=50, sigma=0.1, lr=0.5, n_iter=500, random_state=203):
		"""
		Train a Self Organizing Map 

		Args:
			x (np.array or pd.DataFrame): Input feature data for training.
			w1 (int, optional): Width of SOM grid. Defaults to 50.
			w2 (int, optional): Height of SOM grid. Defaults to 50.
			sigma (float): Neighborhood radius (default 0.1).
			lr (float): Learning rate (default 0.5).
			n_iter (int): Number of training iterations (default 500).
			random_state (int, optional): Seed for random operations for reproducibility. Defaults to None.

		Returns:
			tuple:
				som: Trained MiniSom object.
				scaler: Scaler used to normalize input data.
		"""
		self.logger.info(f"Starting SOM training with grid size ({w1}, {w2}), sigma={sigma}, lr={lr}, iterations={n_iter}")
		self.logger.debug(f"Input data shape: {x.shape}")
		self._print_debug(f"Input data shape: {x.shape}")

		scaler = preprocessing.MinMaxScaler()
		x = scaler.fit_transform(x)
		som = MiniSom(w1, w2, x.shape[1], sigma=sigma, learning_rate=lr, random_seed=random_state)
		som.random_weights_init(x)
		som.train_random(x, n_iter, verbose=self.verbose) 

		self.logger.info("Finished SOM training")
		return som, scaler

	def predict(self, som, data, scaler):
		"""
		Prediction from SOM model

		Args:
			som: Trained SOM model.
			data (pd.DataFrame or np.array): Input data to predict on.
			scaler: Scaler used for input data normalization.

		Returns:
			np.array: Quantization error for each input sample.
		"""
		self.logger.info("Starting SOM prediction")
		x = scaler.transform(data)
		error = som.quantization(x)
		q_error = self.quant_error(x, error)
		self.logger.info(f"Completed SOM prediction with error {q_error}")
		return q_error

	def quant_error(self, x, qant):
		"""
		Compute quantization error between input data and prototypes.

		Args:
			x (np.array): Input data points.
			quant (np.array): Quantized/best matching unit vectors.

		Returns:
			np.array: Quantization error per data point.
		"""
		self.logger.info("Computing quantization error")
		qe = []  # quantization error
		for i in range(len(x)):
			qe.append(np.linalg.norm(qant[i] - x[i]))
		return np.array(qe)