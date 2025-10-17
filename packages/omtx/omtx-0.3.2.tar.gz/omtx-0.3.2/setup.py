"""Setup configuration for OMTX Python SDK"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="omtx",
    version="0.3.2",
    author="Om",
    author_email="hello@omtx.ai",
    description="Simple Python client for the Om API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/omtx/python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/omtx/python-sdk/issues",
        "Source": "https://github.com/omtx/python-sdk",
        "Documentation": "https://docs.omtx.ai/sdk/python",
    },
)
