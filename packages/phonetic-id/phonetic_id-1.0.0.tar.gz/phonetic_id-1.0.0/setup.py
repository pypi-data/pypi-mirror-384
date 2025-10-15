from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='phonetic-id',
    version='1.0.0',
    description=
    "Phonetic ID is a lightweight package for generating a easy to say ID.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Maksymilian Sawicz',
    url='https://github.com/0x1618/phonetic-id',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
