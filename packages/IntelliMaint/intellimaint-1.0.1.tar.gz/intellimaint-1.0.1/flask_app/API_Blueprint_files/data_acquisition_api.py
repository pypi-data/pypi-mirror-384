from flask import Blueprint, request, jsonify
from IntelliMaint.data_acquistion import DataAcquisition

# Create a blueprint for data acquisition
data_acquisition_blueprint = Blueprint('data_acquisition', __name__)


@data_acquisition_blueprint.route('/get_data_from_dir', methods=['POST'])
def get_data_from_dir():
    """
    Fetches data from a specified directory.
    Requires a JSON input with the key 'data_dir_path'.
    """
    data = request.get_json()
    if not data or 'data_dir_path' not in data:
        return jsonify({"error": "Data directory path is required"}), 400

    try:
        DATA_DIR_PATH = data['data_dir_path']
        df = DataAcquisition.get_data_from_dir(DATA_DIR_PATH)
        data_shape = df.shape
        return jsonify(
            {"status":"Data Acquired", "shape": {"rows": data_shape[0], "columns": data_shape[1]}}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@data_acquisition_blueprint.route('/get_data_from_file', methods=['POST'])
def get_data_from_file():
    """
    Fetches data from a specified file.
    Requires a JSON input with the key 'data_file_path'.
    """
    data = request.get_json()
    if not data or 'data_file_path' not in data:
        return jsonify({"error": "Data file path is required"}), 400

    try:
        DATA_FILE_PATH = data['data_file_path']
        df = DataAcquisition.get_data_from_file(DATA_FILE_PATH)
        data_shape = df.shape
        return jsonify(
            {"status": "Data Acquired",
             "shape": {"rows": data_shape[0], "columns": data_shape[1]}}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
