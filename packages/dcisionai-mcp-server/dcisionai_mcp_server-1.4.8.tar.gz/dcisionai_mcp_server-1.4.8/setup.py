#!/usr/bin/env python3
"""
Setup script for DcisionAI MCP Server
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dcisionai-optimization",
    version="1.0.0",
    author="DcisionAI",
    author_email="contact@dcisionai.com",
    description="Optimization Intelligence for AI Workflows via Model Context Protocol (MCP)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/dcisionai/dcisionai-mcp-platform",
    project_urls={
        "Bug Reports": "https://github.com/dcisionai/dcisionai-mcp-platform/issues",
        "Source": "https://github.com/dcisionai/dcisionai-mcp-platform",
        "Documentation": "https://docs.dcisionai.com",
        "Homepage": "https://www.dcisionai.com",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dcisionai-mcp=dcisionai_mcp_server.robust_mcp:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "optimization",
        "mathematical-programming",
        "mcp",
        "model-context-protocol",
        "ai",
        "artificial-intelligence",
        "decision-making",
        "operations-research",
        "linear-programming",
        "manufacturing",
        "healthcare",
        "retail",
        "marketing",
        "financial",
        "logistics",
        "energy",
    ],
)
