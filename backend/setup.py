from setuptools import setup, find_packages

setup(
    name="dft-tool-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        "PyWavelets>=1.4.0",
        "pytest>=7.0.0"
    ]
)
