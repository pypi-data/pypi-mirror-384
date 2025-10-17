"""Setup configuration for SecretStuff package."""

from setuptools import setup, find_packages

with open("README_PYPI.md", "r", encoding="utf-8") as fh:
    short_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="secretstuff",
    version="1.0.1",
    author="axondendrite",
    author_email="amandogra2016@gmail.com",
    maintainer="Aksman",
    maintainer_email="akshatmanihar580@gmail.com",
    description="A comprehensive PII redaction and reverse mapping library using advanced NLP models",
    long_description=short_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adw777/secretStuff",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",  # Changed from 5 to 4 since it's v0.1.0
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Text Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    keywords="pii, redaction, privacy, nlp, gliner, data-protection, anonymization, secretstuff, pii-detection, text-processing",
    project_urls={
        "Documentation": "https://github.com/adw777/secretStuff/blob/main/README.md",
        "Bug Reports": "https://github.com/adw777/secretStuff/issues",
        "Source": "https://github.com/adw777/secretStuff",
        "Changelog": "https://github.com/adw777/secretStuff/releases",
    },
)