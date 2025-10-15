import pickle
from flask import Blueprint, request, jsonify
import pandas as pd
from tensorflow.keras.models import load_model

from IntelliMaint.data_analysis import AutoEncoder, SOM

data_analysis_blueprint = Blueprint('data_analysis', __name__)

@data_analysis_blueprint.route('/train_autoencoder', methods=['POST'])
def train_autoencoder():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "Data is required"}), 400

    try:
        x = pd.DataFrame(data['data'])
        L1 = data.get('L1', 100)
        L2 = data.get('L2', 100)
        e_dim = data.get('e_dim', 2)
        a_func = data.get('a_func', 'relu')
        b_size = data.get('b_size', 30)
        epochs = data.get('epochs', 100)

        ae = AutoEncoder()
        AE, model, scaler = ae.train(x, L1, L2, e_dim, a_func, b_size, epochs)

        # Save model and scaler for future use
        model.save('autoencoder_model.h5')
        pickle.dump(scaler, open('autoencoder_scaler.pkl', 'wb'))

        return jsonify({"message": "Autoencoder trained successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@data_analysis_blueprint.route('/predict_autoencoder', methods=['POST'])
def predict_autoencoder():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "Data and model paths are required"}), 400

    try:
        df = pd.DataFrame(data['data'])
        model = load_model('autoencoder_model.h5')
        scaler = pickle.load(open('autoencoder_scaler.pkl', 'rb'))

        ae = AutoEncoder()
        RE = ae.predict(model, scaler, df)

        return jsonify({"reconstruction_error": RE.tolist()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@data_analysis_blueprint.route('/train_som', methods=['POST'])
def train_som():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "Data is required"}), 400

    try:
        df = pd.DataFrame(data['data'])
        w1 = data.get('w1', 50)
        w2 = data.get('w2', 50)
        sigma = data.get('sigma', 0.1)
        lr = data.get('lr', 0.5)
        n_iter = data.get('n_iter', 500)

        som = SOM()
        trained_som, scaler = som.train(df, w1, w2, sigma, lr, n_iter)

        # Save SOM and scaler for future use
        pickle.dump(trained_som, open('som_model.pkl', 'wb'))
        pickle.dump(scaler, open('som_scaler.pkl', 'wb'))

        return jsonify({"message": "SOM trained successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@data_analysis_blueprint.route('/predict_som', methods=['POST'])
def predict_som():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "Data, SOM, and scaler paths are required"}), 400

    try:
        df = pd.DataFrame(data['data'])
        som = pickle.load(open('som_model.pkl', 'rb'))
        scaler = pickle.load(open('som_scaler.pkl', 'rb'))

        som_instance = SOM()
        q_error = som_instance.predict(som, df, scaler)

        return jsonify({"quantization_error": q_error.tolist()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500