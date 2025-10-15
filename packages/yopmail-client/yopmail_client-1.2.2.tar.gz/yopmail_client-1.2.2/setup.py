"""
Setup script for YOPmail Client package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yopmail-client",
    version="1.2.2",
    author="Firas Guendouz",
    author_email="firasguendouz@example.com",
    description="A clean, modular Python client for YOPmail disposable email service with send and RSS functionality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/firasguendouz/yopmail_auto",
    project_urls={
        "Bug Reports": "https://github.com/firasguendouz/yopmail_auto/issues",
        "Source": "https://github.com/firasguendouz/yopmail_auto",
        "Documentation": "https://github.com/firasguendouz/yopmail_auto#readme",
    },
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
        "Topic :: Communications :: Email",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "beautifulsoup4>=4.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "yopmail-client=yopmail_client.cli:main",
        ],
    },
)
