from setuptools import setup
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('wizata_dsapi/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

core_dependencies = [
    'pandas==1.5.3; python_version<"3.11"',
    'pandas==2.2.3; python_version>="3.11" and python_version<"3.12"',
    'pandas>=2.3.3; python_version>="3.12"',
    'numpy==1.26.4; python_version<"3.12"',
    'numpy>=2.3.3; python_version>="3.12"',
    'dill==0.3.6; python_version<"3.12"',
    'dill==0.4.0; python_version>="3.12"',
    'protobuf==3.20.3; python_version<"3.11"',
    'protobuf==5.29.5; python_version>="3.11" and python_version<"3.12"',
    'protobuf>=5.29.5; python_version>="3.12"',
    'msal==1.30.0; python_version<"3.12"',
    'msal>=1.34.0; python_version>="3.12"',
    'joblib==1.5.2; python_version<"3.12"',
    'joblib>=1.2.0; python_version>="3.12"',
    'requests==2.28.2; python_version<"3.11"',
    'requests>=2.32.5; python_version>="3.11"',
    'setuptools==67.6.0; python_version<"3.11"',
    'setuptools>=80.9.0; python_version>="3.11"',
    'plotly==5.13.1; python_version<"3.12"',
    'plotly>=6.3.1; python_version>="3.12"'
]

ml_dependencies = [
    'matplotlib==3.7.1; python_version<"3.11"',
    'matplotlib>=3.10.6; python_version>="3.11"',
    'tensorflow>=2.15.0; (sys_platform != "darwin" or platform_machine != "arm64") and python_version<"3.12"',
    'tensorflow-macos>=2.15.0; sys_platform == "darwin" and platform_machine == "arm64" and python_version<"3.12"',
    'tensorflow>=2.20.0; python_version>="3.12"',
    'keras==2.15.0; python_version<"3.12"',
    'keras>=3.11.3; python_version>="3.12"',
    'tensorflow_probability==0.15.0; python_version<"3.12"',
    'tensorflow_probability>=0.25.0; python_version>="3.12"',
    'scikit-learn==1.2.2; python_version<"3.12"',
    'scikit-learn>=1.7.2; python_version>="3.12"',
    'adtk==0.6.2',
    'scipy==1.10.1; python_version<"3.12"',
    'scipy>=1.16.2; python_version>="3.12"',
    'xgboost==1.7.4; python_version<"3.12"',
    'xgboost>=3.0.5; python_version>="3.12"',
    'u8darts==0.25.0; python_version<"3.12"',
    'u8darts>=0.38.0; python_version>="3.12"',
    'optuna==3.3.0; python_version<"3.12"',
    'optuna>=4.5.0; python_version>="3.12"',
    'explainerdashboard==0.4.2.1; python_version<"3.12"',
    'ipywidgets==8.0.4; python_version<"3.12"',
    'ipywidgets>=8.1.7; python_version>="3.12"',
    'kaleido==0.2.1; python_version<"3.12"',
    'kaleido>=1.1.0; python_version>="3.12"',
    'pytest==7.2.2; python_version<"3.12"',
    'pytest>=8.4.2; python_version>="3.12"',
    'pytest-cov==4.0.0; python_version<"3.12"',
    'pytest-cov>=7.0.0; python_version>="3.12"',
    'shapely==2.0.1; python_version<"3.12"',
    'shapely>=2.1.2; python_version>="3.12"',
    'pyodbc==4.0.35; python_version<"3.12"',
    'pyodbc>=5.2.0; python_version>="3.12"',
    'torch==2.7.1; python_version>="3.11" and python_version<"3.12"',
    'torch>=2.8.0; python_version>="3.12"'
]
all_dependencies = core_dependencies + ml_dependencies

setup(
    name='wizata_dsapi',
    version=main_ns['__version__'],
    description='Wizata Data Science Toolkit',
    author='Wizata S.A.',
    author_email='info@wizata.com',
    packages=['wizata_dsapi',
              'wizata_dsapi.plots',
              'wizata_dsapi.scripts',
              'wizata_dsapi.models'],
    install_requires=core_dependencies,
    extras_require={
        'all': all_dependencies
    },
)
