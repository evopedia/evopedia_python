#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Evopedia uses compressed dumps of Wikipedia for offline use
especially on embedded devices.

The geographical data in the articles is used to display a map of these
articles. This map automagically uses your saved tiles from maep if you
are offline and Openstreetmap tiles if you are online. The images on Wikipedia
are not contained in the dump but if you are connected to the internet, they
are nevertheless shown.
"""

from distutils.core import setup
from glob import glob

def main():
    setup(
        name='evopedia',
        description='Offline Wikipedia Viewer',
        long_description = __doc__,
        version= '0.2.99+0.3rc2-1',
        url='http://www.reitwiessner.de/openmoko/evopedia.html',
        license='GPL V3 or later',
        platforms=['unix', 'linux'],
        author='Christian Reitwießner',
        author_email='christian@reitwiessner.de',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: POSIX',
            'Programming Language :: Python'],
        scripts=['evopedia_starter.py', 'evopedia.sh'],
        packages=['evopedia'],
        data_files=[('share/applications/hildon', ['evopedia.desktop']),
                    ('share/pixmaps', ['wikipedia.png']),
                    ('share/evopedia/static', glob('static/*'))],
    )

if __name__ == '__main__':
    main()

