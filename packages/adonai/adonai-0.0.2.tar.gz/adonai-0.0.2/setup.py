from pathlib import Path

import setuptools

VERSION = "0.0.2"

NAME = "adonai"

INSTALL_REQUIRES = [
    "furones>= 0.1.2"
]

setuptools.setup(
    name=NAME,
    version=VERSION,
    description="Compute the Approximate Chromatic Number for undirected graph encoded in DIMACS format.",
    url="https://github.com/frankvegadelgado/adonai",
    project_urls={
        "Source Code": "https://github.com/frankvegadelgado/adonai"
    },
    author="Frank Vega",
    author_email="vega.frank@gmail.com",
    license="MIT License",
    classifiers=[
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
    ],
    python_requires=">=3.12",
    # Requirements
    install_requires=INSTALL_REQUIRES,
    packages=["adonai"],
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'salve = adonai.app:main',
            'test_salve = adonai.test:main',
            'batch_salve = adonai.batch:main'
        ]
    }
)