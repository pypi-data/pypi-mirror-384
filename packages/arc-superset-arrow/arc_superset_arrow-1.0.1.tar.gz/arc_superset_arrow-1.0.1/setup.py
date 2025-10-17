"""
Arc Superset Dialect - SQLAlchemy dialect for Arc time-series database
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arc-superset-arrow",
    version="1.0.1",
    author="Arc Core Team",
    author_email="support@basekick.net",
    description="SQLAlchemy dialect for Arc time-series database with Apache Arrow support for Apache Superset",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/basekick-labs/arc-superset-arrow",
    project_urls={
        "Bug Tracker": "https://github.com/basekick-labs/arc-superset-arrow/issues",
        "Documentation": "https://github.com/basekick-labs/arc-superset-arrow",
        "Source Code": "https://github.com/basekick-labs/arc-superset-arrow",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    py_modules=["arc_dialect"],
    python_requires=">=3.8",
    install_requires=[
        "SQLAlchemy>=1.4.0,<3.0.0",
        "requests>=2.31.0",
        "pyarrow>=21.0.0",
    ],
    entry_points={
        "sqlalchemy.dialects": [
            "arc = arc_dialect:ArcDialect",
            "arc.api = arc_dialect:ArcDialect",
        ]
    },
    keywords="arc superset sqlalchemy dialect timeseries database",
    zip_safe=False,
)
