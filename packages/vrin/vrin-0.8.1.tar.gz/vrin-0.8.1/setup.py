"""
Setup script for VRIN SDK
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "VRIN Hybrid RAG SDK - A powerful SDK for interacting with the VRIN Hybrid RAG system."

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return ["requests>=2.28.0"]

setup(
    name="vrin",
    version="0.8.1",
    author="VRIN Team",
    author_email="support@vrin.ai",
    description="Enterprise Hybrid RAG SDK with entity-centric extraction, zero-loss architecture, complete source attribution, constraint solver, temporal consistency, and multi-cloud deployment",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/vrin-ai/vrin-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/vrin-ai/vrin-sdk/issues",
        "Documentation": "https://docs.vrin.ai",
        "Source Code": "https://github.com/vrin-ai/vrin-sdk",
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
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "twine>=4.0.0",
            "build>=0.10.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    keywords="rag, hybrid-rag, knowledge-base, search, ai, machine-learning, nlp",
    license="MIT",
    zip_safe=False,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "vrin=vrin.cli:main",
        ],
    },
) 