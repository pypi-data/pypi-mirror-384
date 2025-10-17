"""
Setup script for flet-stack.
For modern installation, use pyproject.toml.
This file provides backward compatibility.
"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="flet-stack",
    version="0.2.0",
    description="Decorator-based routing with view stacking for Flet applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fasil",
    author_email="fasilwdr@hotmail.com",
    url="https://github.com/fasilwdr/flet-stack",
    license="MIT",
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "flet>=0.70.0.dev6281",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
    ],
    keywords="flet routing router navigation ui view-stack",
    project_urls={
        "Bug Reports": "https://github.com/fasilwdr/flet-stack/issues",
        "Source": "https://github.com/fasilwdr/flet-stack",
    },
)