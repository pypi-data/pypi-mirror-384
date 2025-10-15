from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="uop-mcp-server",
    version="2.0.2",
    author="Unified Offer Protocol",
    author_email="support@unifiedoffer.com",
    description="Universal MCP Server for AI-powered e-commerce integration. Connect AI apps to Shopify, WooCommerce, and Shopware 6.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Chris85appding/unified-offer-protocol-front",
    project_urls={
        "Homepage": "https://unifiedoffer.com/mcp",
        "Documentation": "https://unifiedoffer.com/docs",
        "Bug Tracker": "https://github.com/Chris85appding/unified-offer-protocol-front/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
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
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
)
