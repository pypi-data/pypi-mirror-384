"""
Minimal setup.py for WooCommerce Gemini Query Generator.
Uses pyproject.toml for most metadata, but ensures README is included for PyPI rendering.
"""

from setuptools import setup

if __name__ == "__main__":
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()

    setup(
	 name="woocommerce-gemini-query",
	 version="0.1.2", 
        long_description=long_description,
        long_description_content_type="text/markdown",
    )
