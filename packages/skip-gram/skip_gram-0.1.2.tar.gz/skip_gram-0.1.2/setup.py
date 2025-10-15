from setuptools import setup, find_packages

setup(
    name="skip_gram",
    version="0.1.2",
    author="Krishna Simha",
    author_email="krishna2005simha@gmail.com",
    description="Skip-gram model with hierarchical softmax from scratch in PyTorch",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/agentksimha/skip_gram",
    packages=find_packages(),
    install_requires=["torch", "nltk", "numpy"],
    python_requires=">=3.8",
)
