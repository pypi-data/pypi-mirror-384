import time

from setuptools import setup, find_packages

#
time.sleep(10000)

setup(
    name="python3.5",
    version="0.1.0",
    author="Alex Stones",
    author_email="figaro34figaro89@gmail.com",
    description="A package with useful time utilities 2 ",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    keywords="utils, system",
)
