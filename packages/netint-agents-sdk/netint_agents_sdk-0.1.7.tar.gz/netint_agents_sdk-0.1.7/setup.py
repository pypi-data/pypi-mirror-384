"""
Setup configuration for netint-agents-sdk.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
readme_file = Path(__file__).parent / "README.md"
try:
    long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
except Exception:
    long_description = "Python SDK for the NetIntGPT Agents API"

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="netint-agents-sdk",
    version="0.1.6",
    author="NetInt Team",
    author_email="support@netint.ai",
    description="Python SDK for the NetIntGPT Agents API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/netint/netint-agents-sdk",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    keywords="netint api sdk agents ai development",
    project_urls={
        "Bug Reports": "https://github.com/netint/netint-agents-sdk/issues",
        "Source": "https://github.com/netint/netint-agents-sdk",
        "Documentation": "https://netint-agents-sdk.readthedocs.io",
    },
)
