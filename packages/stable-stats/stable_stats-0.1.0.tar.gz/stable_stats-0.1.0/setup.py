"""
Setup script for the Stable package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "A Python package for beautifying statistical outputs into clean tables."

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="stable-stats",
    version="0.1.0",
    author="Christopher Ren",
    author_email="chris.ren@emory.edu",
    description="A Python package for beautifying statistical outputs into clean tables",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Chris-R030307/StaTable",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=3.0",
            "sphinx-rtd-theme>=0.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "stable=stable.cli:main",
        ],
    },
    keywords="statistics, scipy, statsmodels, tables, formatting, data analysis",
    project_urls={
        "Bug Reports": "https://github.com/Chris-R030307/StaTable/issues",
        "Source": "https://github.com/Chris-R030307/StaTable",
        "Documentation": "https://stable.readthedocs.io/",
    },
)
