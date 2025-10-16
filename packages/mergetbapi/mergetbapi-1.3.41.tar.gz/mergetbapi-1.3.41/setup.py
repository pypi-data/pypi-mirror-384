#!/usr/bin/env python

import os
import io
import sys
from setuptools import setup, find_packages

try:
    VERSION=os.environ['VERSION']
except KeyError:
    print('Must provide VERSION as an environment variable')
    sys.exit(1)

NAME='mergetbapi'
DESCRIPTION='Client interface to the MergeTB API'
URL = 'https://gitlab.com/mergetb/api'
EMAIL = 'bkocolos@isi.edu'
AUTHOR = 'Brian Kocoloski'
REQUIRES_PYTHON = '>=3'
REQUIRED = [
    'betterproto>=2.0.0b6',
    'grpclib>=0.4.7',
]
CLASSIFIERS = [
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Intended Audience :: Developers',
    'Intended Audience :: End Users/Desktop',
    'Development Status :: 4 - Beta',
]

HERE = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(HERE, 'README.md')) as f:
    LDESCRIPTION = f.read()

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    description=DESCRIPTION,
    long_description=LDESCRIPTION,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(),
    install_requires=REQUIRED,
    include_package_data=True,
    zip_safe=False,
    classifiers=CLASSIFIERS,
)
