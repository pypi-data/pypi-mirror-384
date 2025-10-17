import setuptools
from pathlib import Path

setuptools.setup(
    name="ny_lektion",
    version="1.0.0",
    author="Sam Parsakian",
    description="A simple CLI tool to scaffold new lektion projects",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["tests", "data"]),
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "ny_lektion=ny_lektion.ny_lektion:main",
        ],
    },
    include_package_data=True,
)
