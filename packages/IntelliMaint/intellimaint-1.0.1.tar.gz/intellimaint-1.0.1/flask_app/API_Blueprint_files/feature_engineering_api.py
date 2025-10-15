from flask import Blueprint, request, jsonify
import pandas as pd
from IntelliMaint.feature_engineering import TimeDomain, FrequencyDomain


# Create a blueprint for feature engineering
feature_blueprint = Blueprint('feature_engineering', __name__)


@feature_blueprint.route('/extract_features', methods=['POST'])
def extract_features():
    data = request.get_json()

    if not data or 'data' not in data:
        return jsonify({"error": "Data is required"}), 400

    try:
        df = pd.DataFrame(data['data'])

        # Add each feature calculation one at a time to isolate the problem
        rms = TimeDomain.get_rms(df.to_numpy())
        mean = TimeDomain.get_mean(df.to_numpy())
        var = TimeDomain.get_variance(df.to_numpy())
        crest = TimeDomain.get_crestfactor(df.to_numpy())
        kurt = TimeDomain.get_kurtosis(df.to_numpy())
        skew = TimeDomain.get_skewness(df.to_numpy())

        return jsonify({
            "rms": rms.tolist(),
            "mean": mean.tolist(),
            "variance": var.tolist(),
            "crest_factor": crest.tolist(),
            "kurtosis": kurt.tolist(),
            "skewness": skew.tolist()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@feature_blueprint.route('/frequency_domain_features', methods=['POST'])
def frequency_features():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Convert data to DataFrame and then to numpy array
        df = pd.DataFrame(data['data'])
        array_data = df.to_numpy()

        # Create an instance of FrequencyDomain
        frequency_domain = FrequencyDomain(array_data)

        # Calculate cepstrum coefficients
        ceps_coeffs = frequency_domain.get_cepstrumcoeffs(array_data)

        return jsonify({
            "cepstrum_coefficients": ceps_coeffs.tolist()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# @feature_blueprint.route('/bearing_frequency_features', methods=['POST'])
# def specific_frequency_features():
#     data = request.get_json()
#     if not data or 'data' not in data:
#         return jsonify({"error": "No data provided"}), 400
#
#     try:
#         df = pd.DataFrame(data['data'])
#         array_data = df.to_numpy()
#
#         # Assuming FrequencyDomain can calculate specific frequency features
#         frequency_domain = FrequencyDomain(array_data)
#         ftf, bpfi, bpfo, bsf = frequency_domain.calculate_bearing_features(array_data)  # Implement this method
#
#         return jsonify({
#             "ftf": ftf,
#             "bpfi": bpfi,
#             "bpfo": bpfo,
#             "bsf": bsf
#         }), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
