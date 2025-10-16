#!/usr/bin/env python3
"""Setup script for Articlay"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define requirements directly instead of reading from file
# This is more reliable for packaging
requirements = [
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
]

setup(
    name="articlay",
    version="1.1.5",  # Default command now shows one random article
    author="Articlay Contributors",
    description="A CLI tool to aggregate and view curated news articles from 100+ sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pappater/articlay",
    py_modules=["articlay"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "articlay=articlay:main",
        ],
    },
)
