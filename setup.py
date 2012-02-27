#!/usr/bin/env python

version_str = '0.5'

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

classifiers=[
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License (GPL)',
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
    license = "http://www.gnu.org/copyleft/gpl.html",
    platforms = ["any"],
    description = doclines[0],
    classifiers = classifiers,
    long_description = "\n".join(doclines[2:]),
    packages=['metanl'],
    package_data = {'metanl': ['*.txt']},
    install_requires=['csc-utils >= 0.6', 'simplenlp >= 1.1.1', 'nltk >= 2.0b9'],
)
