from setuptools import setup, find_packages

setup(
    name="SmartNlp",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[],  # future: add requirements like nltk, spacy if needed
    author="Yogesh Vyas",
    description="A smart NLP search module with fuzzy matching and semantic awareness.",
    url="https://github.com/yogesh517/smart-nlp-package",  # optional
    python_requires=">=3.10",
)
