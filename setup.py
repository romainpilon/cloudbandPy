"""Setup script for installing cloudbandPy"""

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()


setup(
    name="cloudbandPy",
    version="1.0.0",
    author="Romain Pilon",
    author_email="romain.pilon@gmail.com",
    description="A Python package for atmospheric cloud bands detection.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    install_requires=required,
    python_requires=">=3.8",
)

if __name__ == "__main__":
    setup()