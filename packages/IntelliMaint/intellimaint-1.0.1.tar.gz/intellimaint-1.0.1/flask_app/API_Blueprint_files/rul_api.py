from IntelliMaint.rul_models import GPRDegradationModel
import numpy as np
from flask import Blueprint, request, jsonify

rul_blueprint = Blueprint('rul_models', __name__)

# Create a dictionary to store models (simulate a database for demo purposes)
gpr_models = {}


@rul_blueprint.route('/create', methods=['POST'])
def create_model():
    data = request.get_json()
    if not data or 'HI' not in data or 'failure_threshold' not in data:
        return jsonify({"error": "Health Indicator and failure threshold are required"}), 400

    HI = np.array(data['HI']).reshape(-1, 1)
    failure_threshold = data['failure_threshold']
    order = data.get('order', 1)  # default order is 1

    # Create a model ID
    model_id = len(gpr_models) + 1
    gpr_models[model_id] = GPRDegradationModel(HI, failure_threshold, order)

    return jsonify({"message": "Model created successfully", "model_id": model_id}), 201

@rul_blueprint.route('/predict/<int:model_id>', methods=['POST'])
def predict(model_id):
    data = request.get_json()
    if not data or 'X' not in data:
        return jsonify({"error": "Time steps are required for prediction"}), 400

    if model_id not in gpr_models:
        return jsonify({"error": "Model not found"}), 404

    X = np.array(data['X']).reshape(-1, 1)
    model = gpr_models[model_id]
    Yp, Vp, rul = model.predict(X)

    # Ensure all numpy types are converted to Python native types for JSON serialization
    Yp = Yp.tolist()
    Vp = [float(v) for v in Vp]  # converting each element in variance to float
    rul = int(rul) if rul is not None else 'Not applicable'  # converting rul to int, or setting as a string if not applicable

    return jsonify({
        "predicted_HI": Yp,
        "variance": Vp,
        "estimated_RUL": rul
    }), 200

@rul_blueprint.route('/update/<int:model_id>', methods=['POST'])
def update(model_id):
    data = request.get_json()
    if not data or 'X' not in data or 'Y' not in data:
        return jsonify({"error": "Time steps and health indicator values are required"}), 400

    if model_id not in gpr_models:
        return jsonify({"error": "Model not found"}), 404

    X = np.array(data['X']).reshape(-1, 1)
    Y = np.array(data['Y']).reshape(-1, 1)
    model = gpr_models[model_id]
    model.update(X, Y)

    return jsonify({"message": "Model updated successfully"}), 200
