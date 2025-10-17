#!/usr/bin/env python3
"""
Setup script for lender-datalayer package.
Minimal setup with only required fields.
"""

from setuptools import setup, find_packages

# Required fields with additional metadata
setup(
    name="ldc-lender-datalayer",
    version="1.0.2",
    author="Sandesh Kanagal",
    author_email="sandesh.kanagal@lendenclub.com",
    description="A comprehensive data access layer for ldc lender apps",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10.0",
    install_requires=[
        "Django>=5.2.0",
        "psycopg[binary,pool]>=3.2.9",
        "redis>=5.0.3",
        "pytz>=2023.3",
        "python-dateutil>=2.8.2",
        "pycryptodome>=3.19.0",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities"
    ],
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
)
