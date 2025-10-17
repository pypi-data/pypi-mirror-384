"""Setup configuration for Code Discovery."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Dev dependencies
dev_requirements = [
    "pytest>=7.4.3",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "black>=23.12.0",
    "flake8>=6.1.0",
    "mypy>=1.7.1",
    "isort>=5.13.2",
    "pre-commit>=3.5.0",
]

setup(
    name="code-discovery",
    version="0.1.11",
    author="Code Discovery Team",
    author_email="team@codediscovery.dev",
    description="Automatic API discovery system for multiple frameworks and VCS platforms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/codediscovery",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/codediscovery/issues",
        "Source": "https://github.com/yourusername/codediscovery",
        "Documentation": "https://docs.code-discovery.io",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["main"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Framework :: Flask",
    ],
    keywords="api, openapi, swagger, documentation, discovery, spring-boot, fastapi, flask, micronaut, aspnet",
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "code-discovery=main:main",
        ],
    },
)

