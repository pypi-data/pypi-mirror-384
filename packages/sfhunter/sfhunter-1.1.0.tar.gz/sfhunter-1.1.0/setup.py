#!/usr/bin/env python3
"""
Simple setup script for SFHunter
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="sfhunter",
    version="1.1.0",
    description="High-performance Salesforce URL scanner with advanced exploitation capabilities and Discord/Telegram integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="SFHunter",
    author_email="sfhunter@example.com",
    url="https://github.com/yourusername/sfhunter",
    packages=["sfhunter"],
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=1.26.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "sfhunter=sfhunter.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)