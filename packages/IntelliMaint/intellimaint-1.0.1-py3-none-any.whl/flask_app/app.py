# Main Flask application
from flask import Flask

from flask_app.API_Blueprint_files.data_acquisition_api import data_acquisition_blueprint
from flask_app.API_Blueprint_files.rul_api import rul_blueprint
from flask_app.API_Blueprint_files.anomaly_detection_api import anomaly_blueprint
from flask_app.API_Blueprint_files.feature_engineering_api import feature_blueprint
from flask_app.API_Blueprint_files.data_analysis_api import data_analysis_blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(anomaly_blueprint, url_prefix='/api/v1/anomaly_detection')
    app.register_blueprint(feature_blueprint, url_prefix='/api/v1/feature_engineering')
    app.register_blueprint(data_analysis_blueprint, url_prefix='/api/v1/data_analysis')
    app.register_blueprint(rul_blueprint, url_prefix='/api/v1/rul_models')
    app.register_blueprint(data_acquisition_blueprint, url_prefix='/api/v1/data_acquisition')
    return app

app = create_app()

@app.route('/')
def home():
    return "Welcome to the IntelliMaint API!"

if __name__ == "__main__":
    app.run(debug=True)
