# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import sys
import warnings

VERSION = 'undefined'
install_requires = ['pyprind', 'requests>=2.0.0', 'urllib3>=1.26.0']
extra = {}

with open('quartzbio/version.py') as f:
    for row in f.readlines():
        if row.startswith('VERSION'):
            exec(row)

# quartzbio-recipes requires additional packages
recipes_requires = [
    'pyyaml==5.3.1',
    'click==7.1.2',
    'ruamel.yaml==0.16.12'
]
extras_requires = {
    "recipes": recipes_requires
}

with open('README.md') as f:
    long_description = f.read()

setup(
    name='quartzbio',
    version=VERSION,
    description='The QuartzBio Python client',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    author='Precision for Medicine, Inc.',
    author_email='qb-help@precisionformedicine.com',
    url='https://github.com/quartzbio/quartzbio-python',
    packages=find_packages(),
    package_dir={'quartzbio': 'quartzbio', 'recipes': 'recipes'},
    test_suite='quartzbio.test',
    include_package_data=True,
    install_requires=install_requires,
    platforms='any',
    extras_require=extras_requires,
    entry_points={
        'console_scripts': ['quartzbio = quartzbio.cli.main:main',
                            'quartzbio-recipes = recipes.sync_recipes:sync_recipes']
    },
    classifiers=[
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    **extra
)
