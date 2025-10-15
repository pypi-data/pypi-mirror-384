from setuptools import setup, find_packages

setup(
    name="yognlp",
    version="1.0.0",
    author="Yogesh Vyas",
    author_email="vyasyogesh517@gmail.com",
    description="A lightweight NLP semantic search and command-detection module",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yognlp",
    packages=find_packages(),
    install_requires=[
        "difflib",
        "regex",
    ],
    python_requires=">=3.8",
)
