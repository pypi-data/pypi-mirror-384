from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="paystation-python-sdk",
    version="0.1.1",
    author="Hossain Azad",
    author_email="me-azad@proton.me",
    description="A Python SDK for the PayStation Bangladesh payment gateway.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/h-azad/paystation-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "requests",
    ],
)
