#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    version='0.1.0',
    name='rdflib-endpoint',
    license='MIT License',
    description='A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python, using RDFLib and FastAPI.',
    author='Vincent Emonet',
    author_email='vincent.emonet@gmail.com',
    url='https://github.com/vemonet/rdflib-endpoint',
    packages=find_packages(),
    # packages=find_packages(include=['rdflib_endpoint']),
    # package_dir={'rdflib_endpoint': 'rdflib_endpoint'},

    python_requires='>=3.6.0',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=open("requirements.txt", "r").readlines(),
    tests_require=['pytest==5.2.0'],
    setup_requires=['pytest-runner'],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ]
)
