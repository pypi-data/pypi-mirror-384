from setuptools import setup, find_packages
import os

# Read version from __init__.py
version = {}
with open(os.path.join("docx_json_replacer", "__init__.py")) as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="docx-json-replacer",
    version=version["__version__"],
    author="liuspatt",
    author_email="liuspatt@example.com",
    description="Replace template placeholders in DOCX files with JSON data, supports tables with HTML formatting and cell-level styling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liuspatt/docx-json-replacer",
    project_urls={
        "Bug Tracker": "https://github.com/liuspatt/docx-json-replacer/issues",
        "Documentation": "https://github.com/liuspatt/docx-json-replacer#readme",
        "Source Code": "https://github.com/liuspatt/docx-json-replacer",
        "Changelog": "https://github.com/liuspatt/docx-json-replacer/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "test_env", "test_env.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
        "Topic :: Text Processing :: Markup :: HTML",
        "Typing :: Typed",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-docx>=0.8.11",
        "docxcompose>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "docx-json-replacer=docx_json_replacer.cli:main",
        ],
    },
    keywords=[
        "docx",
        "json",
        "template",
        "replace",
        "table",
        "html",
        "formatting",
        "cell-styling",
        "document-generation",
        "office",
        "word",
        "automation",
    ],
    include_package_data=True,
    zip_safe=False,
)