from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Palantyra",
    version="1.0.3",
    author="Palantyra Team",
    author_email="sharmatanmay617@gmail.com",
    description="AI observability platform for LLM applications - Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tanmaysharma2001/palantyra-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
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
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "typing-extensions>=4.0.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-otlp-proto-grpc>=1.20.0",
        "opentelemetry-instrumentation>=0.41b0",
        "opentelemetry-instrumentation-openai>=0.20.0",
    ],
    extras_require={
        "async": ["httpx>=0.23.0", "aiohttp>=3.8.0"],
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.3.0"],
        "full": [
            "httpx>=0.23.0",
            "aiohttp>=3.8.0", 
            "openai>=1.0.0",
            "anthropic>=0.3.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
    },
)