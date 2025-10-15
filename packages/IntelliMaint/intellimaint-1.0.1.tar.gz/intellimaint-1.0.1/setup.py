from setuptools import setup, find_packages


# Read the contents of your README file
with open('PYPI_DOCS.md', 'r') as f:
    long_description = f.read()

try:
    from IntelliMaint.__version__ import __version__
except ImportError:
    print("not able to find version file")
    # Fallback if _version.py isn't available (e.g., during build)
    __version__ = '1.0.0'

setup(
    name='IntelliMaint',
    version=__version__,
    author='IPTLP0032',
    author_email='iptgithub@intellipredikt.com',
    description='A prognostics package by IntelliPredikt Technologies',
    long_description_content_type='text/markdown',
    long_description=long_description,       
    install_requires=[
        'scikit-learn', 
        'GPy', 
        'minisom', 
        'scipy>=1.3.0', 
        'matplotlib', 
        "numpy>=1.7,<2.0.0",
        'mplcursors', 
        'fpdf2', 
        'tensorflow>=2.10,<2.20', 
        'keras>=2.10', 
        'pandas', 
        'seaborn', 
        'imbalanced-learn',
        'tqdm',
        'paho-mqtt',
        'statsmodels',
        'requests',
        'streamlit'
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'IntelliMaint': [
            'grand/datasets/*',
            'grand/group_anomaly/*',
            'grand/individual_anomaly/*',
            'grand/*'
        ],
        'IntelliMaint.examples.data.battery_data': ['*'],
        'IntelliMaint.examples.data.bearing_data': ['*'],
        'IntelliMaint.examples.data.phm08_data.csv': ['*']
    },
    python_requires='>=3.12',
    entry_points={
        'console_scripts': [
            'intellimaint = IntelliMaint.cli:main',
        ],
    }

)
