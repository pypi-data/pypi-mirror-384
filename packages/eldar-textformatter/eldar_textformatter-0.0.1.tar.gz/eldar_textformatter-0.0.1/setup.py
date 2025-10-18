from setuptools import setup, find_packages

setup(
    name="eldar-textformatter",  # unikal olmalıdır, PyPI-də başqası istifadə etməyib
    version="0.0.1",
    packages=find_packages(),
    install_requires=[],
    author="Eldar",
    author_email="eldar@example.com",
    description="A simple Python library for formatting text",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/eldar/textformatter",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
