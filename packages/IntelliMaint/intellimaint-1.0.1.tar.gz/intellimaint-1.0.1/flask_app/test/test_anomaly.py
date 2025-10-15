import requests

BASE = "http://127.0.0.1:5000/api/v1/anomaly_detection/"

#contains features for sample data
test_data = {
    "data": [
        [0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7],
        [0.8, 0.9, 1.0]
    ],
    "threshold": 0.5
}

response = requests.post(BASE + "train_cosmo", json=test_data)
if response.ok:
    print("Testing successful:", response.json())
else:
    print("Testing failed:", response.status_code, response.text)
test_data = {
    "data": [
        [0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7],
        [0.8, 0.9, 1.0]
    ]
}

response = requests.post(BASE + "test_cosmo", json=test_data)
if response.ok:
    print("Testing successful:", response.json())
else:
    print("Testing failed:", response.status_code, response.text)

streaming_data = {
    "data": [
        [0.3, 0.4, 0.5]
    ]
}

response = requests.post(BASE + "test_streaming", json=streaming_data)
if response.ok:
    print("Streaming test successful:", response.json())
else:
    print("Streaming test failed:", response.status_code, response.text)

# Sample data for nonstationary anomaly detection
nonstationary_data = {
    "data": [
        [0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7],
        [0.8, 0.9, 1.0]
    ],
    "n": 1
}

# Post request to nonstationary_AD_cosmo endpoint
response = requests.post(BASE + "nonstationary_AD_cosmo", json=nonstationary_data)
if response.ok:
    print("Nonstationary AD Cosmo test successful:", response.json())
else:
    print("Nonstationary AD Cosmo test failed:", response.status_code, response.text)

#
# Test data for deviation detection
# deviation_test_data = {
#     "data": [
#         [0.2, 0.3, 0.4],
#         [0.5, 0.6, 0.7],
#         [0.8, 0.9, 1.0]
#     ],
#     "mu": 0.5,  # Mean of the data
#     "sigma": 0.1,  # Standard deviation of the data
#     "l1": 4,
#     "l2": 8,
#     "l3": 12
# }
#
# # Send a POST request to the deviation detection endpoint
# response = requests.post(BASE + "deviation_detection", json=deviation_test_data)
# if response.ok:
#     print("Deviation Detection Test Successful:", response.json())
# else:
#     print("Deviation Detection Test Failed:", response.status_code, response.text)