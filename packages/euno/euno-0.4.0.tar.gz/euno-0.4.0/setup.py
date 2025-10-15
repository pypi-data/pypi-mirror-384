#!/usr/bin/env python3
"""
Setup script for euno-sdk
"""

from setuptools import setup, find_packages
import os


# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Euno's CLI library to programmatically interact with Euno instance"


# Read version from version.py
def get_version():
    version_path = os.path.join(os.path.dirname(__file__), "euno", "version.py")
    if os.path.exists(version_path):
        with open(version_path, "r") as f:
            exec(f.read())
        return locals()["__version__"]
    return "0.2.0"


setup(
    name="euno",
    version=get_version(),
    author="Euno Team",
    author_email="team@euno.ai",
    description="Euno's CLI library to programmatically interact with Euno instance",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/euno-ai/euno-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
            "pre-commit>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "euno=euno.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
