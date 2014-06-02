#!/usr/bin/env python

version_str = '1.0c'
from setuptools import setup
import sys

if sys.version_info.major == 2:
    nltk_version = 'nltk'
else:
    nltk_version = 'nltk >= 3.0a'

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


deprecation_warning = """

    Note: metanl is no longer actively developed or supported.

    metanl was created to support the language-processing needs that ConceptNet
    5 shared with code developed at Luminoso. Those needs have diverged, to the
    point where it made the most sense to split the functionality again.

    A simplified version of metanl has been moved into the `conceptnet5`
    package, as `conceptnet5.language`.

"""
sys.stderr.write(deprecation_warning)

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
    install_requires=[nltk_version, 'ftfy >= 3'],
)
