#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from jenskipper import __version__


HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
NEWS = open(os.path.join(HERE, 'NEWS.rst')).read()


setup(
    name='jenskipper',
    version=__version__,
    description="",
    long_description=README + '\n\n' + NEWS,
    classifiers=[],
    keywords='',
    author='Luper Rouch',
    author_email='luper.rouch@gmail.com',
    url='',
    license='Apache Software License 2.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'click>=7.0',
        'requests[security]',
        'pyyaml',
        'jinja2',
        'configobj',
        'coloredlogs',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'lxml',
            'sphinx',
            'requests-mock',
        ],
    },
    entry_points={
        'console_scripts':
            ['jk=jenskipper.cli.main:main']
    }
)
