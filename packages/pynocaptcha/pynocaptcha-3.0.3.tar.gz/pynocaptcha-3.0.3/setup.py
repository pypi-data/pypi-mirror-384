#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='pynocaptcha',
    version='3.0.3',
    description='nocaptcha.io api',
    long_description='nocaptcha.io python api',
    install_requires=["curl_cffi", "loguru", "rnet"],
    license='MIT',
    packages=["pynocaptcha/crackers", "pynocaptcha/magneto", "pynocaptcha"],
    package_dir={'pynocaptcha': 'pynocaptcha'},
    platforms=["all"],
    include_package_data=True,
    zip_safe=False,
    keywords='nocaptcha',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],
)
