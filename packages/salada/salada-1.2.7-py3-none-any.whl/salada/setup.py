# This setup.py file is deprecated.
# Use the setup.py in the parent directory instead.
# This file is kept for backwards compatibility.

from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='salada',
    version='1.2.4',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    install_requires=[
        'aiohttp',
    ],
    extras_require={
        'fast': ['orjson', 'msgpack', 'aiofiles'],
        'speed': ['ujson'],
    },
    author='ToddyTheNoobDud',
    url='https://github.com/ToddyTheNoobDud/Salad',
    description='A performant lavalink client for python',
)
