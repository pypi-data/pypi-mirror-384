from flask import Blueprint, request, jsonify
import numpy as np
from IntelliMaint.signalprocessing import SignalProcessor

signal_processing_blueprint = Blueprint('signal_processing', __name__)


@signal_processing_blueprint.route('/process_signal', methods=['POST'])
def process_signal():
    data = request.get_json()
    if not data or 'signal' not in data or 'sampling_rate' not in data:
        return jsonify({"error": "Signal data and sampling rate are required"}), 400

    # Extract parameters
    signal = np.array(data['signal'])
    sampling_rate = data['sampling_rate']
    process_type = data.get('process_type')

    # Initialize the signal processor
    processor = SignalProcessor(sampling_rate=sampling_rate)

    try:
        if process_type == 'low_pass_filter':
            cutoff_freq = data.get('cutoff_freq')
            order = data.get('order', 5)
            filtered_signal = processor.low_pass_filter(signal, cutoff_freq, order)
            return jsonify({"filtered_signal": filtered_signal.tolist()}), 200

        elif process_type == 'high_pass_filter':
            cutoff_freq = data.get('cutoff_freq')
            order = data.get('order', 5)
            filtered_signal = processor.high_pass_filter(signal, cutoff_freq, order)
            return jsonify({"filtered_signal": filtered_signal.tolist()}), 200

        elif process_type == 'band_pass_filter':
            low_cutoff_freq = data.get('low_cutoff_freq')
            high_cutoff_freq = data.get('high_cutoff_freq')
            order = data.get('order', 5)
            filtered_signal = processor.band_pass_filter(signal, low_cutoff_freq, high_cutoff_freq, order)
            return jsonify({"filtered_signal": filtered_signal.tolist()}), 200

        elif process_type == 'envelope_analysis':
            bearing_frequencies = data.get('bearing_frequencies', [])
            envelope_result = processor.envelope_analysis(signal, bearing_frequencies)
            return jsonify({"envelope_result": "Analysis complete"}), 200  # Modify as necessary to return actual data

        else:
            return jsonify({"error": "Unknown processing type"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

