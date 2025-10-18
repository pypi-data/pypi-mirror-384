from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="ctmu",
    version="2.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "qrcode[pil]>=7.4.2",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "click>=8.1.0"
    ],
    entry_points={
        "console_scripts": [
            "ctmu=ctmu.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="CTMU Development Team",
    description="Swiss Army Knife CLI tool for macOS - QR codes, hashing, networking, file ops, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JohnThre/CTMU-for-macOS",
    project_urls={
        "Bug Tracker": "https://github.com/JohnThre/CTMU-for-macOS/issues",
        "Documentation": "https://github.com/JohnThre/CTMU-for-macOS#readme",
        "Source Code": "https://github.com/JohnThre/CTMU-for-macOS",
    },
    license="GPL-3.0",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS",
        "Environment :: Console",
        "Topic :: Utilities",
        "Topic :: System :: Systems Administration",
    ],
)