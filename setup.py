"""Setup configuration for mcp-switchboard."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-switchboard",
    version="0.1.0",
    author="MCP Switchboard Contributors",
    description="Intelligent MCP server orchestration and lifecycle management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/mcp-switchboard",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.23",
            "pytest-cov>=4.1",
            "black>=24.0",
            "ruff>=0.3.0",
            "mypy>=1.9",
        ],
        "automation": [
            "playwright>=1.42",
            "keyring>=25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-switchboard=mcp_switchboard.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp_switchboard": ["config/registry.yaml", "state/schema.sql"],
    },
)
