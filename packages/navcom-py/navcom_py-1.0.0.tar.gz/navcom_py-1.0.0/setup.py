from setuptools import setup, find_packages

setup(
    name="navcom",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "navcom = navcom.cli:navcom",
        ],
    },
    python_requires=">=3.7",
    author="Gaura",
    description="CLI tool to navigate git commits easily",
    license="MIT",
)
