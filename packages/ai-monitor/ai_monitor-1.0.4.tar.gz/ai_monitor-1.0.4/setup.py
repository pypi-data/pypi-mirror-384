#!/usr/bin/env python3
"""
Setup script for ai-monitor package.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read version from ai_monitor/version.py
version_dict = {}
with open(os.path.join(this_directory, 'ai_monitor', 'version.py'), 'r') as f:
    exec(f.read(), version_dict)
version = version_dict['__version__']

setup(
    name="ai-monitor",
    version="1.0.4",
    author="AI Monitor Team",
    author_email="ai-monitor@example.com",
    description="Plug & Play AI Agent Monitoring - Zero-configuration monitoring for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-monitor",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
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
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=[
        "ai", "monitoring", "llm", "agent", "observability", "prometheus",
        "opentelemetry", "tracing", "metrics", "quality-analysis",
        "hallucination-detection", "drift-detection"
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
    ],
    extras_require={
        "prometheus": ["prometheus-client>=0.15.0"],
        "tracing": [
            "opentelemetry-api>=1.22.0",
            "opentelemetry-sdk>=1.22.0",
            "opentelemetry-exporter-jaeger>=1.21.0",
        ],
        "jaeger": [
            "opentelemetry-api>=1.15.0",
            "opentelemetry-sdk>=1.15.0",
            "opentelemetry-exporter-jaeger>=1.15.0",
        ],
        "traceloop": ["traceloop-sdk>=0.47.0"],
        "system": ["psutil>=5.8.0"],
        "all": [
            "prometheus-client>=0.15.0",
            "opentelemetry-api>=1.22.0",
            "opentelemetry-sdk>=1.22.0",
            "opentelemetry-exporter-jaeger>=1.21.0",
            "psutil>=5.8.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black",
            "flake8",
            "mypy",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
