import requests

# Base URL of your Flask app running locally
base_url = "http://127.0.0.1:5000/api/v1/data_analysis/"

# Sample data for testing the AutoEncoder training
autoencoder_train_data = {
    "data": [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 1.0, 1.1, 1.2]
    ],
    "L1": 100,
    "L2": 100,
    "e_dim": 2,
    "a_func": "relu",
    "b_size": 10,
    "epochs": 10
}

# Send POST request to train the AutoEncoder
response = requests.post(base_url + "train_autoencoder", json=autoencoder_train_data,timeout=120)
print("Train AutoEncoder Response:", response.json())

# Prepare data for predicting using the trained AutoEncoder
autoencoder_predict_data = {
    "data": [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 1.0, 1.1, 1.2]
    ]
}

# Send POST request to predict using the AutoEncoder
response = requests.post(base_url + "predict_autoencoder", json=autoencoder_predict_data, timeout=120)
print("Predict AutoEncoder Response:", response.json())
