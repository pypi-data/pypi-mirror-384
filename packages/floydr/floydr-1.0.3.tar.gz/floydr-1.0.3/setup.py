from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="floydr",
    version="1.0.3",
    author="Floydr Team",
    author_email="hello@floydr.dev",
    description="A zero-boilerplate framework for building interactive ChatGPT widgets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/floydr-framework/floydr",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastmcp>=0.1.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.20.0",
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "floydr=floydr.cli.main:cli",
        ],
    },
    keywords="chatgpt, widgets, mcp, framework, react",
    project_urls={
        "Bug Reports": "https://github.com/floydr-framework/floydr/issues",
        "Source": "https://github.com/floydr-framework/floydr",
        "Documentation": "https://floydr.dev/docs",
    },
)

