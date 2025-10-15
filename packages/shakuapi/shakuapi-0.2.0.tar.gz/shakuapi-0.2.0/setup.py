from setuptools import setup, find_packages

setup(
    name="shakuapi",
    version="0.2.0",
    author="Shaku",
    description="A simple Python SDK for Shaku REST APIs (size measurement & clothes recognition)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["requests"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
