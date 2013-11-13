#!/usr/bin/env python

version_str = '1.0b1'

from setuptools import setup

classifiers=[
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: C',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development',
    'Topic :: Text Processing :: Linguistic',]

import os
README_contents = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
doclines = README_contents.split("\n")

setup(
    name="metanl",
    version=version_str,
    maintainer='Luminoso Technologies, Inc.',
    maintainer_email='dev@luminoso.com',
    url='http://github.com/commonsense/metanl/',
    license = "MIT",
    platforms = ["any"],
    description = doclines[0],
    classifiers = classifiers,
    long_description = "\n".join(doclines[2:]),
    packages=['metanl'],
    package_data = {'metanl': ['data/freeling/*.cfg', 'data/freeling/*.dat']},
    install_requires=['nltk >= 3.0a3', 'ftfy >= 3'],
)
