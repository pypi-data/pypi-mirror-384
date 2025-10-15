from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='pappardelle',
    version='0.14',
    long_description_content_type='text/markdown',
    long_description=long_description,
    packages=find_packages(),
    install_requires=[
    ]
)
