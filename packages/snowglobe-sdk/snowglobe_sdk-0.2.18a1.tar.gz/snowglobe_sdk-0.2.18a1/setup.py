import pathlib

from setuptools import setup

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="snowglobe-sdk",
    version="0.2.18a1",
    description="A client library for accessing Snowglobe SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.9, <4",
    install_requires=[
        "httpx >= 0.23.0, < 0.29.0",
        "attrs >= 22.2.0",
        "python-dateutil >= 2.8.0, < 3",
    ],
    package_data={"src/snowglobe/sdk": ["py.typed"]},
)
