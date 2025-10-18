# setup.py
from setuptools import setup, find_packages

setup(
    name="hqapi_client",  # must match your Python package folder
    version="1.0.0",
    description="Python client for the HQAPI.com",
    author="HQAPI",
    packages=find_packages(),  # automatically find packages
    install_requires=[
        "requests>=2.30.0",  # your dependencies
    ],
    python_requires=">=3.8",
)