from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()

setup(
    name='pyfcg',
    version='0.3',
    packages=find_packages(), # automatically includes all packages through their __init__.py files
    install_requires=[
        "wget==3.2",          # used for downloading FCG Go
        "requests==2.32.3",   # used for HTTP requests to FCG Go
        "platformdirs",     # used to store FCG Go in user-specific data dir
        "penman",
    ],

    # Sets the (short) project description on PyPI
    description="A Python port of Fluid Construction Grammar",

    # Sets README.md as the project description on PyPI
    long_description=description,
    long_description_content_type="text/markdown",
)
