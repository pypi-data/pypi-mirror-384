#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS1-SYNED'
VERSION = '1.0.52'
ISRELEASED = False

DESCRIPTION = 'SYNED SYNchrotron Elements Dictionary'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Manuel Sanchez del Rio, Luca Rebuffi'
AUTHOR_EMAIL = 'lrebuffi@anl.gov'
URL = 'https://github.com/oasys-kit/OASYS-SYNED'
DOWNLOAD_URL = 'https://github.com/oasys-kit/OASYS-SYNED'
LICENSE = 'GPLv3'

KEYWORDS = (
    'simulator',
    'oasys1',
)

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'oasys1>=1.2.131',
    'syned-gui>=1.0.3',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.syned.widgets.sources":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.syned.widgets.beamline_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.syned.widgets.tools":["icons/*.png", "icons/*.jpg", "misc/*.png"],
    "orangecontrib.syned.widgets.scanning": ["icons/*.png", "icons/*.jpg", "misc/*.png"],
}

NAMESPACE_PACAKGES = ["orangecontrib", "orangecontrib.syned", "orangecontrib.syned.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("syned = orangecontrib.syned", ),
    'oasys.widgets' : (
        "Syned Light Sources = orangecontrib.syned.widgets.light_sources",
        "Syned Optical Elements = orangecontrib.syned.widgets.beamline_elements",
        "Syned Tools = orangecontrib.syned.widgets.tools",
        "Syned Scanning Loops = orangecontrib.syned.widgets.scanning",
    ),
}

if __name__ == '__main__':
    try:
        import PyMca5, PyQt4

        raise NotImplementedError("This package doesn't work with Oasys1 beta.\nPlease install OASYS1 final release: http://www.elettra.eu/oasys.html")
    except:
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
              namespace_packages=NAMESPACE_PACAKGES,
              include_package_data = True,
              zip_safe = False,
              )
