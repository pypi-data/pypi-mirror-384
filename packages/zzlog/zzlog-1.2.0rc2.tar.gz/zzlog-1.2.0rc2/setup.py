from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="zzlog",
    version="1.2.0rc2",
    description="Logging setup made izzy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pierre-rouanet/zzlog",
    author="Pierre Rouanet",
    author_email="pierre.rouanet@gmail.com",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.5",
    install_requires=[
        "python-json-logger",
    ],
)
