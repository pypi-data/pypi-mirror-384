from setuptools import setup, find_packages

setup(
    name='kaqing',
    version='2.0.77',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'qing = adam.cli:cli'
        ]
    }
)
