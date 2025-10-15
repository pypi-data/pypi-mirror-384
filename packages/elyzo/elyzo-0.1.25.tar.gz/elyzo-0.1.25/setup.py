# file: setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    # === Essential Package Information ===
    name='elyzo',
    version='0.1.25',
    packages=find_packages(),

    # === Metadata for PyPI ===
    author='Adrian Muniz',
    author_email='adrian@elyzo.ai',
    description='A client library for making secure requests within the Elyzo runtime.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/adrianmm12/elyzo-core/elyzo-py',
    license='MIT',

    # === Dependencies ===
    install_requires=[
        'requests'
    ],
    python_requires='>=3.7',

    # === Classifiers for categorizing the package ===
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)