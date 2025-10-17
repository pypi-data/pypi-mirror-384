"""
Setup configuration for predev_api package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="predev-api",
    version="0.2.0",
    author="Pre.dev",
    author_email="support@pre.dev",
    description="Python client for the Pre.dev Architect API - Generate comprehensive software specifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/predotdev/predev-api",
    packages=find_packages(exclude=["tests", "tests.*"]),
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
    license="MIT",
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords="predev api specification architect ai",
    project_urls={
        "Documentation": "https://docs.pre.dev/api-reference/introduction",
        "Bug Reports": "https://github.com/predotdev/predev-api/issues",
        "Source": "https://github.com/predotdev/predev-api",
    },
)
