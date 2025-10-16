from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gift-stego",
    version="1.0.0",
    author="dtm",
    author_email="dtmsecurity@gmail.com",
    description="GIF Analysis Steganography Library - Hide and recover data in GIF files using LSB steganography",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dtmsecurity/gift-stego",
    project_urls={
        "Bug Tracker": "https://github.com/dtmsecurity/gift-stego/issues",
        "Documentation": "https://dtm.uk/gif-steganography/",
        "Source Code": "https://github.com/dtmsecurity/gift-stego",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[],  # No external dependencies!
    entry_points={
        "console_scripts": [
            "gift=gift.cli:main",
        ],
    },
    keywords="steganography gif security cryptography privacy lsb watermarking data-hiding",
    license="MIT",
)
