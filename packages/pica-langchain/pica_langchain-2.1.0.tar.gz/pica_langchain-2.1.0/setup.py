from setuptools import setup, find_packages

setup(
    name="pica-langchain",
    version="2.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.3.25,<1.0.0",
        "langchain_openai>=0.3.8,<1.0.0",
        "pydantic>=2.11.2,<3.0.0",
        "requests>=2.32.3,<3.0.0",
        "requests-toolbelt>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest==8.3.5",
            "black==25.1.0",
            "isort==6.0.1",
            "mypy==1.15.0",
            "mcp>=1.0.0",
            "langchain-mcp-adapters>=0.1.0",
        ],
    },
    python_requires=">=3.8",
    author="Pica",
    author_email="support@picaos.com",
    description="Pica LangChain SDK",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://www.picaos.com/",
    project_urls={
        "Documentation": "https://docs.picaos.com/sdk/langchain",
        "Source": "https://github.com/picahq/pica-langchain",
        "Releases": "https://github.com/picahq/pica-langchain/releases",
        "Issue Tracker": "https://github.com/picahq/pica-langchain/issues",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
