"""NCP SDK Setup Configuration."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ncp-sdk",
    version="0.1.8",
    author="Aviz Networks",
    description="SDK for building and deploying AI agents on the NCP platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "toml>=0.10.2",
        "requests>=2.28.0",
        "websockets>=11.0",
        "urllib3>=1.26.0",
        "rich>=13.0.0",
        "pathspec>=0.11.0",
    ],
    entry_points={
        "console_scripts": [
            "ncp=ncp.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "ncp": ["templates/**/*"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
