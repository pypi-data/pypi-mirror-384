from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hello-team",
    version="0.1.0",
    author="DeveloperAlex",
    description="A simple package that greets teams using pprint and colorama.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DeveloperAlex/pypi_HelloTeam",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
