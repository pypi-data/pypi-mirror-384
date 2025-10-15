from setuptools import setup

# Read README as long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eamin",  # Note: This name must be unique on PyPI
    version="0.1.0",
    description="A fun Python package that outputs attribute names dynamically",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",  # Replace with your name
    author_email="your.email@example.com",  # Replace with your email
    url="https://github.com/yourusername/eamin",  # Replace with your GitHub URL
    packages=["eamin"],  # Package name
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="dynamic, magic, metaprogramming, fun, attribute",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/eamin/issues",
        "Source": "https://github.com/yourusername/eamin",
    },
)

