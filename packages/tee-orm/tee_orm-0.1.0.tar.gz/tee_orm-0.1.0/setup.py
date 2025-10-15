from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tee-orm",
    version="0.1.0",
    author="tian-gua",
    author_email="your-email@example.com",
    description="一个小巧的 Python ORM 框架，带有完整的类型系统支持",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tian-gua/tee",
    packages=find_packages(),
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
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyMySQL>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "flake8>=5.0.0",
        ],
    },
    keywords="orm database mysql python typing",
    project_urls={
        "Bug Reports": "https://github.com/tian-gua/tee/issues",
        "Source": "https://github.com/tian-gua/tee",
        "Documentation": "https://github.com/tian-gua/tee#readme",
    },
)