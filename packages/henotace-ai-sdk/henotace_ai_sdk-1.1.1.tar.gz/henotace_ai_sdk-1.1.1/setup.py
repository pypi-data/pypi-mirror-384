from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="henotace-ai-sdk",
    version="1.1.1",
    author="Henotace AI Team",
    author_email="support@henotace.ai",
    description="Official Python SDK for the Henotace AI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Davidoshin/henotace-python-sdk",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["henotace_cli"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "dataclasses; python_version<'3.7'",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "henotace=henotace_cli:main",
        ]
    },
    keywords="ai, tutor, education, api, sdk",
    project_urls={
        "Bug Reports": "https://github.com/Davidoshin/henotace-python-sdk/issues",
        "Source": "https://github.com/Davidoshin/henotace-python-sdk",
        "Documentation": "https://docs.henotace.ai/python-sdk",
    },
)
