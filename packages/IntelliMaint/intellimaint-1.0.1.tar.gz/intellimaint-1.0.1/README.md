# IntelliMaint - Predictive Diagnostics and Prognostics Application Development Python Package for Engineering Systems
IntelliMaint library offers an integrated set of functions written in Python that aids in predictive health diagnostics. The library includes various state-of-the-art algorithms that are accessible by users with simple APIs. Thus the library accelerates the analysis and the development phase for even the novice users. Most of the APIs are provided with intuitive visualizations that guide in choosing the apt algorithm for a system component. Each block in the library is built as an independent module thus used as a plug and play module. The expert users are provided with a provision to add new algorithms for specific use cases.


![image](https://github.com/bkramesh64/intellimaint-0.2/assets/29832933/38402759-d569-4410-b51f-36eb8b043785)


## Features

- Data Preparation
- Signal Processing
- Feature Extraction
- Anomaly Detection
- Diagnostics
- Prognostics

## Contents

- [Installation](docs/installation.md)
- [Quick Start](docs/quickstart.md)
- [API Documentation](docs)


## Repository Structure
- `IntelliMaint/` - The python package files <br />
- `examples/` - Example Python scripts using IntelliMaint <br />
- `README.md` - The readme (this file) <br />
- `setup.py` - Contains all metadata about this package <br />
- `build.py` - Uses py builder to build the wheel and tar files for that version of the package <br />
- `.gitignore` - The gitignore file for this package to exclude uneccesary files t be pushed to the repository <br />

## Setup Upload for PyPi Distribution
- Once you have your `setup.py` file and `__init__.py` and `build.py` files with version numbers updated, you can build binary distribution and source distrubution files.
- To create the distribution files, use the command `pyb publish` <br />
- `pyb publish` creates the .tar and .wheel files for that version in a `target` folder through the command line. <br />

### ALTERNATIVELY
- Once you have your setup.py file and __init__.py you can build binary distribution and source distrubution files.
- To create the distribution files, first check if you have the wheel package - pip install wheel
- Once we have wheel installed we can use the following command to get the distribution files - python setup.py bdist_wheel and python setup.py sdist

## Building intelliamaint for PyPI. 
- Make an account on PyPi. <br />
- use `twine check target/dist/intellimaint-0.15/dist/*` twine checks if all necessary information is there  <br />
- Get the API token from your PyPi account. <br />
- use the following command to upload to PyPI distribution -  `twine upload target/dist/intellimaint-0.15/dist/* -u __token__ -p pypi- <API_TOKEN>` <br />

### ALTERNATIVELY
- Make an account on PyPi. <br />
- use `twine check dist/*` twine checks if all necessary information is there  <br />
- Get the API token from your PyPi account. <br />
- use the following command to upload to PyPI distribution -  `twine upload dist/* -u __token__ -p pypi- <API_TOKEN>` <br />
- Example i would uplaod with my API token like this  -  `twine upload dist/*  -u __token__ -p pypi-AgEIcHlwaS5vcmcCJGMzOTZkNWRhLTNkYjQtNGZlYS04NDMyLTZmNGY5MDU4MzA4MQACKlszLCI4ZDk4NDQ2Mi1jMmZhLTQ2OWItYjBmYy0xNjZjM2Y0NzkzNmUiXQAABiB6dInTXdcHg8NZCc5O2rPO1fDE6JtheC_8_y2IckkxSA`



