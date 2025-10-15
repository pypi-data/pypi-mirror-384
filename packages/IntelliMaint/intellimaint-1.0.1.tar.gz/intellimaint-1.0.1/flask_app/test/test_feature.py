import requests

# Base URL of your Flask app running locally
base_url = "http://127.0.0.1:5000/api/v1/feature_engineering/"

# Sample data for testing time domain features
time_domain_data = {
    "data": [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
}

# Sample data for testing frequency domain features
frequency_domain_data = {
    "data": [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
}

# Send POST request for time domain features
response = requests.post(base_url + "time_domain_features", json=time_domain_data)
print("Time Domain Response:", response.json())

# Send POST request for frequency domain features
response = requests.post(base_url + "frequency_domain_features", json=frequency_domain_data)
print("Frequency Domain Response:", response.json())
