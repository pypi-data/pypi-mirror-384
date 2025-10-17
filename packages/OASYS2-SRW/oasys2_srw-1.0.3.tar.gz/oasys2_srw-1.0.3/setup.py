#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS2-SRW'
VERSION = '1.0.3'
ISRELEASED = True

DESCRIPTION = 'SRW in OASYS2'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Luca Rebuffi'
AUTHOR_EMAIL = 'lrebuffi@anl.gov'
URL = 'https://github.com/lucarebuffi/OASYS-SRW'
DOWNLOAD_URL = 'https://github.com/lucarebuffi/OASYS-SRW'
LICENSE = 'GPLv3'

KEYWORDS = [
    'waveoptics',
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
    'oasys2>=0.0.2',
    'syned-gui-2>=1.0.0',
    'wofrysrw>=1.1.34',
    'xoppylib>=1.0.43',
    'srwpy==4.1.1',
    'scikit-image'
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.srw.widgets.light_sources":["icons/*.png", "icons/*.jpg", "misc/*.png"],
    "orangecontrib.srw.widgets.optical_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.tools":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.native":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.loops": ["icons/*.png", "icons/*.jpg"],
}

ENTRY_POINTS = {
    'oasys2.addons' : ("SRW = orangecontrib.srw", ),
    'oasys2.widgets' : (
        "SRW Light Sources = orangecontrib.srw.widgets.light_sources",
        "SRW Optical Elements = orangecontrib.srw.widgets.optical_elements",
        "SRW Tools = orangecontrib.srw.widgets.tools",
        "SRW Loops = orangecontrib.srw.widgets.loops",
        "SRW Native = orangecontrib.srw.widgets.native",
    ),
    'oasys2.menus' : ("srwmenu = orangecontrib.srw.menu",)
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
