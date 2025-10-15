"""
Setup script for Media Crawler package.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="pymedia-crawler",
    version="1.0.0",
    author="Hasan Ragab",
    author_email="hasanmragab@gmail.com",
    description="A robust, extensible web crawler for downloading media content from YouTube, SoundCloud, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hasanragab/media-crawler",
    packages=find_packages(exclude=["tests", "examples", "scripts", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "auto-chromedriver": [
            "webdriver-manager>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "media-crawler=cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "media_crawler": ["py.typed"],
    },
    zip_safe=False,
)
