# setup.py
"""Setup configuration for PyPI"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dsf-label-sdk",
    version="1.1.10",
    author="Jaime Alexander Jimenez",
    author_email="contacto@softwarefinanzas.com.co",
    description="Professional SDK for DSF Label Adaptive Formula API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaimeajl/dsf-label-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
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
            "flake8>=3.9",
            "mypy>=0.900",
        ]
    },
    keywords="dsf label adaptive formula evaluation api sdk",
    project_urls={
        "Bug Tracker": "https://github.com/jaimeajl/dsf-label-sdk/issues",
        "Documentation": "https://docs.jaimeajl.com/dsf-label-sdk",
        "Source Code": "https://github.com/jaimeajl/dsf-label-sdk",
    },
)