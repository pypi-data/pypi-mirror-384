"""
Setup script for humalab_sdk package.

This setup.py is compatible with Bazel's py_wheel rule and allows
the package to be installed via pip.
"""

from setuptools import setup, find_packages
import os

# Read version from VERSION file
version = "0.0.1"
version_file = os.path.join(os.path.dirname(__file__), "VERSION")
if os.path.exists(version_file):
    with open(version_file, "r") as f:
        version = f.read().strip()

# Read long description from README
long_description = ""
readme_file = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_file):
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="humalab",
    version=version,
    author="HumaLab Team",
    author_email="info@humalab.ai",
    description="Python SDK for HumaLab - A platform for adaptive AI validation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/humalab/humalab_sdk",
    packages=find_packages(exclude=["*_test.py", "test_*.py", "tests"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    extras_require={
        "dev": [
            line.strip()
            for line in open("requirements-dev.txt")
            if line.strip() and not line.startswith("#") and not line.startswith("-r")
        ],
    },
    entry_points={
        "console_scripts": [
            "humalab=humalab.humalab:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
