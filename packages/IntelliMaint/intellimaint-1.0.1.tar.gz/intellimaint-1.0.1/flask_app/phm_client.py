import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import json
import threading

class PHMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PHM")

        self.config = {
          "data": {
            # "files_path": "../examples/data/2nd_test/2nd_test",
            "files_path": "./test/data",
            "sampling_rate": 20480
          },
          "bearing_parameters": {
            "Bd": 0.331,
            "Pd": 2.815,
            "Nb": 16,
            "a": 0.265,
            "s": 33.33
          },
          "signal_processing": {
            "techniques": [
              {
                "name": "low_pass_filter",
                "params": {
                  "cutoff_freq": 100,
                  "order": 5
                }
              },
              {
                "name": "envelope_analysis",
                "params": {
                  "bearing_frequencies": [3.5848, 5.4152, 0.3983, 4.7135]
                }
              }
            ]
          },
          "anomaly_detection": {
            "normal_data_pts_som": 200,
            "normal_data_pts_cosmo": 200,
            "incipient_fault_threshold": 0.6
          },
          "diagnostics": {
            "failure_mode": "outer_race",
            "top_n": 5
          },
          "prognostics": {
            "min_continuous_deg_pts": 10,
            "failure_threshold": 6.3,
            "prediction_horizon": 300
          },
          "model_paths": {
            "rf_classifier": "../examples/models/rf_classifier_.pkl",
            "label_encoder": "../examples/models/label_encoder_.pkl"
          }
        }

        self.processed_signals = {} #save for feature extraction
        self.feature_data = {} #save for anomoly detection

        self.create_widgets()

    def create_widgets(self):
        self.data_acq_button = tk.Button(self.root, text="Acquire Data", command=self.data_acquisition)
        self.data_acq_button.pack(pady=10)

        self.signal_proc_button = tk.Button(self.root, text="Process Signal", command=self.process_all_signals)
        self.signal_proc_button.pack(pady=10)

        self.time_domain_features_button = tk.Button(self.root, text="Extract Features", command=self.extract_features)
        self.time_domain_features_button.pack(pady=10)

        # self.anomaly_detection_button = tk.Button(self.root, text="Detect Anomalies", command=self.anomaly_detection)
        # self.anomaly_detection_button.pack(pady=10)

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack(pady=20)

    def data_acquisition(self):
        threading.Thread(target=self._data_acquisition).start()

    def _data_acquisition(self):
        try:
            # Prepare the correct JSON structure for the server
            data_dir_path = {'data_dir_path': self.config['data']['files_path']}
            response = requests.post('http://127.0.0.1:5000/api/v1/data_acquisition/get_data_from_dir',
                                     json=data_dir_path)
            response.raise_for_status()
            result = response.json()
            self.root.after(0, self.update_result, f"Data Loaded: {result}")
        except requests.exceptions.RequestException as e:
            self.root.after(0, messagebox.showerror, "Error", f"Request failed: {e}")

    def process_all_signals(self):
        for technique in self.config['signal_processing']['techniques']:
            self.signal_processing(technique['name'])

    def signal_processing(self, technique_name):
        threading.Thread(target=self._signal_processing, args=(technique_name,)).start()

    def _signal_processing(self, technique_name):
        technique = next((tech for tech in self.config['signal_processing']['techniques'] if tech['name'] == technique_name), None)
        if not technique:
            self.root.after(0, messagebox.showerror, "Error", "Technique configuration not found.")
            return

        # random signal values because signal is not in input data but the package uses it
        signal_data = [0.0, 1.0, 0.5, 2.0]

        signal_processing_payload = {
            'sampling_rate': self.config['data']['sampling_rate'],
            'signal': signal_data,
            'process_type': technique['name'],
            **technique['params']
        }

        try:
            response = requests.post('http://127.0.0.1:5000/api/v1/signal_processing/process_signal', json=signal_processing_payload)
            response.raise_for_status()
            result = response.json()

            # Save the processed signal for future use
            self.processed_signals[technique_name] = result
            self.root.after(0, self.update_result, f"Signal Processed for {technique_name}: {result}")
        except requests.exceptions.RequestException as e:
            self.root.after(0, messagebox.showerror, "Error", f"Request failed: {e}")

    def extract_features(self):
        if not self.processed_signals:
            messagebox.showinfo("Info", "No processed signals available for feature extraction.")
            return
        threading.Thread(target=self._extract_features).start()

    def _extract_features(self):
        for technique_name, processed_data in self.processed_signals.items():
            try:
                response = requests.post('http://127.0.0.1:5000/api/v1/feature_engineering/extract_features',
                                         json={"data": processed_data})
                response.raise_for_status()
                features = response.json()

                # Save the features for each technique for potential use in anomaly detection
                self.feature_data[technique_name] = features
                self.root.after(0, self.update_result, f"Features Extracted: {features}")
            except requests.exceptions.RequestException as e:
                self.root.after(0, messagebox.showerror, "Error", f"Feature extraction failed: {e}")

    def update_result(self, result):
        self.result_label.config(text=result)

if __name__ == "__main__":
    root = tk.Tk()
    app = PHMApp(root)
    root.mainloop()