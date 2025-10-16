import setuptools
from pathlib import Path
setuptools.setup(
    name="aizpdf",
    version="0.0.1",
    license="MIT",
    long_description=Path("README.md").read_text(),
    packages=setuptools.find_packages(exclude=["test", "data"]))
