#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS2-SYNED'
VERSION = '1.0.3'
ISRELEASED = False

DESCRIPTION = 'SYNED SYNchrotron Elements Dictionary'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Manuel Sanchez del Rio, Luca Rebuffi'
AUTHOR_EMAIL = 'lrebuffi@anl.gov'
URL = 'https://github.com/oasys-kit/OASYS2-SYNED'
DOWNLOAD_URL = 'https://github.com/oasys-kit/OASYS2-SYNED'
LICENSE = 'GPLv3'

KEYWORDS = [
    'simulator',
    'oasys2',
]

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
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
    'oasys2>=0.0.7',
    'syned-gui-2>=1.0.3',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.syned.widgets.sources":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.syned.widgets.beamline_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.syned.widgets.tools":["icons/*.png", "icons/*.jpg", "misc/*.png"],
    "orangecontrib.syned.widgets.loops": ["icons/*.png", "icons/*.jpg", "misc/*.png"],
}

ENTRY_POINTS = {
    'oasys2.addons' : ("syned = orangecontrib.syned", ),
    'oasys2.widgets' : (
        "Syned: Light Sources = orangecontrib.syned.widgets.light_sources",
        "Syned: Optical Elements = orangecontrib.syned.widgets.beamline_elements",
        "Syned: Tools = orangecontrib.syned.widgets.tools",
        "Syned: Loops = orangecontrib.syned.widgets.loops",
    ),
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
