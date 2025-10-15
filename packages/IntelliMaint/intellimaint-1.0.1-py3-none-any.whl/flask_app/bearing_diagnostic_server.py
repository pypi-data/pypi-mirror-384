import glob
import os

from flask import request, jsonify, Flask
import pandas as pd
import numpy as np
from IntelliMaint.anomaly_detection import AnomalyDetection
from IntelliMaint.data_analysis import SOM
from IntelliMaint.rul_models import GPRDegradationModel
from examples.bearing_diagnostics import Bearing
import traceback
import pickle as pkl
from scipy.signal import savgol_filter

app = Flask(__name__)


@app.route('/process', methods=['POST'])
def process():
    config = request.json
    # bearing = Bearing(config)
    #this did not work because Bearing expects parameters like Bd , Pd directly. passing the config didnt work because of this i think


    try:
        print("path:", config['data']['files_path'])
        files = glob.glob(os.path.join(config['data']['files_path'], '*'))
        print("Files:",  files)
        Bd = config['bearing_parameters']['Bd']
        Pd = config['bearing_parameters']['Pd']
        Nb = config['bearing_parameters']['Nb']
        a = config['bearing_parameters']['a']
        s = config['bearing_parameters']['s']
        sampRate = config['data']['sampling_rate']

        # Instantiate Bearing with the correct parameters
        bearing = Bearing(files, Bd, Pd, Nb, a, s, sampRate)
        # Analyzing raw data (You can remove this if not needed)
        bearing.analyze_raw_data(config['ber'])

        # Extracting features
        features_df = bearing.extract_features(config['ber'], config['n_cols'], bearing.files)

        # Constructing Health Indicator with SOM
        normal_data_pts_som = config["anomaly_detection"]["normal_data_pts_som"]
        da = SOM()
        som, scaler_ = da.train(features_df[:normal_data_pts_som])
        mqe = da.predict(som, features_df, scaler_).reshape(-1, 1)

        # Training Anomaly detection with normal health indicator
        normal_data_pts_cosmo = config["anomaly_detection"]["normal_data_pts_cosmo"]
        hi_train = pd.DataFrame(mqe[normal_data_pts_som:normal_data_pts_som + normal_data_pts_cosmo])
        ad = AnomalyDetection()
        ad.train_cosmo(hi_train)

        # Perform anomaly detection
        incipient_fault_threshold = config["anomaly_detection"]["incipient_fault_threshold"]
        deg_start_idx, score_till_incipient, initial_deg_pts = bearing.detect_anomaly(
            incipient_fault_threshold, normal_data_pts_som, bearing.files, config['ber'],
            config['n_cols'], som, scaler_, da, ad)

        # Prepare Data for Diagnostics
        df = bearing.prepare_data1(features_df, deg_start_idx, normal_data_pts_som,
                                   config["diagnostics"]["failure_mode"])
        df_features, labels = bearing.prepare_data2(df, deg_start_idx, normal_data_pts_som,
                                                    config["diagnostics"]["failure_mode"])

        # Evaluate Features for Diagnostics
        diagnostic_features = bearing.evaluate_diagnostic_features(df_features, labels)

        # Perform fault classification
        with open(config['model_paths']['rf_classifier'], 'rb') as file:
            clf = pkl.load(file)

        with open(config['model_paths']['label_encoder'], 'rb') as file:
            label_encoder = pkl.load(file)

        predictions = []
        for i in range(deg_start_idx, len(bearing.files)):
            df_ = bearing.extract_features(config['ber'], config['n_cols'], [bearing.files[i]], log_msg=False)
            pred_y = clf.predict(df_)
            predicted_label = label_encoder.inverse_transform(pred_y)
            predictions.append(predicted_label[0])

        # Prognostics Assessment
        min_continuous_deg_pts = config["prognostics"]["min_continuous_deg_pts"]
        hi_raw = np.array(initial_deg_pts).reshape(len(initial_deg_pts), 1)
        initial_deg_pts_filtered = savgol_filter(hi_raw.reshape(-1), 2, 1)
        failure_threshold = config["prognostics"]["failure_threshold"]
        rul_model = GPRDegradationModel(initial_deg_pts_filtered.reshape(-1, 1), failure_threshold, order=2)
        rul_estimates = []
        for i in range(deg_start_idx + min_continuous_deg_pts, len(bearing.files)):
            df_ = bearing.extract_features(config['ber'], config['n_cols'], [bearing.files[i]], log_msg=False)
            features_array = df_.to_numpy()
            mqe = da.predict(som, features_array, scaler_).reshape(-1, 1)
            error = pd.DataFrame(mqe)
            health_score, p, deviation = ad.test_cosmo_streaming(error)
            hi_raw = np.concatenate((hi_raw, health_score.reshape(-1, 1)), axis=0)
            if hi_raw.shape[0] < 51:
                win_len = 11
            else:
                win_len = 51
            hi_filtered = savgol_filter(hi_raw.reshape(hi_raw.shape[1], hi_raw.shape[0]), win_len, 1)
            hi_filtered = hi_filtered.reshape(hi_raw.shape[0], hi_raw.shape[1])
            X = np.array([k for k in range(min_continuous_deg_pts + i,
                                           min_continuous_deg_pts + i + config["prognostics"][
                                               "prediction_horizon"])]).reshape(
                config["prognostics"]["prediction_horizon"], 1)
            Yp, Vp, rul = rul_model.predict(X)
            if rul is not None:
                rul_estimates.append(rul)
            # Update the model only if the index is within bounds
            if i < len(initial_deg_pts_filtered):
                rul_model.update(np.array([i]).reshape(1, 1), initial_deg_pts_filtered[i].reshape(1, 1))

        result = {
            "diagnostic_features": diagnostic_features,
            "predicted_fault": predictions,
            "rul_estimates": rul_estimates
        }
        return jsonify(result)

    except Exception as e:
        print("Exception occurred: ", e)
        print(traceback.format_exc())
        return str(e), 500


if __name__ == "__main__":
    app.run(debug=True)

