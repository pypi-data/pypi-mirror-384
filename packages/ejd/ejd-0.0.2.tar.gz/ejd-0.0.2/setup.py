from setuptools import setup, find_packages

setup(
    name="ejd",
    version="0.0.2",
    packages=find_packages(),
    install_requires=[
        "google-generativeai>=0.3.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'ejd=ejad.cli:main',  # ejad is the folder name!
        ],
    },
)
