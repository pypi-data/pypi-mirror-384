from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jancodegen",
    version="1.0.2",
    author="Tran Trung Kien",
    author_email="kientt13.7@gmail.com",
    description="A Python package for generating random JAN codes and related product identification codes with valid check digits",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kientt137/jancodegen",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)