"""
Dataset Toolkit - 一个用于计算机视觉数据集处理的Python工具包
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dataset-toolkit",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="一个用于加载、处理和导出计算机视觉数据集的工具包",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dataset-toolkit",
    packages=find_packages(exclude=["tests", "examples", "outputs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
        ],
    },
    entry_points={
        "console_scripts": [
            "dataset-toolkit=dataset_toolkit.cli:main",
        ],
    },
)

