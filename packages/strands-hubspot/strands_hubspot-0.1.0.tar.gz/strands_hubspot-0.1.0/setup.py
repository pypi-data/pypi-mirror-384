"""Setup configuration for strands-hubspot package."""

from pathlib import Path

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="strands-hubspot",
    version="0.1.0",
    description="HubSpot CRM tool for Strands Agents SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Eray Keskin",
    author_email="eraykeskinmac@gmail.com",
    url="https://github.com/eraykeskinmac/strands-hubspot",
    packages=find_packages(),
    install_requires=[
        "strands-agents>=1.11.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    python_requires=">=3.9",
    keywords=["strands", "ai", "agents", "hubspot", "crm", "sales", "marketing"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    project_urls={
        "Documentation": "https://github.com/eraykeskinmac/strands-hubspot",
        "Source": "https://github.com/eraykeskinmac/strands-hubspot",
        "Bug Reports": "https://github.com/eraykeskinmac/strands-hubspot/issues",
    },
)

