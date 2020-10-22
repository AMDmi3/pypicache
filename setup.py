#!/usr/bin/env python3

from setuptools import setup
from pypicache import __version__ as version


def read_requirements(filename):
    with open(filename, 'r') as f:
        return [line for line in f.readlines() if not line.startswith('-')]


setup(
    name='pypicache',
    version=version,
    description='Accumulator and dump generator for fresh PyPi package data',
    author='Dmitry Marakasov',
    author_email='amdmi3@amdmi3.ru',
    url='https://github.com/repology/pypicache/',
    license='GNU General Public License v3 or later (GPLv3+)',
    packages=['pypicache'],
    entry_points={
        "console_scripts": [
            "pypicache = pypicache.__main__:main"
        ]
    },
    classifiers=[
        'Topic :: System :: Software Distribution',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.9',
    install_requires=read_requirements('requirements.txt')
)
