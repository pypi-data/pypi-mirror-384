"""Setup script for QUTEN optimizer."""
from setuptools import setup, find_packages
import os

# Version management
__version__ = "1.0.0"

# Read long description from README
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="quten-optimizer",
    version=__version__,
    author="Your Name",
    author_email="your.email@example.com",
    description="Quantum-inspired PyTorch optimizer with tunneling and observation-based decoherence",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/quten",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    py_modules=["quten"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: Pytorch",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
            "matplotlib>=3.5.0",
            "numpy>=1.21.0",
        ],
        "viz": [
            "matplotlib>=3.5.0",
            "numpy>=1.21.0",
        ],
    },
    keywords=[
        "optimization",
        "deep-learning",
        "pytorch",
        "quantum-inspired",
        "optimizer",
        "machine-learning",
        "neural-networks",
        "gradient-descent",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/quten/issues",
        "Source": "https://github.com/yourusername/quten",
        "Documentation": "https://github.com/yourusername/quten/blob/main/README.md",
        "Ablation Study": "https://github.com/yourusername/quten/blob/main/ABLATION_STUDY.md",
    },
    license="MIT",
    zip_safe=False,
)
