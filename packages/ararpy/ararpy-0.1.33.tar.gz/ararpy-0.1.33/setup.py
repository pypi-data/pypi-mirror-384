#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ==========================================
# Copyright 2023 Yang 
# ararpy - setup
# ==========================================
#
#
#

import setuptools
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

setuptools.setup(
    name='ararpy',  #
    version='0.1.33',  # version
    author='Yang Wu',
    author_email='wuycug@hotmail.com',
    description='A project for Ar-Ar geochronology',  # short description
    long_description=long_description,  # detailed description in README.md
    long_description_content_type='text/markdown',
    url='https://github.com/wuyangchn/ararpy.git',  # github url
    packages=setuptools.find_packages(),
    package_data={'ararpy': ['examples/*']},
    # install_requires=[
    #     "chardet", "numpy", "OriginExt", "pandas", "parse", "python_dateutil",
    #     "scipy", "setuptools", "xlrd", "XlsxWriter", "pdf_maker"
    # ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    license='MIT',
    python_requires='>=3.5',
)
