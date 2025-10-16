from setuptools import setup

setup(
    name="syntheseus-chemformer",
    version="0.3.0",
    description="Fork of Chemformer for use in the syntheseus library",
    package_dir={
        "chemformer": ".",
        "chemformer.molbart": "molbart"
    },
    package_data={"": ["*.txt"]},
    install_requires=["syntheseus-PySMILESutils"],
    url="https://github.com/kmaziarz/Chemformer",
)
