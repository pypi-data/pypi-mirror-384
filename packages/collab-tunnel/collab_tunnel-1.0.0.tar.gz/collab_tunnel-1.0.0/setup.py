"""
Setup file for collab-tunnel Python package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="collab-tunnel",
    version="1.0.0",
    author="Antun Jurkovic",
    author_email="antunjurkovic@gmail.com",
    description="Python client library for the Collaboration Tunnel Protocol (TCT)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/antunjurkovic-collab/collab-tunnel-python",
    packages=find_packages(),
    keywords=["ai", "crawler", "optimization", "bandwidth", "llm", "http", "protocol"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    project_urls={
        "Homepage": "https://llmpages.org",
        "Documentation": "https://llmpages.org/docs/python/",
        "Repository": "https://github.com/antunjurkovic-collab/collab-tunnel-python",
        "Bug Tracker": "https://github.com/antunjurkovic-collab/collab-tunnel-python/issues",
    },
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
        ]
    },
    entry_points={
        "console_scripts": [
            "collab-tunnel=collab_tunnel.cli:main",
        ],
    },
)
