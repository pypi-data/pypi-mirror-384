from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="sso-apigee-client",
    version="2.7.0",
    author="Your Organization",
    author_email="dev@yourorg.com",
    description="Python client library for APIGEE Service and MOMRAH SSO with JWT-based authentication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/sso-apigee-service",
    project_urls={
        "Documentation": "https://github.com/yourorg/sso-apigee-service",
        "Source": "https://github.com/yourorg/sso-apigee-service",
        "Issues": "https://github.com/yourorg/sso-apigee-service/issues",
    },
    packages=find_packages(),
    keywords=["apigee", "api", "gateway", "client", "sdk", "fastapi", "momrah", "sso", "oauth", "oidc", "jwt", "authentication"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Framework :: AsyncIO",
        "Typing :: Typed",
    ],
    license="MIT",
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
        "python-jose[cryptography]>=3.3.0",
    ],
    extras_require={
        "fastapi": ["fastapi>=0.104.0"],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "ruff>=0.1.0",
        ],
    },
)
