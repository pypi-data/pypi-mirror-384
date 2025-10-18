from setuptools import setup, find_packages

setup(
    name="famo-data-validator",
    version="0.1.5",
    author="Famo",
    author_email="CoreByMostafa@gmail.com",
    description="Python data validation library with type hints and schema support",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/famo-codes/data_validator",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "validators>=0.35.0"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="data validation serializer schema python",
)
