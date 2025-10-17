"""Setup configuration for the Gushwork RAG SDK."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gushwork-rag",
    version="0.1.1",
    author="Gushwork",
    author_email="support@gushwork.com",
    description="Python SDK for the Gushwork RAG API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gushwork/gw-rag",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
    },
    keywords="rag retrieval ai llm chatbot langchain pinecone vector-search",
    project_urls={
        "Bug Reports": "https://github.com/gushwork/gw-rag/issues",
        "Source": "https://github.com/gushwork/gw-rag",
        "Documentation": "https://github.com/gushwork/gw-rag/tree/main/sdk/python",
    },
)

