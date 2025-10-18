from setuptools import setup, find_packages

setup(
name="eldar-textformatter-matrix",
version="0.1.0",
author="Eldar Eliyev",
author_email="eldar@example.com",
description="A simple Python library for text formatting and cleaning.",
long_description=open("README.md", encoding="utf-8").read(),
long_description_content_type="text/markdown",
url="https://github.com/eldar/textformatter",
packages=find_packages(),
classifiers=[
"Programming Language :: Python :: 3",
"Operating System :: OS Independent",
],
python_requires=">=3.7",
)
