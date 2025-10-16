#setup.py
from setuptools import setup, find_packages

setup(
    name="privacify",
    version="0.1.0",
    author="Ashour Merza",
    description="A package to anonymize sensitive data in text.",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)