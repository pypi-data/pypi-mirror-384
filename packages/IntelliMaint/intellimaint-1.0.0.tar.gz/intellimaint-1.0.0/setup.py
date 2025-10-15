#!/usr/bin/env python
#   -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.install import install as _install

class install(_install):
    def pre_install_script(self):
        pass

    def post_install_script(self):
        pass

    def run(self):
        self.pre_install_script()

        _install.run(self)

        self.post_install_script()

if __name__ == '__main__':
    setup(
        name = 'IntelliMaint',
        version = '1.0.0',
        description = 'A prognostics package by IntelliPredikt Technologies',
        long_description = 'A prognostics package by IntelliPredikt Technologies',
        long_description_content_type = None,
        classifiers = [
            'Development Status :: 3 - Alpha',
            'Programming Language :: Python'
        ],
        keywords = '',

        author = '',
        author_email = '',
        maintainer = '',
        maintainer_email = '',

        license = '',

        url = '',
        project_urls = {},

        scripts = [],
        packages = [],
        namespace_packages = [],
        py_modules = [],
        entry_points = {},
        data_files = [],
        package_data = {
            'IntelliMaint': ['grand/datasets/*', 'grand/group_anomaly/*', 'grand/individual_anomaly/*', 'grand/*'],
            'IntelliMaint.examples.data': ['phm08_data.csv'],
            'IntelliMaint.examples.data.battery_data': ['*'],
            'IntelliMaint.examples.data.bearing_data': ['*']
        },
        install_requires = [
            'GPy',
            'fpdf2',
            'imbalanced-learn',
            'keras>=2.10',
            'matplotlib',
            'minisom',
            'mplcursors',
            'numpy<2.0.0,>=1.7',
            'pandas',
            'scikit-learn',
            'scipy>=1.3.0',
            'seaborn',
            'tensorflow<2.20,>=2.10'
        ],
        dependency_links = [],
        zip_safe = True,
        cmdclass = {'install': install},
        python_requires = '',
        obsoletes = [],
    )
