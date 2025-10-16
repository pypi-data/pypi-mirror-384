#!/usr/bin/env python3
"""
Setup script for auth-service package
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from pyproject.toml
with open("pyproject.toml", "r", encoding="utf-8") as fh:
    content = fh.read()

setup(
    name="trovesuite-auth-service",
    version="1.0.1",
    author="Bright Debrah Owusu",
    author_email="owusu.debrah@deladetech.com",
    description="A comprehensive authentication and authorization service for ERP systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deladetech/trovesuite-auth-service",
    project_urls={
        "Bug Tracker": "https://github.com/deladetech/trovesuite-auth-service/issues",
        "Documentation": "https://github.com/deladetech/trovesuite-auth-service#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security",
    ],
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.116.1",
        "pydantic>=2.11.9",
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
    ],
    extras_require={
        "dev": [
            "pytest>=8.4.2",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "factory-boy>=3.3.0",
            "faker>=20.1.0",
            "black>=23.11.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
