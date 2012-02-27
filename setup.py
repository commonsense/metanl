#!/usr/bin/env python

version_str = '0.5.1'

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
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development',
    'Topic :: Text Processing :: Linguistic',]

import os
README_contents = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()
doclines = README_contents.split("\n")

setup(
    name="metanl",
    version=version_str,
    maintainer='MIT Media Lab, Digital Intuition group',
    maintainer_email='conceptnet@media.mit.edu',     
    url='http://github.com/commonsense/metanl/',
    license = "MIT",
    platforms = ["any"],
    description = doclines[0],
    classifiers = classifiers,
    long_description = "\n".join(doclines[2:]),
    packages=['metanl'],
    package_data = {'metanl': ['data/*.txt']},
    install_requires=['nltk >= 2.0b9', 'setuptools'],
)
