#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

install_requirements = open("requirements.txt").readlines()

setup(
    author="Thoughtful",
    author_email="support@thoughtful.ai",
    python_requires=">=3.9",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    description="Cookiecutter template for Thoughtful pip package",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords="t_page_object",
    name="t_page_object",
    packages=find_packages(include=["t_page_object", "t_page_object.*"]),
    test_suite="tests",
    url="https://www.thoughtful.ai/",
    version="1.1.5",
    zip_safe=False,
    install_requires=install_requirements,
)
