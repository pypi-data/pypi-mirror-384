#flask blueprint
# ref : https://flask.palletsprojects.com/en/2.3.x/blueprints/
from flask import Blueprint, request, jsonify
import pandas as pd
from IntelliMaint.anomaly_detection import AnomalyDetection

# Define the blueprint with a URL prefix
anomaly_blueprint = Blueprint('anomaly_detection', __name__)

# Initialize the AnomalyDetection model
ad_model = AnomalyDetection()


@anomaly_blueprint.route('/deviation_detection', methods=['POST'])
def deviation_detection_api():
    # Parse JSON data from the request
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400

    mu = data.get('mu')
    sigma = data.get('sigma')
    l1 = data.get('l1', 4)
    l2 = data.get('l2', 8)
    l3 = data.get('l3', 12)

    if mu is None or sigma is None:
        return jsonify({"error": "Mean (mu) and standard deviation (sigma) are required"}), 400

    df = pd.DataFrame(data['data'])
    z_scores, sigma_used = ad_model.deviation_detection(df, mu, sigma, l1, l2, l3)
    return jsonify({
        "z_scores": z_scores.tolist(),
        "sigma": sigma_used
    }), 200

@anomaly_blueprint.route('/train_cosmo', methods=['POST'])
def train_anomaly_detection():
    data = request.get_json()  # Get JSON from request
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400

    # Extract data and optional threshold from the request
    df = pd.DataFrame(data['data'])
    threshold = data.get('threshold', 0.6)

    # Train the model
    ad_model.train_cosmo(df, threshold)
    return jsonify({"message": "Model trained successfully."}), 200

@anomaly_blueprint.route('/test_cosmo', methods=['POST'])
def test_anomaly_detection():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400

    df = pd.DataFrame(data['data'])
    strangeness, p_values = ad_model.test_cosmo(df)
    return jsonify({
        "strangeness": strangeness.tolist(),
        "p_values": p_values.tolist()
    }), 200

@anomaly_blueprint.route('/test_streaming', methods=['POST'])
def test_anomaly_detection_streaming():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400

    df = pd.DataFrame(data['data'])
    strangeness, p_values, deviation = ad_model.test_cosmo_streaming(df)
    return jsonify({
        "strangeness": strangeness.tolist(),
        "p_values": p_values.tolist(),
        "deviation": deviation.tolist()
    }), 200


@anomaly_blueprint.route('/nonstationary_AD_cosmo', methods=['POST'])
def nonstationary_AD_cosmo_api():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400

    n = data.get('n', 1)
    df = pd.DataFrame(data['data'])
    strangeness, deviation, pvalue = ad_model.nonstationary_AD_cosmo(df, n)
    return jsonify({
        "strangeness": strangeness,
        "deviation": deviation,
        "pvalue": pvalue
    }), 200
