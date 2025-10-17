"""
Setup script for the MRCE+ package.
"""

from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements file
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="mrce-plus",
    version="1.0.0",
    author="Krishna Bajpai, Vedanshi Gupta",
    author_email="krishna@krishnabajpai.me, vedanshigupta158@gmail.com",
    description="Meta-Recursive Cognitive Engine Plus - A triple-loop cognitive system with multi-tiered memory and LLM integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/krishnabajpai/mrce-plus",  # Replace with actual repository URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
)