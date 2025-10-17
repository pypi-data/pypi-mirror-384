"""
    Library setup file
"""

import subprocess
from setuptools import setup, find_packages


try:
    subprocess.check_output(["pip", "show", "psycopg2"])
    PSYCOPG2_INSTALLED = True
except subprocess.CalledProcessError:
    PSYCOPG2_INSTALLED = False


install_requires = ["optilogic>=2.13.0", "PyJWT>=2.8.0", "httpx>=0.24.1"]

# If psycopg2 is not installed let's check if we should use the binary version instead
if not PSYCOPG2_INSTALLED:
    import os

setup(
    name="ol-datastar",
    include_package_data=True,
    version="0.0.4",
    description="Helpful utilities for working with Datastar projects",
    url="https://cosmicfrog.com",
    author="Optilogic",
    packages=find_packages(),
    license="MIT",
    install_requires=install_requires,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
