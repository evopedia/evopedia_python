#!/usr/bin/python
# coding=utf8

# evopedia, offline Wikipedia reader
# Copyright (C) 2009 Christian Reitwiessner <christian@reitwiessner.de>
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


from __future__ import with_statement
from __future__ import division

import cgi, shutil
from os import path, listdir, walk, readlink
import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urllib import unquote_plus, unquote, quote, pathname2url
from xml.sax import saxutils
import math
from math import floor, ceil
import re
import operator, time, threading
from random import randint, choice
import urllib2


# do not put slashes at the end here!
config = {
    'static_path': '/usr/lib/evopedia/static',
    'article_path': '/usr/lib/evopedia/articles'
}

use_dbus = 0
try:
    import dbus
    use_dbus = 1
except ImportError: pass


endpattern = re.compile('(_[0-9a-f]{4})?(\.html(\.redir)?)?$')


normalization_table = {
       u"Ḅ": u"b", u"Ć": u"c", u"Ȍ": u"o", u"ẏ": u"y", u"Ḕ": u"e", u"Ė": u"e",  
       u"ơ": u"o", u"Ḥ": u"h", u"Ȭ": u"o", u"ắ": u"a", u"Ḵ": u"k", u"Ķ": u"k",  
       u"ế": u"e", u"Ṅ": u"n", u"ņ": u"n", u"Ë": u"e", u"ỏ": u"o", u"Ǒ": u"o",  
       u"Ṕ": u"p", u"Ŗ": u"r", u"Û": u"u", u"ở": u"o", u"ǡ": u"a", u"Ṥ": u"s",  
       u"ë": u"e", u"ữ": u"u", u"p": u"p", u"Ṵ": u"u", u"Ŷ": u"y", u"û": u"u",  
       u"ā": u"a", u"Ẅ": u"w", u"ȇ": u"e", u"ḏ": u"d", u"ȗ": u"u", u"ḟ": u"f",  
       u"ġ": u"g", u"Ấ": u"a", u"ȧ": u"a", u"ḯ": u"i", u"Ẵ": u"a", u"ḿ": u"m",  
       u"À": u"a", u"Ễ": u"e", u"ṏ": u"o", u"ő": u"o", u"Ổ": u"o", u"ǖ": u"u",  
       u"ṟ": u"r", u"š": u"s", u"à": u"a", u"Ụ": u"u", u"Ǧ": u"g", u"k": u"k",  
       u"ṯ": u"t", u"ű": u"u", u"Ỵ": u"y", u"ṿ": u"v", u"Ā": u"a", u"Ȃ": u"a",  
       u"ẅ": u"w", u"Ḋ": u"d", u"Ȓ": u"r", u"Ḛ": u"e", u"Ġ": u"g", u"ấ": u"a",  
       u"Ḫ": u"h", u"İ": u"i", u"Ȳ": u"y", u"ẵ": u"a", u"Ḻ": u"l", u"Á": u"a",  
       u"ễ": u"e", u"Ṋ": u"n", u"Ñ": u"n", u"Ő": u"o", u"ổ": u"o", u"Ǜ": u"u",  
       u"Ṛ": u"r", u"á": u"a", u"Š": u"s", u"ụ": u"u", u"f": u"f", u"ǫ": u"o",  
       u"Ṫ": u"t", u"ñ": u"n", u"Ű": u"u", u"ỵ": u"y", u"v": u"v", u"ǻ": u"a",  
       u"Ṻ": u"u", u"ḅ": u"b", u"ċ": u"c", u"Ẋ": u"x", u"ȍ": u"o", u"ḕ": u"e",  
       u"ě": u"e", u"Ơ": u"o", u"ḥ": u"h", u"ī": u"i", u"Ẫ": u"a", u"ȭ": u"o",  
       u"ư": u"u", u"ḵ": u"k", u"Ļ": u"l", u"Ẻ": u"e", u"ṅ": u"n", u"Ị": u"i",  
       u"ǐ": u"i", u"ṕ": u"p", u"Ö": u"o", u"ś": u"s", u"Ớ": u"o", u"a": u"a",  
       u"Ǡ": u"a", u"ṥ": u"s", u"ū": u"u", u"Ừ": u"u", u"q": u"q", u"ǰ": u"j",  
       u"ṵ": u"u", u"ö": u"o", u"Ż": u"z", u"Ȁ": u"a", u"ẃ": u"w", u"Ă": u"a",  
       u"Ḉ": u"c", u"Ȑ": u"r", u"Ē": u"e", u"Ḙ": u"e", u"ả": u"a", u"Ģ": u"g",  
       u"Ḩ": u"h", u"Ȱ": u"o", u"ẳ": u"a", u"Ḹ": u"l", u"ể": u"e", u"Ç": u"c",  
       u"Ṉ": u"n", u"Ǎ": u"a", u"ồ": u"o", u"Ṙ": u"r", u"ợ": u"o", u"Ţ": u"t",  
       u"ç": u"c", u"Ṩ": u"s", u"ǭ": u"o", u"l": u"l", u"ỳ": u"y", u"Ų": u"u",  
       u"Ṹ": u"u", u"ḃ": u"b", u"Ẉ": u"w", u"ȋ": u"i", u"č": u"c", u"ḓ": u"d",  
       u"ẘ": u"w", u"ț": u"t", u"ĝ": u"g", u"ḣ": u"h", u"Ẩ": u"a", u"ȫ": u"o",  
       u"ĭ": u"i", u"ḳ": u"k", u"Ẹ": u"e", u"Ľ": u"l", u"ṃ": u"m", u"Ỉ": u"i",  
       u"ō": u"o", u"Ì": u"i", u"ṓ": u"o", u"ǒ": u"o", u"Ộ": u"o", u"ŝ": u"s",  
       u"Ü": u"u", u"ṣ": u"s", u"g": u"g", u"Ứ": u"u", u"ŭ": u"u", u"ì": u"i",  
       u"ṳ": u"u", u"w": u"w", u"Ỹ": u"y", u"Ž": u"z", u"ü": u"u", u"Ȇ": u"e",  
       u"ẉ": u"w", u"Č": u"c", u"Ḏ": u"d", u"Ȗ": u"u", u"ẙ": u"y", u"Ĝ": u"g",  
       u"Ḟ": u"f", u"Ȧ": u"a", u"ẩ": u"a", u"Ĭ": u"i", u"Ḯ": u"i", u"ẹ": u"e",  
       u"ļ": u"l", u"Ḿ": u"m", u"ỉ": u"i", u"Í": u"i", u"Ō": u"o", u"Ṏ": u"o",  
       u"Ǘ": u"u", u"ộ": u"o", u"Ý": u"y", u"Ŝ": u"s", u"Ṟ": u"r", u"b": u"b",  
       u"ǧ": u"g", u"ứ": u"u", u"í": u"i", u"Ŭ": u"u", u"Ṯ": u"t", u"r": u"r",  
       u"ỹ": u"y", u"ý": u"y", u"ż": u"z", u"Ṿ": u"v", u"ȁ": u"a", u"ć": u"c",  
       u"ḉ": u"c", u"Ẏ": u"y", u"ȑ": u"r", u"ė": u"e", u"ḙ": u"e", u"ḩ": u"h",  
       u"Ắ": u"a", u"ȱ": u"o", u"ķ": u"k", u"ḹ": u"l", u"Ế": u"e", u"Â": u"a",  
       u"Ň": u"n", u"ṉ": u"n", u"Ỏ": u"o", u"Ò": u"o", u"ŗ": u"r", u"ṙ": u"r",  
       u"ǜ": u"u", u"Ở": u"o", u"â": u"a", u"ṩ": u"s", u"m": u"m", u"Ǭ": u"o",  
       u"Ữ": u"u", u"ò": u"o", u"ŷ": u"y", u"ṹ": u"u", u"Ȅ": u"e", u"ẇ": u"w",  
       u"Ḍ": u"d", u"Ď": u"d", u"Ȕ": u"u", u"ẗ": u"t", u"Ḝ": u"e", u"Ğ": u"g",  
       u"ầ": u"a", u"Ḭ": u"i", u"Į": u"i", u"ặ": u"a", u"Ḽ": u"l", u"ľ": u"l",  
       u"Ã": u"a", u"ệ": u"e", u"Ṍ": u"o", u"Ŏ": u"o", u"Ó": u"o", u"ỗ": u"o",  
       u"Ǚ": u"u", u"Ṝ": u"r", u"Ş": u"s", u"ã": u"a", u"ủ": u"u", u"ǩ": u"k",  
       u"h": u"h", u"Ṭ": u"t", u"Ů": u"u", u"ó": u"o", u"ỷ": u"y", u"ǹ": u"n",  
       u"x": u"x", u"Ṽ": u"v", u"ž": u"z", u"ḇ": u"b", u"ĉ": u"c", u"Ẍ": u"x",  
       u"ȏ": u"o", u"ḗ": u"e", u"ę": u"e", u"ȟ": u"h", u"ḧ": u"h", u"ĩ": u"i",  
       u"Ậ": u"a", u"ȯ": u"o", u"ḷ": u"l", u"Ĺ": u"l", u"Ẽ": u"e", u"ṇ": u"n",  
       u"È": u"e", u"Ọ": u"o", u"ǎ": u"a", u"ṗ": u"p", u"ř": u"r", u"Ờ": u"o",  
       u"Ǟ": u"a", u"c": u"c", u"ṧ": u"s", u"ũ": u"u", u"è": u"e", u"Ử": u"u",  
       u"s": u"s", u"ṷ": u"u", u"Ź": u"z", u"Ḃ": u"b", u"Ĉ": u"c", u"Ȋ": u"i",  
       u"ẍ": u"x", u"Ḓ": u"d", u"Ę": u"e", u"Ț": u"t", u"쎟": u"s", u"Ḣ": u"h",  
       u"Ĩ": u"i", u"Ȫ": u"o", u"ậ": u"a", u"Ḳ": u"k", u"ẽ": u"e", u"Ṃ": u"m",  
       u"É": u"e", u"ň": u"n", u"ọ": u"o", u"Ǔ": u"u", u"Ṓ": u"o", u"Ù": u"u",  
       u"Ř": u"r", u"ờ": u"o", u"Ṣ": u"s", u"é": u"e", u"Ũ": u"u", u"ử": u"u",  
       u"n": u"n", u"Ṳ": u"u", u"ù": u"u", u"Ÿ": u"y", u"ă": u"a", u"Ẃ": u"w",  
       u"ȅ": u"e", u"ḍ": u"d", u"ē": u"e", u"ȕ": u"u", u"ḝ": u"e", u"ģ": u"g",  
       u"Ả": u"a", u"ḭ": u"i", u"Ẳ": u"a", u"ḽ": u"l", u"Ń": u"n", u"Ể": u"e",  
       u"ṍ": u"o", u"Î": u"i", u"Ồ": u"o", u"ǘ": u"u", u"ṝ": u"r", u"ţ": u"t",  
       u"Ợ": u"o", u"i": u"i", u"Ǩ": u"k", u"ṭ": u"t", u"î": u"i", u"ų": u"u",  
       u"Ỳ": u"y", u"y": u"y", u"Ǹ": u"n", u"ṽ": u"v", u"Ḁ": u"a", u"Ȉ": u"i",  
       u"ẋ": u"x", u"Ċ": u"c", u"Ḑ": u"d", u"Ș": u"s", u"Ě": u"e", u"Ḡ": u"g",  
       u"Ȩ": u"e", u"ẫ": u"a", u"Ī": u"i", u"Ḱ": u"k", u"ẻ": u"e", u"ĺ": u"l",  
       u"Ṁ": u"m", u"ị": u"i", u"Ï": u"i", u"Ṑ": u"o", u"Ǖ": u"u", u"ớ": u"o",  
       u"Ś": u"s", u"ß": u"s", u"Ṡ": u"s", u"d": u"d", u"ừ": u"u", u"Ū": u"u",  
       u"ï": u"i", u"Ṱ": u"t", u"ǵ": u"g", u"t": u"t", u"ź": u"z", u"ÿ": u"y",  
       u"Ẁ": u"w", u"ȃ": u"a", u"ą": u"a", u"ḋ": u"d", u"ȓ": u"r", u"ĕ": u"e",  
       u"ḛ": u"e", u"Ạ": u"a", u"ĥ": u"h", u"ḫ": u"h", u"Ằ": u"a", u"ȳ": u"y",  
       u"ĵ": u"j", u"ḻ": u"l", u"Ề": u"e", u"Ņ": u"n", u"Ä": u"a", u"ṋ": u"n",  
       u"Ố": u"o", u"ŕ": u"r", u"Ô": u"o", u"ṛ": u"r", u"ǚ": u"u", u"Ỡ": u"o",  
       u"ť": u"t", u"ä": u"a", u"ṫ": u"t", u"Ǫ": u"o", u"o": u"o", u"Ự": u"u",  
       u"ŵ": u"w", u"ô": u"o", u"ṻ": u"u", u"Ǻ": u"a", u"ẁ": u"w", u"Ą": u"a",  
       u"Ḇ": u"b", u"Ȏ": u"o", u"Ĕ": u"e", u"Ḗ": u"e", u"Ȟ": u"h", u"ạ": u"a",  
       u"Ĥ": u"h", u"Ḧ": u"h", u"Ư": u"u", u"Ȯ": u"o", u"ằ": u"a", u"Ĵ": u"j",  
       u"Ḷ": u"l", u"ề": u"e", u"Å": u"a", u"ń": u"n", u"Ṇ": u"n", u"Ǐ": u"i",  
       u"ố": u"o", u"Õ": u"o", u"Ŕ": u"r", u"Ṗ": u"p", u"ǟ": u"a", u"ỡ": u"o",  
       u"å": u"a", u"Ť": u"t", u"Ṧ": u"s", u"j": u"j", u"ự": u"u", u"õ": u"o",  
       u"Ŵ": u"w", u"Ṷ": u"u", u"z": u"z", u"ḁ": u"a", u"Ẇ": u"w", u"ȉ": u"i", 
       u"ď": u"d", u"ḑ": u"d", u"ẖ": u"h", u"ș": u"s", u"ğ": u"g", u"ḡ": u"g",  
       u"Ầ": u"a", u"ȩ": u"e", u"į": u"i", u"ḱ": u"k", u"Ặ": u"a", u"ṁ": u"m",  
       u"Ệ": u"e", u"Ê": u"e", u"ŏ": u"o", u"ṑ": u"o", u"ǔ": u"u", u"Ỗ": u"o",  
       u"Ú": u"u", u"ş": u"s", u"ṡ": u"s", u"e": u"e", u"Ủ": u"u", u"ê": u"e",  
       u"ů": u"u", u"ṱ": u"t", u"u": u"u", u"Ǵ": u"g", u"Ỷ": u"y", u"ú": u"u",
       u"0": u"0", u"1": u"1", u"2": u"2", u"3": u"3", u"4": u"4", u"5": u"5",
       u"6": u"6", u"7": u"7", u"8": u"8", u"9": u"9"}



class EvopediaHandler(BaseHTTPRequestHandler):
    TILESIZE = 256
    map_width = 400
    map_height = 380

    def output_wiki_page(self, parts):
        global config
        if '.' in parts or '..' in parts: return

        f = path.join(config['article_path'], '/'.join(parts).encode('utf-8'))
        #if path.islink(f):
        #    l = os.readlink(f)
        #elif path.isfile(f):
        if path.isfile(f):
            self.write_header(use_cache = 1)
            with open(path.join(config['static_path'], 'header.html')) as head:
                shutil.copyfileobj(head, self.wfile)
            with open(f) as article:
                text = article.read()
                (lat, lon) = self.get_coords_in_article(text)
                if lat is not None and lon is not None:
                    self.wfile.write('<a class="evopedianav" href="/map/?lat=%f&lon=%f&zoom=13"><img src="/static/maparticle.png"></a>' % (lat, lon))
                self.wfile.write('</div>')
                self.wfile.write(text)
            with open(path.join(config['static_path'], 'footer.html')) as foot:
                shutil.copyfileobj(foot, self.wfile)
        else:
            self.output_error_page()

    def output_error_page(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(path.join(config['static_path'], 'header.html')) as head:
            shutil.copyfileobj(head, self.wfile)
        self.wfile.write("</div>ERROR - Page not found")
        with open(path.join(config['static_path'], 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)
        
    def output_error_msg_page(self, msg):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(path.join(config['static_path'], 'header.html')) as head:
            shutil.copyfileobj(head, self.wfile)
        self.wfile.write((u"</div>ERROR: %s" % msg).encode('utf-8'))
        with open(path.join(config['static_path'], 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)
        
    def normalize(self, str):
        global normalization_table
        nt = normalization_table # optimization

        str2 = u''
        for c in unicode(str).lower():
            try: str2 += nt[c]
            except: str2 += '_'
        return str2

    def normalized_startswith(self, str, start):
        global normalization_table
        nt = normalization_table # optimization

        str = unicode(str).lower()
        if len(str) < len(start): return False
        str = str[:len(start)]

        for i in range(len(str)):
            c = str[i]
            try:
                if nt[c] != start[i]: return False
            except:
                if '_' != start[i]: return False
        return True

    def output_search_result(self, query, limit):
        self.write_header('text/xml')
        self.wfile.write("<?xml version='1.0' encoding='UTF-8' ?>\n")

        try:
            self.wfile.write(self.get_search_result_text(query, limit).encode('utf-8'))
        except Exception, e:
            self.wfile.write(('<error>%s</error>' % saxutils.escape(repr(e))).encode('utf-8'))
            #print(repr(e))

    def get_article_name_from_filename(self, filename):
        return endpattern.sub('', filename).replace('_', ' ')

    def get_search_result_text(self, query, limit):
        global config, search_depth
        # some optimizations
        articlepath = config['article_path']

        query = self.normalize(query)

        text = '';

        exceptions = set(['evopedia_version', 'creation_date'])

        results = 0
        path = (u'/' + u'/'.join(query[:search_depth])).encode('utf-8')
        try:
            for root, dirs, files in walk(articlepath + path):
                r = root[len(articlepath):]
                dirs.sort()
                unicodefiles = [f.decode('utf-8') for f in files]
                for f in sorted(unicodefiles):
                    if self.normalized_startswith(f, query):
                        if f in exceptions: continue
                        url = u'/articles%s/%s' % (r, f)

                        if results >= limit:
                            return '<list complete="0">' + text + '</list>'
                        else:
                            article_name = self.get_article_name_from_filename(f)
                            text += ('<article name="%s" url="%s" />' %
                                    (saxutils.escape(article_name), saxutils.escape(url)))
                            results += 1
        except OSError: pass

        return '<list complete="1">' + text + '</list>'

    def get_coords_in_article(self, text):
        lat = lng = None

        m = re.search('params=(\d*)_(\d*)_([0-9.]*)_(N|S)_(\d*)_(\d*)_([0-9.]*)_(E|W)', text)
        if m:
            (lat, lng) = self.parse_coordinates_dms(m)
        else:
            m = re.search('params=(\d*\.\d*)_(N|S)_(\d*\.\d*)_(E|W)', text)
            if m:
                (lat, lng) = self.parse_coordinates_dec(m)
        return (lat, lng)

    def splice_coords(self, coords):
        (head, rest) = ('%012.7f' % coords).split('.')
        head1 = head[:-1]
        head2 = head[-1]
        return [head[:-1], head[-1]] + list(rest[:1])

    def parse_coordinates_dec(self, match):
        try:
            lat = float(match.group(1))
            if match.group(2) == 'S':
                lat = -lat
            lon = float(match.group(3))
            if match.group(4) == 'W':
                lon = -lon
            return (lat, lon)
        except ValueError:
            return (None, None)

    def parse_coordinates_dms(self, match):
        try:
            groups = [match.group(i) for i in (1, 2, 3, 5, 6, 7)]
            for i in range(len(groups)):
                try:
                    groups[i] = float(groups[i])
                except:
                    groups[i] = 0
            lat = groups[0] + groups[1] / 60 + groups[2] / 3600
            if match.group(4) == 'S':
                lat = -lat
            lon = groups[3] + groups[4] / 60 + groups[5] / 3600
            if match.group(8) == 'W':
                lon = -lon
            return (lat, lon)
        except ValueError:
            return (None, None)

    def output_map(self, coords, zoom):
        TILESIZE = self.TILESIZE

        self.write_header()

        with open(path.join(config['static_path'], 'mapheader.html')) as head:
            shutil.copyfileobj(head, self.wfile)

        global tangogps_tilerepos
        
        (tx, ty) = self.coords2pixel(zoom, coords)

        # XXX "repr" below could behave a bit different than expected but we'll see.
        text = (u'<script type="text/javascript">' +
                u'var map = new MapHandler(%d, %d, %d, %s);</script>' %
                (zoom, tx, ty, repr([x.title for x in tangogps_tilerepos])))

        self.wfile.write(text.encode('utf-8'))

        with open(path.join(config['static_path'], 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)

    def output_geo_articles(self, zoom, minx, miny, maxx, maxy):
        self.write_header('text/xml')
        self.wfile.write("<?xml version='1.0' encoding='UTF-8' ?>\n")

        mincoords = self.pixel2coords(zoom, (minx, maxy))
        maxcoords = self.pixel2coords(zoom, (maxx, miny))

        try:
            self.wfile.write(u'<articles>'.encode('utf-8'));

            articlecount = 0
            for (name, lat, lon, url) in self.articles_in_coords(mincoords, maxcoords):
                (x, y) = self.coords2pixel(zoom, (lat, lon))
                self.wfile.write((u'<article name="%s" x="%d" y="%d" href="%s"/>' % (
                        saxutils.escape(name), x, y, quote(url))).encode('utf-8'))

                articlecount += 1
                if articlecount > 100:
                    self.wfile.write((u'<error>Zoom in for more articles.</error>').encode('utf-8'))
                    break

            self.wfile.write((u'</articles>').encode('utf-8'))
        except IOError:
            print("geo request cancelled by browser")

    def coords2pixel(self, zoom, coords):
        TILESIZE = self.TILESIZE

        (lat, lon) = coords

        lon = lon / 360 + 0.5
        lat = math.atanh(math.sin(lat / 180 * math.pi))
        lat = -lat / (2 * math.pi) + 0.5

        scale = 2 ** zoom * TILESIZE

        return (int(lon * scale), int(lat * scale))

    def pixel2coords(self, zoom, pixel):
        TILESIZE = self.TILESIZE

        (x, y) = pixel

        scale = 2 ** zoom * TILESIZE

        lon = (x / scale - 0.5) * 360
        lat = -(y / scale - 0.5) * 2 * math.pi
        lat = math.asin(math.tanh(lat)) * 180 / math.pi

        return (lat, lon)

    def coordpath_in_limits(self, path, mincoords, maxcoords):
        lon = int(path[0]) * 10 + int(path[2])
        lat = int(path[1]) * 10 + int(path[3])

    # this is a generator
    def articles_in_coords(self, mincoords, maxcoords):
        # TODO speed optimizations: replace global variables by local variables

        coordpath = config['article_path'] + '/coords/'
        for (dirpath, dirnames, filenames) in walk(coordpath):
            if len(dirnames) > 0:
                relpath = dirpath[len(coordpath):]
                if relpath == '':
                    pathparts = []
                else:
                    pathparts = relpath.split('/')
                depth = len(pathparts)
                parity = depth % 2
                # parity == 0: latitude else longitude
                if depth >= 2 and pathparts[parity][0] == '-':
                    sign = -1
                else:
                    sign = 1

                coord = sum([sign * abs(int(pathparts[i])) * 10 ** (1 - i // 2) for i in range(parity, len(pathparts), 2)])
                size = 10 ** (1 - depth // 2)

                minc = mincoords[parity]
                maxc = maxcoords[parity]

                #print (pathparts, coord, sign)

                for d in dirnames[:]:
                    if d[0] == '-':
                        signhere = -1
                    else:
                        signhere = sign

                    (a, b) = sorted([coord + signhere * abs(int(d)) * size,
                                        coord + signhere * (abs(int(d)) + 1) * size])
                    # remove if interval [a, b] does not intersect [minc, maxc]
                    if not (minc <= a <= maxc or minc <= b <= maxc or a <= minc <= b):
                        dirnames.remove(d)

            for f in filenames:
                fj = path.join(dirpath, f)
                if path.islink(fj):
                    dest = readlink(fj)
                    (lat, lon, fname) = f.split(',', 2)
                    fname = fname.decode('utf-8')
                    lat = float(lat)
                    lon = float(lon)
                    if mincoords[0] <= lat <= maxcoords[0] and mincoords[1] <= lon <= maxcoords[1]:
                        yield (self.get_article_name_from_filename(fname), lat, lon, dest)



    def write_header(self, content_type = 'text/html', use_cache = 0):
        self.send_response(200)
        if use_cache:
            # XXX test if caching is really relevant (browser does not use it)
            # XXX Use real time (could be time-consuming)
            #self.send_header('Last-Modified', 'Thu, 01 Jan 1970 00:00:00 GMT')
            pass
        self.send_header('Content-type', content_type + '; charset=UTF-8')
        self.end_headers()

    def decode(self, s):
        try:
            s = s.decode('utf-8')
        except:
            try:
                s = s.decode('latin-1')
            except: pass
        return s

    def do_GET(self):
        global config

        dict = None
        i = self.path.rfind('?')
        if i >= 0:
            self.path, query = self.path[:i], self.path[i+1:]
            if query:
                dict = cgi.parse_qs(query)
        
        parts = [ self.decode(unquote(i)) for i in self.path.split('/') if i ]


        if len(parts) == 0:
            # XXX Compare file dates (could be time-consuming), use
            # headers.getdate('If...')
            if self.headers.get('If-Modified-Since') is not None:
                self.send_response(304)
                self.end_headers()
                return
            self.write_header(use_cache = 1)
            with open(path.join(config['static_path'], 'search.html')) as search:
                shutil.copyfileobj(search, self.wfile)
            return
        elif parts[0] == 'static':
            # XXX Compare file dates (could be time-consuming)
            if self.headers.get('If-Modified-Since') is not None:
                self.send_response(304)
                self.end_headers()
                return
            if len(parts) == 2 and parts[1] in set(['search.js', 'main.css',
                    'search.html', 'mapclient.js', 'map.js', 'zoomin.png',
                    'zoomout.png', 'search.png', 'wikipedia.png', 'close.png',
                    'random.png', 'map.png', 'maparticle.png', 'home.png',
                    'crosshairs.png']):
                if parts[1].endswith('.png'):
                    self.write_header('image/png', use_cache = 1)
                elif parts[1].endswith('.css'):
                    self.write_header('text/css', use_cache = 1)
                elif parts[1].endswith('.js'):
                    self.write_header('application/javascript', use_cache = 1)
                else:
                    self.write_header(use_cache = 1)
                with open(path.join(config['static_path'], parts[1])) as fobj:
                    shutil.copyfileobj(fobj, self.wfile)
                return
        elif parts[0] == 'search':
            try: query = self.decode(dict['q'][0])
            except: query = ''
            self.output_search_result(query, 50)
            return
        elif parts[0] == 'map':
            try: coords = (float(dict['lat'][0]), float(dict['lon'][0]))
            except: coords = (50, 10)

            try: zoom = int(dict['zoom'][0])
            except: zoom = 3

            self.output_map(coords, zoom)
            return
        elif parts[0] == 'maptile':
            # XXX Compare file dates (could be time-consuming)
            if self.headers.get('If-Modified-Since') is not None:
                print("cache hit")
                self.send_response(304)
                self.end_headers()
                return
            try:
                (repoindex, z, x, y) = parts[1:5]
                y = y.split('.')[0]
                global tangogps_tilerepos
                tangogps_tilerepos[int(repoindex)].output_map_tile(self, int(x), int(y), int(z))
            except Exception, e:
                self.output_error_msg_page('Invalid URL')
                import traceback
                traceback.print_exc()
            return
        elif parts[0] == 'geo':
            try:
                minx = int(dict['minx'][0])
                miny = int(dict['miny'][0])
                maxx = int(dict['maxx'][0])
                maxy = int(dict['maxy'][0])
                zoom = int(dict['zoom'][0])
            except:
                self.output_error_msg_page('Invalid URL')
                return
            self.output_geo_articles(zoom, minx, miny, maxx, maxy)
            return
        elif parts[0] == 'gpspos':
            try:
                zoom = int(dict['zoom'][0])
            except:
                self.output_error_msg_page('Invalid URL')
                return

            global gps_handler

            pos = gps_handler.get_gps_pos()
            self.write_header('text/xml')
            self.wfile.write("<?xml version='1.0' encoding='UTF-8' ?>\n")
            if pos is False:
                self.wfile.write('<error>No GPS Fix</error>')
                return

            (coordx, coordy) = self.coords2pixel(zoom, pos)

            self.wfile.write('<position x="%d" y="%d" zoom="%d"/>' % (coordx, coordy, zoom))

            return
        elif parts[0] == 'random':
            url = '/articles'

            for root, dirs, files in walk(config['article_path']):
                try: dirs.remove('coords')
                except ValueError: pass
                if len(dirs) > 0:
                    i = randint(0, len(dirs) - 1)
                    del dirs[i+1:]
                    del dirs[:i-1]
                    url += '/' + dirs[0]
                else:
                    url += '/' + choice(files)
                    self.send_response(302)
                    self.send_header('Location', pathname2url(url))
                    self.end_headers()
                    return
            self.output_error_msg_page("Error finding random page...")
            return
        elif parts[0] == 'articles':
            # XXX Compare file dates (could be time-consuming)
            if 'If-Modified-Since' in self.headers:
                self.send_response(304)
                self.end_headers()
                return
            self.output_wiki_page(parts[1:])
            return

        self.output_error_page()

class GPSHandler:
    def __init__(self):
        self.dbus = None
        self.ousaged = None
        self.gypsy = None
        self.gps_release_timer = None

        self.gps_activated = False
        self.last_gps_usage = 0

        self.thread = threading.Thread(target = self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while 1:
            try:
                if self.gps_activated and self.last_gps_usage < time.time() - 5 * 60:
                    self.release_gps()
                time.sleep(60)
            except Exception as e:
                print e


    def init_dbus(self):
        global use_dbus
        if not use_dbus: return False

        try:
            if self.dbus is None:
                self.dbus = dbus.SystemBus()
            gypsy_object = self.dbus.get_object("org.freedesktop.Gypsy", "/org/freedesktop/Gypsy")
            self.gypsy = dbus.Interface(gypsy_object, "org.freedesktop.Gypsy.Position")
            ousaged_object = self.dbus.get_object("org.freesmartphone.ousaged", "/org/freesmartphone/Usage")
            self.ousaged = dbus.Interface(ousaged_object, "org.freesmartphone.Usage")
        except dbus.exceptions.DBusException as e:
            print e
            if self.gypsy is None:
                return False
            return True

    def request_gps(self):
        self.last_gps_usage = time.time()
        if self.gps_activated: return
        try:
            self.ousaged.RequestResource("GPS")
            self.gps_activated = True
        except Exception as e:
            print e

    def update_gps_release_timer(self):
# XXX don't use timer but interval that checks the last usage timestamp
        if self.gps_release_timer is not None:
            self.gps_release_timer.cancel()
        self.gps_release_timer = threading.Timer(5 * 60, self.release_gps)
        self.gps_release_timer.start()
    
    def get_gps_pos(self):
        if self.gypsy is None:
            if not self.init_dbus():
                return False

        self.request_gps()

        (valid, tstamp, lat, lng, alt) = self.gypsy.GetPosition()

        if lat != 0 and lng != 0:
            return (lat, lng)
        else:
            return False

    def release_gps(self):
        self.gps_activated = False
        if self.ousaged is None: return

        print("Releasing GPS...")
        self.ousaged.ReleaseResource("GPS")

class TileRepo:
    def __init__(self, title, tileurl, tilepath, zoom_last = False):
        self.title = title
        self.tileurl = saxutils.unescape(tileurl)
        self.tilepath = tilepath
        self.zoom_last = zoom_last

        if tilepath is not None and not path.isdir(tilepath):
            self.tilepath = None

    def __str__(self):
        return u'Tile Repository "%s" (%s, %s)' % (self.title, self.tilepath, self.tileurl)

    def output_map_tile(self, request_handler, x, y, zoom):
        if self.tilepath is not None:
            if self.get_local_tile(request_handler, x, y, zoom):
                return

        self.redirect_to_remote_tile(request_handler, x, y, zoom)
        #self.send_remote_tile(request_handler, x, y, zoom)


    def get_local_tile(self, request_handler, x, y, zoom):
        tiledir = '/%d/%d/%d.png' % (zoom, x, y)
        try:
            with file(self.tilepath + tiledir) as f:
                image = f.read()
        except IOError:
            return False
        # some special remote tile handlers copied from the tangogps source
        if self.tileurl in ('maps-for-free', 'openaerial'):
            request_handler.write_header(content_type = 'image/jpeg', use_cache = 1)
        else:
            request_handler.write_header(content_type = 'image/png', use_cache = 1)
        request_handler.wfile.write(image)
        return True

    def get_remote_tile_url(self, x, y, zoom):
        # some special remote tile handlers copied from the tangogps source
        if self.tileurl == 'maps-for-free':
            return ('http://maps-for-free.com/layer/relief/z%d/row%d/%d_%d-%d.jpg' %
                    (zoom, y, zoom, x, y))
        elif self.tileurl == 'openaerial':
            return ('http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/%d/%d/%d.jpg' %
                    (zoom, x, y))
        else:
            if self.zoom_last:
                return self.tileurl % (x, y, zoom)
            else:
                return self.tileurl % (zoom, x, y)


    def redirect_to_remote_tile(self, request_handler, x, y, zoom):
        request_handler.send_response(301)
        request_handler.send_header('Location', self.get_remote_tile_url(x, y, zoom))
        request_handler.end_headers()

    def send_remote_tile(self, request_handler, x, y, zoom):
        url = self.get_remote_tile_url(x, y, zoom)
        print("Fetchind %s..." % url)
        f = urllib2.urlopen(url)
        # XXX use write_header
        request_handler.send_response(200)
        request_handler.send_header('Content-type', f.info().get('Content-type'))
        # XXX Use real time (could be time-consuming)
        request_handler.send_header('Last-Modified', 'Thu, 01 Jan 1970 00:00:00 GMT')
        request_handler.end_headers()
        shutil.copyfileobj(f, request_handler.wfile)


    @staticmethod
    def parse_tilerepos(repostring):
        if repostring.startswith('['):
            repostring = repostring[1:-1].split(',')
        else:
            repostring = repostring.split('\n')

        repos = []
        try:
            for repo in repostring:
                (title, url, path, zoom_last) = repo.strip().split('|')
                repos += [TileRepo(title, url, path, zoom_last != '0')]
        except:
            if len(repos) == 0:
                repos = [TileRepo('OSM', 'http://tile.openstreetmap.org/%d/%d/%d.png', None, False)]
        return repos

class ThreadingHTTPServer(SocketServer.ThreadingMixIn, HTTPServer):
    daemon_threads = True


# XXX The caching used here for articles and map tiles assumes that content
# never changes. You have to empty the browser's cache to get a new version from
# disk.

def main():
    import sys

    port = 8080
    if len(sys.argv) >= 2:
        port = int(sys.argv[1])
    if len(sys.argv) >= 3:
        repostring = sys.argv[2]
    else:
        repostring = ''

    global tangogps_tilerepos
    tangogps_tilerepos = TileRepo.parse_tilerepos(repostring)
    print "Using map tile repositories " + str([x.title for x in tangogps_tilerepos])

    global gps_handler
    gps_handler = GPSHandler()

    global search_depth
    search_depth = 4
    try:
        with open(path.join(config['article_path'], 'evopedia_version')) as versionfile:
            m = re.search('depth ([0-9]*)', versionfile.readline())
            search_depth = int(m.group(1))
    except: pass
    print "Using search depth %i." % search_depth

    try:
        server = ThreadingHTTPServer(('', port), EvopediaHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

