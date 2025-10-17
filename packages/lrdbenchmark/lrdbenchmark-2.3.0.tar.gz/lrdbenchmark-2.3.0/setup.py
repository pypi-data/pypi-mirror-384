#!/usr/bin/env python3
"""
Setup script for LRDBenchmark package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get version from __init__.py
def get_version():
    with open("lrdbenchmark/__init__.py", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "2.1.8"

setup(
    name="lrdbenchmark",
    version=get_version(),
    author="Davian R. Chin",
    author_email="d.r.chin@reading.ac.uk",
    description="Comprehensive Long-Range Dependence Benchmarking Framework with Classical, ML, and Neural Network Estimators + 5 Demonstration Notebooks",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/dave2k77/LRDBenchmark",
    project_urls={
        "Bug Reports": "https://github.com/dave2k77/LRDBenchmark/issues",
        "Source": "https://github.com/dave2k77/LRDBenchmark",
        "Documentation": "https://lrdbenchmark.readthedocs.io/",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=[
        "long-range dependence",
        "hurst parameter", 
        "time series analysis",
        "benchmarking",
        "machine learning",
        "neural networks",
        "reproducible research",
        "fractional brownian motion",
        "wavelet analysis",
        "spectral analysis"
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "scikit-learn>=1.0.0",
        "pandas>=1.3.0",
        "pywavelets>=1.3.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "psutil>=5.8.0",
        "networkx>=2.6.0",
        "joblib>=1.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.12",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5",
            "myst-parser>=0.15",
        ],
        "dashboard": [
            "streamlit>=1.28.0",
            "plotly>=5.15.0",
        ],
        "accel": [
            "jax>=0.3.0",
            "jaxlib>=0.3.0",
            "numba>=0.56.0",
        ],
        "ml": [
            "torch>=1.9.0",
        ],
        "bayes": [
            "optuna>=3.0.0",
            "numpyro>=0.12.0",
        ],
        "all": [
            "jax>=0.3.0",
            "jaxlib>=0.3.0",
            "numba>=0.56.0",
            "torch>=1.9.0",
            "optuna>=3.0.0",
            "numpyro>=0.12.0",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["notebooks/*.ipynb", "notebooks/README.md"],
    },
    zip_safe=False,
)
