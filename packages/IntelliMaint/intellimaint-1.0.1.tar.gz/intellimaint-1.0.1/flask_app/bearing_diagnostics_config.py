import os
import glob
import math
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, savgol_filter, hilbert
from scipy.stats import kurtosis
from scipy.fftpack import fft
from scipy.fft import fft, fftfreq
from scipy.signal import cwt, find_peaks_cwt, ricker
from IntelliMaint.feature_engineering import TimeDomain
from IntelliMaint.anomaly_detection import AnomalyDetection
from IntelliMaint.data_analysis import SOM
from IntelliMaint.rul_models import GPRDegradationModel
import pickle as pkl
from imblearn.over_sampling import SMOTE
import statistics


class Bearing:
    def __init__(self, config):
        self.files = glob.glob(os.path.join(config['data']['files_path'], '*'))
        self.Bd = config["bearing_parameters"]["Bd"]
        self.Pd = config["bearing_parameters"]["Pd"]
        self.Nb = config["bearing_parameters"]["Nb"]
        self.a = config["bearing_parameters"]["a"] * math.pi / 180
        self.s = config["bearing_parameters"]["s"] / 60
        self.sampRate = config["data"]["sampling_rate"]
        self.ratio = self.Bd / self.Pd * math.cos(self.a)
        self.ftf = self.s / 2 * (1 - self.ratio)
        self.bpfi = self.Nb / 2 * self.s * (1 + self.ratio)
        self.bpfo = self.Nb / 2 * self.s * (1 - self.ratio)
        self.bsf = self.Pd / self.Bd * self.s / 2 * (1 - self.ratio**2)
        self.bearFreq = [self.ftf, self.bpfi, self.bpfo, self.bsf]

    def analyze_raw_data(self, ber):

        rawData = pd.read_csv(self.files[0], sep='\t', header=None)
        signal = rawData.iloc[:, ber].values

        # Split the signal into normal and outer_fault portions
        normal_signal = signal[:750]
        outer_fault_signal = signal[750:]

        # Plot the normal and outer race fault signals
        plt.figure(figsize=(12, 8))
        plt.subplot(2, 2, 1)
        plt.plot(normal_signal)
        plt.title('Normal Signal')
        plt.xlabel('Time')
        plt.ylabel('Acceleration')

        plt.subplot(2, 2, 2)
        plt.plot(outer_fault_signal)
        plt.title('Outer Race Fault Signal')
        plt.xlabel('Time')
        plt.ylabel('Acceleration')

        # Perform FFT on the normal and outer race fault signals
        normal_fft = np.abs(fft(normal_signal))
        outer_fault_fft = np.abs(fft(outer_fault_signal))

        freq_normal = np.fft.fftfreq(len(normal_signal), 1/self.sampRate)
        freq_outer_fault = np.fft.fftfreq(len(outer_fault_signal), 1/self.sampRate)

        # Plot the FFT of the normal signal
        plt.subplot(2, 2, 3)
        plt.plot(freq_normal[:len(freq_normal)//2], normal_fft[:len(normal_fft)//2])
        plt.title('FFT of Normal Signal')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
        plt.xlim(0, 1000)  # Adjust the frequency range as needed

        # Plot the FFT of the outer race fault signal
        plt.subplot(2, 2, 4)
        plt.plot(freq_outer_fault[:len(freq_outer_fault)//2], outer_fault_fft[:len(outer_fault_fft)//2])
        plt.title('FFT of Outer Race Fault Signal')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
        plt.xlim(0, 1000)  # Adjust the frequency range as needed

        # Add vertical lines for BPFO harmonics in the outer race fault FFT plot
        num_harmonics = 4  # Number of harmonics to plot
        for i in range(1, num_harmonics + 1):
            harmonic_freq = i * self.bpfo
            plt.axvline(x=harmonic_freq, color='r', linestyle='--', linewidth=1, label=f'{i}x BPFO' if i == 1 else '')
            plt.text(harmonic_freq, plt.ylim()[1] * 0.9, f'{i}x BPFO\n{harmonic_freq:.2f} Hz', rotation=90, va='top', ha='right', fontsize=8)

        plt.tight_layout()
        plt.show()

    def extract_time_domain_features(self, df, td, ber):
        c = np.reshape([td.get_kurtosis(df[str(ber)]), td.get_skewness(df[str(ber)])], (-1, 2))
        return c

    def extract_fft(self, df):
        SAMPLE_RATE = 20480
        DURATION = 1
        
        N = SAMPLE_RATE * DURATION
        
        yf = fft(df.to_numpy())
        xf = fftfreq(N, 1 / SAMPLE_RATE)
        
        xf, yf = xf[:int(N/2)], np.abs(yf)[:int(N/2)]
        
        xf_low, yf_low = xf.reshape(-1, 1), np.abs(yf).reshape(-1, 1)
        
        arr = np.concatenate((xf_low, yf_low), 1)
        
        arr = sorted(arr, key=lambda a_entry: a_entry[1])
        
        top_n = arr[::-1][:]
        
        return np.vstack(top_n)[:, 0]

    def freq2index(self, freq):
        step = 10000 / 10240
        return math.floor(freq / step)

    def extract_features(self, ber, n_cols, files, log_msg=True):
        td = TimeDomain()
        
        a = []
        b = []
        
        for i in range(len(files)):
            df = pd.read_csv(files[i], sep='\t', header=None, names=([str(i) for i in range(n_cols)]))
            c = self.extract_time_domain_features(df, td, ber)
            a.append(c)
            
            amps = self.extract_fft(df[str(ber)])
            features = np.array([amps[self.freq2index(self.ftf)], amps[self.freq2index(self.bpfi)], amps[self.freq2index(self.bpfo)], amps[self.freq2index(self.bsf)]]).reshape(-1, 4)
            b.append(features)
            if log_msg:
                print("Processed sample number {}/{}".format(i+1, len(files)))
        
        fea = np.array(a).reshape(-1, 2)
        stats_features = pd.DataFrame(fea, columns=['kurtosis', 'skewness'])
        fea = np.array(b).reshape(-1, 4)
        domain_features = pd.DataFrame(fea, columns=['ftf', 'bpfi', 'bpfo', 'bsf'])
        
        all_features = pd.concat([stats_features, domain_features], axis=1)
        return all_features    

    def detect_anomaly(self, incipient_fault_threshold, normal_data_pts_som, files, ber, n_cols, som, scaler_, da, ad):
        score_till_incipient = []
        initial_deg_pts = []
        iter_ = 0
        tracker = 0
        flag = False
        continuously_deg_pts = 0
        deg_start_idx = None
        min_continuous_deg_pts = 10
        window_size = 70  # Adjust the window size as needed
        
        for i in range(normal_data_pts_som+1, len(files)):
            df_ = self.extract_features(ber, n_cols, [files[i]], log_msg=False)
            mqe = da.predict(som, df_, scaler_).reshape(-1, 1)
            error = pd.DataFrame(mqe)
            health_score, p, deviation = ad.test_cosmo_streaming(error)
            
            health_score = health_score.squeeze()
            
            print("\rThe health_score is : {} p value: {} deviation : {}".format(health_score, p.squeeze(), deviation.squeeze()), end='')
            score_till_incipient.append(health_score)
            
            if (health_score >= incipient_fault_threshold):
                if (not flag):
                    deg_start_idx = i
                iter_ += 1
            
            if (iter_ > 0):
                tracker += 1
            
                if (tracker >= window_size):
                    window_iter = iter_ - (tracker - window_size)
                    window_tracker = window_size
                    
                    if (window_iter / window_tracker >= 0.8):  # Adjust the ratio as needed
                        continuously_deg_pts += 1
                        initial_deg_pts.append(health_score)
                        flag = True  # Set flag to True when ratio condition is satisfied
                    else:
                        initial_deg_pts = []
                        continuously_deg_pts = 0
                        iter_ = 0
                        tracker = 0
                        flag = False
                        deg_start_idx = None
            
            if (continuously_deg_pts >= min_continuous_deg_pts):
                break
        
                break
        
        if deg_start_idx is None:
            print("\nNo degradation detected.")
        else:
            print("\nFound Degradation Start at instance... ",format(deg_start_idx))
        
        return deg_start_idx, score_till_incipient, initial_deg_pts

    def prepare_data1(self,df, failure_idx, normal_data_pts_som, failure_mode):
        fault_modes_col = []
        for i in range(failure_idx+1):
            fault_modes_col.append('normal')
        for i in range(failure_idx+1, df.shape[0]):
            fault_modes_col.append(failure_mode)
        df['fault_modes'] = fault_modes_col
        return df

    def prepare_data2(self, df, failure_idx, normal_data_pts_som, failure_mode):
        fault_modes_col = []
        for i in range(failure_idx+1):
            fault_modes_col.append('normal')
        for i in range(failure_idx+1, df.shape[0]):
            fault_modes_col.append(failure_mode)
        df['fault_modes'] = fault_modes_col
    
        # Extract features and labels
        features = df.drop('fault_modes', axis=1)
        labels = df['fault_modes']
        return features, labels



    def evaluate_diagnostic_features(self, features_df, labels):
    # Calculate Fisher's Discriminant Ratio (FDR) for each feature
        fdr_values = {}

        for feature in features_df.columns:
            feature_data = features_df[feature]
            normal_data = feature_data[labels == 'normal']
            fault_data = feature_data[labels == 'outer_race']

        # Check if both classes are present
            if len(normal_data) > 0 and len(fault_data) > 0:
                mean_normal = np.mean(normal_data)
                mean_fault = np.mean(fault_data)
                var_normal = np.var(normal_data)
                var_fault = np.var(fault_data)

            # Check for division by zero and handle it appropriately
            if var_normal + var_fault == 0:
                fdr = 0  # Or any other appropriate value
            else:
                fdr = (mean_normal - mean_fault) ** 2 / (var_normal + var_fault)

            # Check for NaN values and handle them appropriately
            if np.isnan(fdr):
                fdr = 0  # Or any other appropriate value

            fdr_values[feature] = fdr
        else:
            # If only one class is present, set FDR to 0 or any other appropriate value
            fdr_values[feature] = 0

    # Sort features based on FDR values (higher FDR indicates better separability)
        sorted_features = sorted(fdr_values.items(), key=lambda x: x[1], reverse=True)

        return sorted_features

    

    
    def plot_diagnostic_features(self, diagnostic_features, top_n=5):
        features, fdr_values = zip(*diagnostic_features[:top_n])
        plt.figure(figsize=(8, 6))
        plt.bar(features, fdr_values)
        plt.xlabel('Features')
        plt.ylabel('Fisher\'s Discriminant Ratio (FDR)')
        plt.title('Top {} Diagnostic Features'.format(top_n))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()





def main(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)

    bearing = Bearing(config)
    ber = 0
    bearing.analyze_raw_data(ber)

    # Extract features
    n_cols = 4
    df = bearing.extract_features(ber, n_cols, bearing.files, log_msg=True)
    print(df.shape)

    # Construct Health Indicator with SOM
    normal_data_pts_som = config["anomaly_detection"]["normal_data_pts_som"]
    train_som = df[:normal_data_pts_som]
    test_som = df
    da = SOM()
    som, scaler_ = da.train(train_som)
    mqe = da.predict(som, test_som, scaler_).reshape(-1, 1)

    plt.figure(figsize=(16, 8))
    plt.plot(mqe)

    # Train Anomaly detection with normal health indicator
    normal_data_pts_cosmo = config["anomaly_detection"]["normal_data_pts_cosmo"]
    hi = mqe
    hi_train = hi[normal_data_pts_som:normal_data_pts_som + normal_data_pts_cosmo]
    hi_test = hi[normal_data_pts_som:]
    ad = AnomalyDetection()
    hi_train = pd.DataFrame(hi_train)
    ad.train_cosmo(hi_train)

    # Evaluate health score using health indicator test
    hi_test = pd.DataFrame(hi_test)
    health_score_test, _ = ad.test_cosmo(hi_test)
    health_score_test = health_score_test.squeeze()

    hi_train = pd.DataFrame(hi_train)
    health_score_train, _ = ad.test_cosmo(hi_train)
    health_score_train = health_score_train.squeeze()

    score_train = []
    score_test = []

    for i in range(hi_train.shape[0]):
        score_train.append(health_score_train[i])

    for i in range(hi_test.shape[0]):
        score_test.append(health_score_test[i])

    h_score = score_train + score_test
    h_score = np.array(h_score)
    window_length_filter = 51
    h_score_filtered = savgol_filter(h_score, window_length_filter, 1)
    plt.figure(figsize=(20, 10))
    plt.plot([i for i in range(100, h_score.shape[0])], h_score[100:h_score.shape[0]], label='hi')
    plt.plot([i for i in range(100, h_score.shape[0])], h_score_filtered[100:h_score.shape[0]], label='hi_filtered')
    plt.ylabel('health score')
    plt.xlabel('samples')
    plt.legend()
    plt.show()

    # Perform anomaly detection
    incipient_fault_threshold = config["anomaly_detection"]["incipient_fault_threshold"]
    deg_start_idx, score_till_incipient, initial_deg_pts = bearing.detect_anomaly(
        incipient_fault_threshold, normal_data_pts_som, bearing.files, ber, n_cols, som, scaler_, da, ad)

    # Prepare Data for Diagnostics
    df = bearing.prepare_data1(df, deg_start_idx, normal_data_pts_som, config["diagnostics"]["failure_mode"])
    df.to_csv('2nd_test_bearing_1_outer_race1.csv', index=False)

    df_features, labels = bearing.prepare_data2(df, deg_start_idx, normal_data_pts_som, config["diagnostics"]["failure_mode"])
    print(df_features.head(5))
    print(labels.head(5))

    # Evaluate Features for Diagnostics
    labels = df['fault_modes']
    diagnostic_features = bearing.evaluate_diagnostic_features(df_features, labels)
    print("Diagnostic Features (sorted by FDR):")
    for feature, fdr in diagnostic_features:
        print(f"{feature}: FDR = {fdr:.4f}")
    bearing.plot_diagnostic_features(diagnostic_features, top_n=5)

    # Perform fault classification
    
    
    file = open(config["model_paths"]["rf_classifier"], 'rb')
    clf = pkl.load(file)
    file = open(config["model_paths"]["label_encoder"], 'rb')
    label_encoder = pkl.load(file)

    predictions = []
    for i in range(deg_start_idx, len(bearing.files)):
        df_ = bearing.extract_features(ber, n_cols, [bearing.files[i]], log_msg=False)
        pred_y = clf.predict(df_)
        predicted_label = label_encoder.inverse_transform(pred_y)
        print(predicted_label)
        predictions.append(predicted_label[0])
    print("The bearing failed due to this fault: {}".format(statistics.mode(predictions)))

# Prognostics Assessment
    min_continuous_deg_pts = config["prognostics"]["min_continuous_deg_pts"]
    fig = plt.figure(figsize=(20, 10))
    plt.axis([0, 250, 0, 10])
    RULTrue = []
    RULPredicted = []
    rul_max = 140

    hi_raw = np.array(initial_deg_pts).reshape(len(initial_deg_pts), 1)
    window_length = 2
    polyorder = 1
    initial_deg_pts_filtered = savgol_filter(hi_raw.reshape(-1), window_length, polyorder)
    failure_threshold = config["prognostics"]["failure_threshold"]
    rul_model = GPRDegradationModel(initial_deg_pts_filtered.reshape(-1, 1), failure_threshold, order=2)
    l = 0
    offset = 100
    prediction_horizon = config["prognostics"]["prediction_horizon"]
    print("RUL Estimation in progress ... ")

    for i in range(deg_start_idx + min_continuous_deg_pts, len(bearing.files)):
        df_ = bearing.extract_features(ber, n_cols, [bearing.files[i]], log_msg=False)
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
        X = np.array([k for k in range(min_continuous_deg_pts + l, min_continuous_deg_pts + l + prediction_horizon)]).reshape(prediction_horizon, 1)
        Yp, Vp, rul = rul_model.predict(np.array([k for k in range(min_continuous_deg_pts + l, min_continuous_deg_pts + l + prediction_horizon)]).reshape(prediction_horizon, 1))
        if rul is None:
            print("RUL estimation not available at timestep {}".format(l))
        else:
            if l in [11, 40, 94]:
                RULTrue.append(rul_max - l)
                RULPredicted.append(rul)
                color = 'g' if l == 11 else 'y' if l == 40 else 'r'
                plt.plot([k for k in range(l + offset, l + prediction_horizon + offset)], Yp, color=color, label='prediction at ' + str(l + offset))
                plt.fill_between(np.array([k for k in range(l + offset, l + prediction_horizon + offset)]).reshape(len(Yp), 1).squeeze(), Yp, Yp + Vp, color=color, alpha=.5)
                plt.fill_between(np.array([k for k in range(l + offset, l + prediction_horizon + offset)]).reshape(len(Yp), 1).squeeze(), Yp, Yp - Vp, color=color, alpha=.5)
                plt.axvline(x=l + offset, c=color)
                plt.text(l + offset, 6, "RUL :" + str(round(rul / 6, 2)) + " hours")
                print("RUL at timestep {} is {} hrs".format(l, rul))

        rul_model.update(np.array([k for k in range(len(hi_raw))]).reshape(len(hi_raw), 1), hi_filtered)
        l += 1

    plt.plot(score_till_incipient[-offset:], color='b')
    plt.plot([i for i in range(offset, len(hi_raw) + offset)], hi_raw[:], color='b', label='health score')
    plt.plot([i for i in range(offset, len(hi_raw) + offset)], hi_filtered[:], color='k', label='health score filtered')
    plt.plot([failure_threshold for i in range(len(Yp) + len(hi_raw))], linestyle='dashed', color='#ff0000')
    plt.plot([incipient_fault_threshold for i in range(len(Yp) + len(hi_raw))], linestyle='dashed', color='#ffff00')
    plt.text(0, 0.55, "incipient fault threshold")
    plt.text(0, 5.05, "failure threshold")
    plt.text(215, 7.6, "confidence interval")
    plt.arrow(225, 7.5, -14, -0.5, head_width=0.5, width=0.05, ec='black')
    plt.arrow(225, 7.5, 5, -0.5, head_width=0.5, width=0.05, ec='black')
    plt.ylabel('health_score')
    plt.xlabel('samples')
    plt.legend()
    plt.show()
if __name__ == '__main__':
    import sys
    config_file = sys.argv[1]  # Pass the configuration file as a command line argument
    main(config_file)
