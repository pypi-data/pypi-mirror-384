from setuptools import setup, find_packages

setup(
    name='easyibkr',
    version='0.1.0',
    author='Andy Suri',
    description='Helper functions for easier IBKR trade automation using ib_insync.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['ib_insync'],
    python_requires='>=3.8',
)