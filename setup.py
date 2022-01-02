import os
import pathlib

from setuptools import setup
from setuptools_github import tools

initfile = pathlib.Path(__file__).parent / "mono2repo.py"
version = tools.update_version(initfile, os.getenv("GITHUB_DUMP"))

setup(
    name="mono2repo",
    version=version,
    url="https://github.com/cav71/mono2repo",
    py_modules=[
        "mono2repo",
    ],
    entry_points={
        "console_scripts": ["mono2repo=mono2repo:main"],
    },
    description="extract a monorepo subdir",
    long_description=pathlib.Path("README.rst").read_text(),
    long_description_content_type="text/x-rst",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
)
