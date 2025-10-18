#setup.py
from setuptools import setup, find_packages

#usage
#python setup.py sdist bdist_wheel
#twine upload dist/*

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="privacify",
    version="0.3.3",
    author="Ashour Merza",
    description="A package to anonymize sensitive data in text.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    long_description=long_description,
    long_description_content_type="text/markdown"
)