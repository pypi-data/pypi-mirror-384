"""
Setup configuration for USF P1 Chatbot SDK
"""
from setuptools import setup, find_packages

# Read the contents of README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="usf-p1-chatbot-sdk",
    version="2.0.0",
    author="USF Team",
    author_email="support@ultrasafe.com",
    description="Python SDK for Civie Chatbot API v2.0.0 with comprehensive endpoint coverage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ultrasafe/usf-p1-chatbot-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/ultrasafe/usf-p1-chatbot-sdk/issues",
        "Documentation": "https://github.com/ultrasafe/usf-p1-chatbot-sdk/blob/main/README.md",
        "Source Code": "https://github.com/ultrasafe/usf-p1-chatbot-sdk",
        "API Documentation": "https://api-civie.us.inc/docs",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
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
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
    },
    keywords=[
        "civie",
        "chatbot",
        "api",
        "sdk",
        "healthcare",
        "patient management",
        "rag",
        "llm",
        "medical records",
        "document ingestion",
    ],
    include_package_data=True,
    zip_safe=False,
)
