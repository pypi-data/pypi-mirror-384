"""
AssertLang setup configuration.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="assertlang",
    version="2.1.0b4",
    author="AssertLang Contributors",
    author_email="hello@assertlang.dev",
    description="Executable contracts for multi-agent systems - deterministic coordination across frameworks and languages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AssertLang/AssertLang",
    project_urls={
        "Documentation": "https://github.com/AssertLang/AssertLang/tree/main/docs",
        "Source": "https://github.com/AssertLang/AssertLang",
        "Issues": "https://github.com/AssertLang/AssertLang/issues",
        "Website": "https://assertlang.dev",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: System :: Distributed Computing",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    keywords=[
        "mcp",
        "model-context-protocol",
        "agent",
        "microservices",
        "code-generation",
        "multi-language",
        "ai",
        "langchain",
        "opentelemetry",
        "rpc",
        "sdk",
        "testing",
    ],
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies
        "requests>=2.31.0",
        "pyyaml>=6.0.0",
        "jsonschema>=4.0.0",

        # CLI dependencies
        # (argparse is built-in)
        "tomli>=2.0.0; python_version<'3.11'",  # TOML parsing (built-in for 3.11+)
        "tomli-w>=1.0.0",  # TOML writing

        # Testing framework dependencies
        # (uses requests already specified)
    ],
    extras_require={
        # Server generation dependencies (optional)
        "server": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "slowapi>=0.1.9",
            "python-multipart>=0.0.6",
        ],

        # AI features (optional, for Python servers)
        "ai": [
            "langchain>=0.1.0",
            "langchain-anthropic>=0.1.0",
            "langchain-core>=0.1.0",
        ],

        # Observability features (optional, for Python servers)
        "observability": [
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "opentelemetry-instrumentation-fastapi>=0.41b0",
        ],

        # Workflow features (optional, for Python servers)
        "workflows": [
            "temporalio>=1.5.0",
        ],

        # Development dependencies
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.10.0",
            "flake8>=6.1.0",
            "mypy>=1.6.0",
            "ipython>=8.17.0",
            "ipdb>=0.13.13",
            "click>=8.0.0",
        ],

        # Documentation dependencies
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],

        # All optional features
        "all": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "slowapi>=0.1.9",
            "python-multipart>=0.0.6",
            "langchain>=0.1.0",
            "langchain-anthropic>=0.1.0",
            "langchain-core>=0.1.0",
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "opentelemetry-instrumentation-fastapi>=0.41b0",
            "temporalio>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "asl=assertlang.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "assertlang": ["py.typed"],
    },
    zip_safe=False,
)
