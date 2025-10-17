#!/usr/bin/env python3
"""
Setup script for DcisionAI MCP Server
=====================================

A Model Context Protocol (MCP) server for AI-powered business optimization
with industry-specific workflows and Qwen 30B integration.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        # Fallback requirements if requirements.txt is not found
        return [
            "fastmcp>=2.12.0",
            "uvicorn>=0.31.0",
            "boto3>=1.40.0",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0.0",
            "click>=8.0.0",
            "requests>=2.28.0",
            "pydantic>=2.0.0",
            "typing_extensions>=4.0.0",
            "httpx>=0.24.0",
            "aiohttp>=3.8.0",
            "pandas>=1.5.0",
            "numpy>=1.24.0",
            "asyncio-mqtt>=0.11.0",
            "aiofiles>=23.0.0",
            "structlog>=23.0.0",
            "rich>=13.0.0"
        ]

setup(
    name="dcisionai-mcp-server",
    version="1.0.0",
    author="DcisionAI Team",
    author_email="team@dcisionai.com",
    description="AI-powered business optimization MCP server with industry-specific workflows",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/dcisionai/dcisionai-mcp-server",
    project_urls={
        "Bug Reports": "https://github.com/dcisionai/dcisionai-mcp-server/issues",
        "Source": "https://github.com/dcisionai/dcisionai-mcp-server",
        "Documentation": "https://docs.dcisionai.com",
        "Homepage": "https://platform.dcisionai.com",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "aws": [
            "boto3>=1.26.0",
            "botocore>=1.29.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dcisionai-mcp-server=dcisionai_mcp_server.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dcisionai_mcp_server": [
            "workflows/*.json",
            "config/*.yaml",
            "templates/*.json",
        ],
    },
    keywords=[
        "mcp",
        "model-context-protocol",
        "ai",
        "optimization",
        "business-intelligence",
        "decision-support",
        "qwen",
        "bedrock",
        "agentcore",
        "workflow-automation",
    ],
    zip_safe=False,
)
