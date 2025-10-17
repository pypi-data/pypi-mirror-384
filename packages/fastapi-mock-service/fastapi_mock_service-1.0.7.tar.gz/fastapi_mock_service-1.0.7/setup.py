#!/usr/bin/env python3
"""
Setup script for FastAPI Mock Service
"""

from setuptools import setup, find_packages
import os
from fastapi_mock_service import __version__, __author__, __email__


# Read README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


# Read requirements
def read_requirements(filename='requirements.txt'):
    req_path = os.path.join(os.path.dirname(__file__), filename)
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return requirements


setup(
    name="fastapi-mock-service",
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="Professional mock service library with load testing infrastructure for FastAPI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://gitlab.com/eastden4ik/fastapimockserver",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'fastapi_mock_service': ['templates/*.html'],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing :: Mocking",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.900',
        ],
    },
    entry_points={
        'console_scripts': [
            'fastapi-mock=fastapi_mock_service.cli:main',
        ],
    },
    keywords=['fastapi', 'mock', 'testing', 'api', 'load-testing', 'prometheus', 'dashboard'],
    zip_safe=False,
)
