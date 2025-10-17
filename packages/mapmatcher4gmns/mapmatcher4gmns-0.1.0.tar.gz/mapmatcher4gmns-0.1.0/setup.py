# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Created Date: 10/16/2025
# Author: Yajun Liu
# Contact Info: yajunliu@asu.edu

"""
Setup script for mapmatcher4gmns package.
This file is kept for backward compatibility.
The main configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages

# Read the long description from README
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A high-performance map matching tool for GMNS networks"

setup(
    name="mapmatcher4gmns",
    version="0.1.0",
    author="Yajun Liu",
    author_email="yajunliu@asu.edu",
    description="A high-performance map matching tool for GMNS networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://pypi.org/project/mapmatcher4gmns/",  # 可选：发布后填写 PyPI 链接
    packages=find_packages(include=['mapmatcher4gmns', 'mapmatcher4gmns.*']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "shapely>=2.0.0",
        "geopandas>=0.10.0",
        "networkx>=2.6.0",
        "tqdm>=4.60.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    package_data={
        "mapmatcher4gmns": ["*.csv"],
    },
    include_package_data=True,
    keywords="map-matching GMNS",
)

