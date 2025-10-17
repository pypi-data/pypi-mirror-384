# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="smarttext",
    version="0.1.0",
    author="Eldar Eliyev",
    author_email="eldar@example.com",
    description="An intelligent text analysis library for Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/eldar-eliyev/smarttext",
    packages=find_packages(),
    install_requires=[
        "langdetect",
        "textblob",
        "matplotlib"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
)
# -*- coding: utf-8 -*-

