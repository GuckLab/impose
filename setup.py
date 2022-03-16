#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import exists, dirname, realpath
from setuptools import setup, find_packages
import sys


maintainer = u"Paul Müller"
maintainer_email = "dev@craban.de"
description = 'Fit and superimpose shapes from different imaging modalities'
name = 'impose'
year = "2020"

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
from _version import version  # noqa: E402


setup(
    name=name,
    maintainer=maintainer,
    maintainer_email=maintainer_email,
    url='https://github.com/GuckLab/impose',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="GPL v3",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    install_requires=["czifile==2019.7.2",  # bc cgohlke and used for signature
                      "bmlab>=0.1.2",
                      "h5py>=2.10.0",
                      "numpy>=1.17.0",
                      "pyqt6>=6.2.0",
                      "pyqtgraph==0.12.4",
                      "scikit-image>=0.17.2",
                      "scipy>=0.12.0",  # compute size of polygon shape
                      "imageio",  # open image files
                      ],
    python_requires=">=3.7",
    keywords=["image analysis", "biology", "microscopy"],
    classifiers=['Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 'Topic :: Scientific/Engineering :: Visualization',
                 'Intended Audience :: Science/Research',
                 ],
    platforms=['ALL'],
)
