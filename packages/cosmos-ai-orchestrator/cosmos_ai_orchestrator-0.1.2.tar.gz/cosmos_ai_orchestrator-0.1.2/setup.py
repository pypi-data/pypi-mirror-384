from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cosmos_ai_orchestrator",  # PyPI-safe, unique name
    version="0.1.2",
    author="Vamsi Gudapati",
    author_email="vamsi7673916775@gmail.com",
    description="A reusable toolkit integrating Azure OpenAI and Cosmos DB for semantic search and embeddings orchestration.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vamsichowdaryg/cosmos_ai_orchestrator",
    project_urls={
        "Bug Tracker": "https://github.com/vamsichowdaryg/cosmos_ai_orchestrator/issues",
        "Source Code": "https://github.com/vamsichowdaryg/cosmos_ai_orchestrator",
    },
    packages=find_packages(where="."),  # Automatically finds src/ if used
    install_requires=[
        "openai>=1.3.0",
        "azure-cosmos>=4.5.0",
        "typing-extensions>=4.0.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
    ],
    license="MIT",
    include_package_data=True,
    keywords=[
        "Azure OpenAI", "Cosmos DB", "Semantic Search",
        "Embeddings", "AI Orchestration", "Azure", "Toolkit"
    ],
)
