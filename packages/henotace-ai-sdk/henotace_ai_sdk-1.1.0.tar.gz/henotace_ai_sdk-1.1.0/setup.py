"""
Setup script for Henotace AI Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="henotace-ai-sdk",
    version="1.1.0",
    author="Henotace AI Team",
    author_email="support@henotace.ai",
    description="Python SDK for Henotace AI Tutor API - Intelligent tutoring capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/henotace/henotace-ai-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
            keywords="henotace ai tutor education tutoring sdk api intelligent learning",
    project_urls={
        "Bug Reports": "https://github.com/henotace/henotace-ai-sdk-python/issues",
        "Source": "https://github.com/henotace/henotace-ai-sdk-python",
        "Documentation": "https://docs.henotace.ai",
    },
)

