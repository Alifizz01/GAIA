"""
Setup script for GAIA BMS Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="gaia-bms",
    version="1.0.0",
    author="GAIA Development Team",
    author_email="gaia@example.com",
    description="GAIA: Generalized Advanced Intelligent Analytics for Battery Management Systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/GAIA",
    packages=find_packages(where="Scripts"),
    package_dir={"": "Scripts"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9,<3.13",  # PyBaMM requires Python 3.9-3.12
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "pybamm>=23.1,<26.0; python_version>='3.9' and python_version<'3.13'",
        "PyQt5>=5.15.0",
        "pyqtgraph>=0.12.0",
        "pandas>=1.3.0",
        "joblib>=1.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
        ],
        "db": [
            "sqlalchemy>=1.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gaia-simulator=gui.main_window:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

