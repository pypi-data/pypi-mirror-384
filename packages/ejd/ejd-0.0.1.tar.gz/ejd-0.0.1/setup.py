from setuptools import setup, find_packages

setup(
    name="ejd",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ejd=ejad.cli:main',  # ejad is the folder name!
        ],
    },
)
