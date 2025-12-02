"""
Setup script for multi-robot task allocation package
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="multi-robot-task-allocation",
    version="0.1.0",
    description="Game-theoretic multi-robot task allocation in dynamic environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Andrew Kipkoech",
    author_email="andrew_kip78@tamu.edu",
    url="https://github.com/yourusername/multi-robot-task-allocation",
    packages=find_packages(exclude=["tests", "experiments", "analysis"]),
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "viz": [
            "seaborn>=0.11.0",
            "plotly>=5.0.0",
            "jupyter>=1.0.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="multi-robot robotics task-allocation game-theory",
)