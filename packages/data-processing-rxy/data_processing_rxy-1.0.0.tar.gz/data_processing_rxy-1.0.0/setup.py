# setup.py
from setuptools import setup, find_packages

setup(
    name="data_processing_rxy",
    version="1.0.0",
    packages=find_packages(),  # 关键：自动识别 data_processing 包
    author="Your Name",
    author_email="your@email.com",
    description="A data processing library with numeric, text, and stats tools",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    install_requires=["numpy>=1.21.0"],
    python_requires=">=3.8",
)