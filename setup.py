# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

"pixcat setuptools file"

from setuptools import setup, find_packages

from pixcat import __about__


def get_readme():
    with open("README.md", "r") as readme:
        return readme.read()


setup(
    name        = __about__.__pkg_name__,
    version     = __about__.__version__,

    author       = __about__.__author__,
    author_email = __about__.__email__,
    license      = __about__.__license__,

    description                   = __about__.__doc__,
    long_description              = get_readme(),
    long_description_content_type = "text/markdown",

    python_requires  = ">=3.6, <4",
    install_requires = [
        "blessed",
        "dataclasses;python_version<'3.7'",
        "docopt",
        "pillow",
        "requests"
    ],

    include_package_data = True,
    packages             = find_packages(),
    entry_points    = {
        "console_scripts": [
            f"{__about__.__pkg_name__}={__about__.__pkg_name__}.cli:main"
        ]
    },

    url      = "https://github.com/mirukan/pixcat",
    keywords = "kitty api cli terminal print display resize scale image " \
               "picture graphic icat",

    classifiers=[
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",

        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",

        "Environment :: Console",

        "Topic :: Multimedia :: Graphics :: Viewers",
        "Topic :: Terminals",

        ("License :: OSI Approved :: "
         "GNU Lesser General Public License v3 or later (LGPLv3+)"),

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",

        "Natural Language :: English",

        "Operating System :: POSIX",
    ]
)
