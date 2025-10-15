"""Setup script for ConnectLife Cloud API client."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from pyproject.toml instead
requirements = [
    "aiohttp>=3.8.0",
    "aiofiles>=0.8.0",
]

setup(
    name="connectlife-cloud",
    version="0.2.0",
    author="ConnectLife LLC",
    author_email="support@connectlife.com",
    description="ConnectLife Cloud API client library for Home Assistant integrations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Connectlife-LLC/connectlife-cloud",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "isort>=5.0.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "connectlife-cloud=connectlife_cloud.cli:main",
        ],
    },
)
