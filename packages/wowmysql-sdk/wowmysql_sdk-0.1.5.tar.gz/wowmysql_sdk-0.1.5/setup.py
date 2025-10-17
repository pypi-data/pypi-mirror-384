"""Setup configuration for wowmysql-sdk package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wowmysql-sdk",
    version="0.2.0",
    author="WowMySQL Team",
    author_email="support@wowmysql.com",
    description="Official Python SDK for WowMySQL with S3 Storage support, SSL, and subdomain routing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wowmysql/wowmysql",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="wowmysql mysql database backend-as-a-service baas api rest s3 storage file-upload object-storage",
    project_urls={
        "Documentation": "https://wowmysql.com/docs",
        "Source": "https://github.com/wowmysql/wowmysql",
        "Tracker": "https://github.com/wowmysql/wowmysql/issues",
    },
)
