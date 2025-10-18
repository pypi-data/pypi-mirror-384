from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="antonnia-apps",
    version="1.0.1",
    author="Antonnia",
    author_email="support@antonnia.com",
    description="Python SDK for Antonnia Apps API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/antonnia-com-br/antonnia-apps",
    project_urls={
        "Homepage": "https://antonnia.com",
        "Documentation": "https://docs.antonnia.com/apps",
        "Bug Tracker": "https://github.com/antonnia-com-br/antonnia-apps/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.7.0,<3.0.0",
        "typing-extensions>=4.0.0; python_version<'3.10'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
        ],
    },
    package_data={
        "antonnia.apps": ["py.typed"],
    },
    keywords=["antonnia", "apps", "api", "sdk"],
    zip_safe=False,
)