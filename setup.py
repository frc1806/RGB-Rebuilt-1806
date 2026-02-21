"""
RGB-Rebuilt-1806 Setup
FRC Robot LED Controller for Orange Pi 5
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rgb-rebuilt-1806",
    version="0.1.0",
    author="SWAT Team 1806",
    description="FRC Robot LED Controller for Orange Pi 5 with Network Tables",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swat1806/RGB-Rebuilt-1806",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "spidev>=3.5",  # SPI interface for LED control
        "pyntcore>=2026.0.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "simulator": ["pyserial>=3.5"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rgb-rebuilt=rgb_reefscape.main:main",
        ],
    },
)
