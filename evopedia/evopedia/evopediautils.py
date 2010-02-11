#!/usr/bin/python
# -*- encoding: utf-8
#
# evopedia, offline Wikipedia reader
# Copyright (C) 2009-2010 Christian Reitwiessner <christian@reitwiessner.de>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, see
# <http://www.gnu.org/licenses/>.

import re
import math

__all__ = ['normalization_table', 'characters', 'normalize',
        'get_coords_in_article']

normalization_table = {
       u"Ḅ": "b", u"Ć": "c", u"Ȍ": "o", u"ẏ": "y", u"Ḕ": "e", u"Ė": "e",
       u"ơ": "o", u"Ḥ": "h", u"Ȭ": "o", u"ắ": "a", u"Ḵ": "k", u"Ķ": "k",
       u"ế": "e", u"Ṅ": "n", u"ņ": "n", u"Ë": "e", u"ỏ": "o", u"Ǒ": "o",
       u"Ṕ": "p", u"Ŗ": "r", u"Û": "u", u"ở": "o", u"ǡ": "a", u"Ṥ": "s",
       u"ë": "e", u"ữ": "u", u"p": "p", u"Ṵ": "u", u"Ŷ": "y", u"û": "u",
       u"ā": "a", u"Ẅ": "w", u"ȇ": "e", u"ḏ": "d", u"ȗ": "u", u"ḟ": "f",
       u"ġ": "g", u"Ấ": "a", u"ȧ": "a", u"ḯ": "i", u"Ẵ": "a", u"ḿ": "m",
       u"À": "a", u"Ễ": "e", u"ṏ": "o", u"ő": "o", u"Ổ": "o", u"ǖ": "u",
       u"ṟ": "r", u"š": "s", u"à": "a", u"Ụ": "u", u"Ǧ": "g", u"k": "k",
       u"ṯ": "t", u"ű": "u", u"Ỵ": "y", u"ṿ": "v", u"Ā": "a", u"Ȃ": "a",
       u"ẅ": "w", u"Ḋ": "d", u"Ȓ": "r", u"Ḛ": "e", u"Ġ": "g", u"ấ": "a",
       u"Ḫ": "h", u"İ": "i", u"Ȳ": "y", u"ẵ": "a", u"Ḻ": "l", u"Á": "a",
       u"ễ": "e", u"Ṋ": "n", u"Ñ": "n", u"Ő": "o", u"ổ": "o", u"Ǜ": "u",
       u"Ṛ": "r", u"á": "a", u"Š": "s", u"ụ": "u", u"f": "f", u"ǫ": "o",
       u"Ṫ": "t", u"ñ": "n", u"Ű": "u", u"ỵ": "y", u"v": "v", u"ǻ": "a",
       u"Ṻ": "u", u"ḅ": "b", u"ċ": "c", u"Ẋ": "x", u"ȍ": "o", u"ḕ": "e",
       u"ě": "e", u"Ơ": "o", u"ḥ": "h", u"ī": "i", u"Ẫ": "a", u"ȭ": "o",
       u"ư": "u", u"ḵ": "k", u"Ļ": "l", u"Ẻ": "e", u"ṅ": "n", u"Ị": "i",
       u"ǐ": "i", u"ṕ": "p", u"Ö": "o", u"ś": "s", u"Ớ": "o", u"a": "a",
       u"Ǡ": "a", u"ṥ": "s", u"ū": "u", u"Ừ": "u", u"q": "q", u"ǰ": "j",
       u"ṵ": "u", u"ö": "o", u"Ż": "z", u"Ȁ": "a", u"ẃ": "w", u"Ă": "a",
       u"Ḉ": "c", u"Ȑ": "r", u"Ē": "e", u"Ḙ": "e", u"ả": "a", u"Ģ": "g",
       u"Ḩ": "h", u"Ȱ": "o", u"ẳ": "a", u"Ḹ": "l", u"ể": "e", u"Ç": "c",
       u"Ṉ": "n", u"Ǎ": "a", u"ồ": "o", u"Ṙ": "r", u"ợ": "o", u"Ţ": "t",
       u"ç": "c", u"Ṩ": "s", u"ǭ": "o", u"l": "l", u"ỳ": "y", u"Ų": "u",
       u"Ṹ": "u", u"ḃ": "b", u"Ẉ": "w", u"ȋ": "i", u"č": "c", u"ḓ": "d",
       u"ẘ": "w", u"ț": "t", u"ĝ": "g", u"ḣ": "h", u"Ẩ": "a", u"ȫ": "o",
       u"ĭ": "i", u"ḳ": "k", u"Ẹ": "e", u"Ľ": "l", u"ṃ": "m", u"Ỉ": "i",
       u"ō": "o", u"Ì": "i", u"ṓ": "o", u"ǒ": "o", u"Ộ": "o", u"ŝ": "s",
       u"Ü": "u", u"ṣ": "s", u"g": "g", u"Ứ": "u", u"ŭ": "u", u"ì": "i",
       u"ṳ": "u", u"w": "w", u"Ỹ": "y", u"Ž": "z", u"ü": "u", u"Ȇ": "e",
       u"ẉ": "w", u"Č": "c", u"Ḏ": "d", u"Ȗ": "u", u"ẙ": "y", u"Ĝ": "g",
       u"Ḟ": "f", u"Ȧ": "a", u"ẩ": "a", u"Ĭ": "i", u"Ḯ": "i", u"ẹ": "e",
       u"ļ": "l", u"Ḿ": "m", u"ỉ": "i", u"Í": "i", u"Ō": "o", u"Ṏ": "o",
       u"Ǘ": "u", u"ộ": "o", u"Ý": "y", u"Ŝ": "s", u"Ṟ": "r", u"b": "b",
       u"ǧ": "g", u"ứ": "u", u"í": "i", u"Ŭ": "u", u"Ṯ": "t", u"r": "r",
       u"ỹ": "y", u"ý": "y", u"ż": "z", u"Ṿ": "v", u"ȁ": "a", u"ć": "c",
       u"ḉ": "c", u"Ẏ": "y", u"ȑ": "r", u"ė": "e", u"ḙ": "e", u"ḩ": "h",
       u"Ắ": "a", u"ȱ": "o", u"ķ": "k", u"ḹ": "l", u"Ế": "e", u"Â": "a",
       u"Ň": "n", u"ṉ": "n", u"Ỏ": "o", u"Ò": "o", u"ŗ": "r", u"ṙ": "r",
       u"ǜ": "u", u"Ở": "o", u"â": "a", u"ṩ": "s", u"m": "m", u"Ǭ": "o",
       u"Ữ": "u", u"ò": "o", u"ŷ": "y", u"ṹ": "u", u"Ȅ": "e", u"ẇ": "w",
       u"Ḍ": "d", u"Ď": "d", u"Ȕ": "u", u"ẗ": "t", u"Ḝ": "e", u"Ğ": "g",
       u"ầ": "a", u"Ḭ": "i", u"Į": "i", u"ặ": "a", u"Ḽ": "l", u"ľ": "l",
       u"Ã": "a", u"ệ": "e", u"Ṍ": "o", u"Ŏ": "o", u"Ó": "o", u"ỗ": "o",
       u"Ǚ": "u", u"Ṝ": "r", u"Ş": "s", u"ã": "a", u"ủ": "u", u"ǩ": "k",
       u"h": "h", u"Ṭ": "t", u"Ů": "u", u"ó": "o", u"ỷ": "y", u"ǹ": "n",
       u"x": "x", u"Ṽ": "v", u"ž": "z", u"ḇ": "b", u"ĉ": "c", u"Ẍ": "x",
       u"ȏ": "o", u"ḗ": "e", u"ę": "e", u"ȟ": "h", u"ḧ": "h", u"ĩ": "i",
       u"Ậ": "a", u"ȯ": "o", u"ḷ": "l", u"Ĺ": "l", u"Ẽ": "e", u"ṇ": "n",
       u"È": "e", u"Ọ": "o", u"ǎ": "a", u"ṗ": "p", u"ř": "r", u"Ờ": "o",
       u"Ǟ": "a", u"c": "c", u"ṧ": "s", u"ũ": "u", u"è": "e", u"Ử": "u",
       u"s": "s", u"ṷ": "u", u"Ź": "z", u"Ḃ": "b", u"Ĉ": "c", u"Ȋ": "i",
       u"ẍ": "x", u"Ḓ": "d", u"Ę": "e", u"Ț": "t", u"쎟": "s", u"Ḣ": "h",
       u"Ĩ": "i", u"Ȫ": "o", u"ậ": "a", u"Ḳ": "k", u"ẽ": "e", u"Ṃ": "m",
       u"É": "e", u"ň": "n", u"ọ": "o", u"Ǔ": "u", u"Ṓ": "o", u"Ù": "u",
       u"Ř": "r", u"ờ": "o", u"Ṣ": "s", u"é": "e", u"Ũ": "u", u"ử": "u",
       u"n": "n", u"Ṳ": "u", u"ù": "u", u"Ÿ": "y", u"ă": "a", u"Ẃ": "w",
       u"ȅ": "e", u"ḍ": "d", u"ē": "e", u"ȕ": "u", u"ḝ": "e", u"ģ": "g",
       u"Ả": "a", u"ḭ": "i", u"Ẳ": "a", u"ḽ": "l", u"Ń": "n", u"Ể": "e",
       u"ṍ": "o", u"Î": "i", u"Ồ": "o", u"ǘ": "u", u"ṝ": "r", u"ţ": "t",
       u"Ợ": "o", u"i": "i", u"Ǩ": "k", u"ṭ": "t", u"î": "i", u"ų": "u",
       u"Ỳ": "y", u"y": "y", u"Ǹ": "n", u"ṽ": "v", u"Ḁ": "a", u"Ȉ": "i",
       u"ẋ": "x", u"Ċ": "c", u"Ḑ": "d", u"Ș": "s", u"Ě": "e", u"Ḡ": "g",
       u"Ȩ": "e", u"ẫ": "a", u"Ī": "i", u"Ḱ": "k", u"ẻ": "e", u"ĺ": "l",
       u"Ṁ": "m", u"ị": "i", u"Ï": "i", u"Ṑ": "o", u"Ǖ": "u", u"ớ": "o",
       u"Ś": "s", u"ß": "s", u"Ṡ": "s", u"d": "d", u"ừ": "u", u"Ū": "u",
       u"ï": "i", u"Ṱ": "t", u"ǵ": "g", u"t": "t", u"ź": "z", u"ÿ": "y",
       u"Ẁ": "w", u"ȃ": "a", u"ą": "a", u"ḋ": "d", u"ȓ": "r", u"ĕ": "e",
       u"ḛ": "e", u"Ạ": "a", u"ĥ": "h", u"ḫ": "h", u"Ằ": "a", u"ȳ": "y",
       u"ĵ": "j", u"ḻ": "l", u"Ề": "e", u"Ņ": "n", u"Ä": "a", u"ṋ": "n",
       u"Ố": "o", u"ŕ": "r", u"Ô": "o", u"ṛ": "r", u"ǚ": "u", u"Ỡ": "o",
       u"ť": "t", u"ä": "a", u"ṫ": "t", u"Ǫ": "o", u"o": "o", u"Ự": "u",
       u"ŵ": "w", u"ô": "o", u"ṻ": "u", u"Ǻ": "a", u"ẁ": "w", u"Ą": "a",
       u"Ḇ": "b", u"Ȏ": "o", u"Ĕ": "e", u"Ḗ": "e", u"Ȟ": "h", u"ạ": "a",
       u"Ĥ": "h", u"Ḧ": "h", u"Ư": "u", u"Ȯ": "o", u"ằ": "a", u"Ĵ": "j",
       u"Ḷ": "l", u"ề": "e", u"Å": "a", u"ń": "n", u"Ṇ": "n", u"Ǐ": "i",
       u"ố": "o", u"Õ": "o", u"Ŕ": "r", u"Ṗ": "p", u"ǟ": "a", u"ỡ": "o",
       u"å": "a", u"Ť": "t", u"Ṧ": "s", u"j": "j", u"ự": "u", u"õ": "o",
       u"Ŵ": "w", u"Ṷ": "u", u"z": "z", u"ḁ": "a", u"Ẇ": "w", u"ȉ": "i",
       u"ď": "d", u"ḑ": "d", u"ẖ": "h", u"ș": "s", u"ğ": "g", u"ḡ": "g",
       u"Ầ": "a", u"ȩ": "e", u"į": "i", u"ḱ": "k", u"Ặ": "a", u"ṁ": "m",
       u"Ệ": "e", u"Ê": "e", u"ŏ": "o", u"ṑ": "o", u"ǔ": "u", u"Ỗ": "o",
       u"Ú": "u", u"ş": "s", u"ṡ": "s", u"e": "e", u"Ủ": "u", u"ê": "e",
       u"ů": "u", u"ṱ": "t", u"u": "u", u"Ǵ": "g", u"Ỷ": "y", u"ú": "u",
       u"0": "0", u"1": "1", u"2": "2", u"3": "3", u"4": "4", u"5": "5",
       u"6": "6", u"7": "7", u"8": "8", u"9": "9"}

characters = "0123456789_abcdefghijklmnopqrstuvwxyz"


def normalize(str):
    global normalization_table
    nt = normalization_table # optimization

    str2 = ''
    for c in unicode(str).lower():
        try:
            str2 += nt[c]
        except KeyError:
            str2 += '_'
    return str2

geo_scale_by_type = {
      'country':    10000000,
      'satellite':  10000000,  
      'state':       3000000,
      'adm1st':      1000000,
      'adm2nd':       300000,
      'default':      300000,
      'adm3rd':       100000,
      'city':         100000,
      'mountain':     100000,
      'isle':         100000,
      'river':        100000,
      'waterbody':    100000,
      'event':         50000,
      'forest':        50000,
      'glacier':       50000,
      'airport':       30000,
      'edu':           10000,
      'pass':          10000,
      'landmark':      10000,
      'railwaystation':10000 }

def parse_coordinates_in_article(text, parse_zoom=True):
    """Search article text for geo link and return parsed coordinates
    together with guessed zoom value.

    For more information see https://wiki.toolserver.org/view/GeoHack"""

    m = re.search('params=(\d*\.?\d*)_(\d*)_?(\d*\.?\d*)_?(N|S)'
                  '_(\d*\.?\d*)_(\d*)_?(\d*\.?\d*)_?(E|W)([^"\']*)', text)
    if not m:
        return (None, None, None)

    lat = 0
    for i in range(1, 4):
        v = m.group(i)
        try:
            v = float(v)
        except ValueError:
            continue
        lat += v * (60.0 ** -(i - 1))
    if m.group(4) == 'S':
        lat = - lat

    lng = 0
    for i in range(5, 8):
        v = m.group(i)
        try:
            v = float(v)
        except ValueError:
            continue
        lng += v * (60.0 ** -(i - 5))
    if m.group(8) == 'W':
        lng = - lng

    if parse_zoom:
        zoom = parse_coordinates_zoom(m.group(9))
    else:
        zoom = None
    return (lat, lng, zoom)

def parse_coordinates_zoom(zoomstr):
    """Guess zoom value in zoomstr as defined in https://wiki.toolserver.org/view/GeoHack"""

    default = 12

    m = re.search('_(scale|dim|type):(\d*)([a-z0-9]*)', zoomstr)
    if not m:
        return default
    else:
        s = m.group(1)
        if s == 'scale':
            try:
                scale = float(m.group(2))
            except ValueError:
                return default
        elif s == 'dim':
            try:
                scale = 10 * float(m.group(2))
            except ValueError:
                return default
        else:
            type = m.group(2) + m.group(3)
            try:
                scale = geo_scale_by_type[type]
            except KeyError:
                return default

        try:
            zoom = round(28.7253 - math.log(scale, 2))
        except OverflowError:
            zoom = default
        return int(max(2, min(18, zoom)))

