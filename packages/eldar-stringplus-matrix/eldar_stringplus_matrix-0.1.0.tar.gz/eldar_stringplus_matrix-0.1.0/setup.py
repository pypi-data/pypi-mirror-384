from setuptools import setup, find_packages

setup(
    name="eldar-stringplus-matrix",        # unikaldır, PyPI-də mövcud olmamalıdır
    version="0.1.0",
    author="Eldar Eliyev",
    author_email="your_email@example.com",
    description="Python string methods extended library",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/eldar/stringplus",  # GitHub linki varsa
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
