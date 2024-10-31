# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import setup

setup(
    name = 'cod',
    version = '0.0.1',

    url = 'https://github.com/tanhaoqiang/',
    description = 'C source code package manager',
    license = "AGPL-3.0-only",

    classifiers = [
        "Topic :: Software Development :: Build Tools",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: C",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: Console",
        "Intended Audience :: Developers",
    ],

    author = 'taohaoqiang',
    author_email = '',

    packages = ['cod'],
    install_requires = ['ninja', 'ziglang', 'solv']
)
