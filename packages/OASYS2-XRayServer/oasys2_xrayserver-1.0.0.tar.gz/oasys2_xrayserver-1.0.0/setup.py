#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS2-XRayServer'
VERSION = '1.0.0'
ISRELEASED = True

DESCRIPTION = 'X-Ray Server: Sergey Stepanov\'s X-Ray Server on OASYS 2'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Luca Rebuffi'
AUTHOR_EMAIL = 'lrebuffi@anl.gov'
URL = 'https://github.com/oasys-kit/OASYS2-XRayServer'
DOWNLOAD_URL = 'https://github.com/oasys-kit/OASYS2-XRayServer'
LICENSE = 'GPLv3'

KEYWORDS = [
    'X-ray optics',
    'simulator',
    'oasys2',
]

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
]

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'oasys2>=0.0.1',
    'PyQtWebEngine>=5.15.7',
    'dabax',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.xrayserver.widgets.xrayserver":["icons/*.png", "icons/*.jpg", "misc/*.*"],
}

ENTRY_POINTS = {
    'oasys2.addons' : ("xrayserver = orangecontrib.xrayserver", ),
    'oasys2.widgets' : (
        "X-Ray Server = orangecontrib.xrayserver.widgets.xrayserver",
    )
}

if __name__ == '__main__':
    setup(
          name = NAME,
          version = VERSION,
          description = DESCRIPTION,
          long_description = LONG_DESCRIPTION,
          author = AUTHOR,
          author_email = AUTHOR_EMAIL,
          url = URL,
          download_url = DOWNLOAD_URL,
          license = LICENSE,
          keywords = KEYWORDS,
          classifiers = CLASSIFIERS,
          packages = PACKAGES,
          package_data = PACKAGE_DATA,
          setup_requires = SETUP_REQUIRES,
          install_requires = INSTALL_REQUIRES,
          entry_points = ENTRY_POINTS,
          include_package_data = True,
          zip_safe = False,
          )