#!/usr/bin/python
# coding=utf8

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


from __future__ import with_statement
from __future__ import division

import sys
import cgi
import shutil
import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urllib import unquote_plus, unquote, quote, pathname2url
from xml.sax import saxutils
import math
from math import floor, ceil
import re
import operator
import time
import threading
from random import randint, choice
import urllib2
import os
import ConfigParser

import evopediautils

__all__ = ['EvopediaHandler', 'GPSHandler', 'GPSHandlerGypsy',
        'GPSHandlerLiblocation', 'TileRepo', 'start_server']

static_path = os.path.join(sys.prefix, 'share/evopedia/static/')
configfile = '~/.evopediarc'
config = None
storage = None
storage_class = None
tile_repository = None
gps_handler = None

EVOPEDIA_VERSION = 'Evopedia 0.3.0 RC 3'

try:
    math.atanh(0)
except AttributeError:
    math.atanh = lambda x: .5 * (math.log(1 + x) - math.log(1 - x))


class EvopediaHandler(BaseHTTPRequestHandler):
    TILESIZE = 256
    map_width = 400
    map_height = 380

    def output_wiki_page(self, url):
        global storage
        global static_path

        text = storage.get_article_by_name(url)
        if text is None:
            self.output_error_page()
        else:
            self.write_header(expires=True)
            with open(os.path.join(static_path, 'header.html')) as head:
                shutil.copyfileobj(head, self.wfile)
            (lat, lon, zoom) = evopediautils.parse_coordinates_in_article(text)
            if lat is not None and lon is not None:
                self.wfile.write(('<a class="evopedianav" ' +
                        'href="/map/?lat=%f&lon=%f&zoom=%d">' +
                        '<img src="/static/maparticle.png"></a>') %
                                 (lat, lon, zoom))
            self.wfile.write(('<a class="evopedianav" href="%s">' +
                    '<img src="/static/wikipedia.png"></a>') %
                    storage.get_orig_url(url))
            self.wfile.write('</div>')
            self.wfile.write(text)
            with open(os.path.join(static_path, 'footer.html')) as foot:
                shutil.copyfileobj(foot, self.wfile)

    def output_error_page(self):
        global static_path

        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(os.path.join(static_path, 'header.html')) as head:
            shutil.copyfileobj(head, self.wfile)
        self.wfile.write("</div>ERROR - Page not found")
        with open(os.path.join(static_path, 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)

    def output_error_msg_page(self, msg):
        global static_path
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(os.path.join(static_path, 'header.html')) as head:
            shutil.copyfileobj(head, self.wfile)
        self.wfile.write((u"</div>ERROR: %s" % msg).encode('utf-8'))
        with open(os.path.join(static_path, 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)

    def output_search_result(self, query, limit):
        self.write_header('text/xml')
        self.wfile.write("<?xml version='1.0' encoding='UTF-8' ?>\n")
        try:
            self.wfile.write(self.get_search_result_text(query, limit)
                             .encode('utf-8'))
        except Exception, e:
            self.wfile.write(('<error>%s</error>' %
                              saxutils.escape(repr(e))).encode('utf-8'))

    def get_search_result_text(self, query, limit):
        global storage

        text = ''
        titles = storage.get_titles_with_prefix(query)
        for (i, title) in enumerate(titles):
            if i >= limit:
                return '<list complete="0">' + text + '</list>'
            else:
                title = saxutils.escape(title[0])
                name = title.replace('_', ' ')
                text += '<article name="%s" url="/wiki/%s" />' % (name, title)
        return '<list complete="1">' + text + '</list>'

    def output_map(self, coords, zoom):
        global static_path
        TILESIZE = self.TILESIZE

        self.write_header()

        with open(os.path.join(static_path, 'mapheader.html')) as head:
            shutil.copyfileobj(head, self.wfile)

        global tile_repository

        (tx, ty) = self.coords2pixel(zoom, coords)

        # XXX "repr" below could behave a bit different than expected
        #     but we'll see.
        text = (u'<script type="text/javascript">' +
                u'var map = new MapHandler(%d, %f, %f, %s);</script>' %
                (zoom, tx, ty, repr([x.title for x in tile_repository])))

        self.wfile.write(text.encode('utf-8'))

        with open(os.path.join(static_path, 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)

    def output_geo_articles(self, zoom, minx, miny, maxx, maxy):
        global storage

        self.write_header('text/xml')
        self.wfile.write("<?xml version='1.0' encoding='UTF-8' ?>\n")

        mincoords = self.pixel2coords(zoom, (minx, maxy))
        maxcoords = self.pixel2coords(zoom, (maxx, miny))

        self.wfile.write('<articles>')

        articlecount = 0
        for (name, lat, lon) in storage.titles_in_coords(mincoords,
                                                             maxcoords):
            (x, y) = self.coords2pixel(zoom, (lat, lon))
            text = '<article name="%s" x="%f" y="%f" href="%s"/>' % \
                    (saxutils.escape(name.replace('_', ' ').encode('utf-8')),
                    x, y, pathname2url('/wiki/' + name.encode('utf-8')))
            self.wfile.write(text)
            articlecount += 1
            if articlecount >= 15:
                self.wfile.write('<error>Zoom in for more articles.' +
                                  '</error>')
                break

        self.wfile.write('</articles>')

    def coords2pixel(self, zoom, coords):
        TILESIZE = self.TILESIZE
        (lat, lon) = coords
        lon = lon / 360 + 0.5
        lat = math.atanh(math.sin(lat / 180 * math.pi))
        lat = - lat / (2 * math.pi) + 0.5
        scale = 2 ** zoom * TILESIZE
        return (lon * scale, lat * scale)

    def pixel2coords(self, zoom, pixel):
        TILESIZE = self.TILESIZE
        (x, y) = pixel
        scale = 2 ** zoom * TILESIZE
        lon = (x / scale - 0.5) * 360
        lat = - (y / scale - 0.5) * 2 * math.pi
        lat = math.asin(math.tanh(lat)) * 180 / math.pi
        return (lat, lon)

    def coordpath_in_limits(self, path, mincoords, maxcoords):
        lon = int(path[0]) * 10 + int(path[2])
        lat = int(path[1]) * 10 + int(path[3])

    def output_data_selector(self, parts, dict):
        self.write_header()

        global storage
        global storage_class
        global static_path

        path = storage.get_datadir()
        if not os.path.isdir(path):
            path = os.path.expanduser("~/")
        try:
            path = self.decode(dict['path'][0])
        except (UnicodeDecodeError, TypeError, KeyError):
            pass
        path = os.path.abspath(path)

        with open(os.path.join(static_path, 'header.html')) as head:
            shutil.copyfileobj(head, self.wfile)
        self.wfile.write('</div>')
        if not storage.is_readable():
            self.wfile.write('<h2>Please download a Wikipedia dump from ' +
                        '<a href="http://wiki.maemo.org/Evopedia">' +
                        'http://wiki.maemo.org/Evopedia</a>, ' +
                        'extract it to a folder on your device and ' +
                        'select this folder here.</h2>')
        else:
            self.wfile.write('<h2>Please choose data directory</h2>')

        # make every part of the current path clickable
        path_parts = []
        path_cur = path
        while path_cur != '' and path_cur != '/':
            (path_next, path_part) = os.path.split(path_cur)
            if path_part == '':
                continue
            path_parts += ['<a href="/choose_data?path=%s">%s</a></li>' %
                            (quote(path_cur.encode('utf-8')),
                                saxutils.escape(path_part.encode('utf-8')))]
            path_cur = path_next

        self.wfile.write('<h3>%s</h3>' %
                            ('/' + '/'.join(reversed(path_parts))))

        date = language = num_articles = error = None
        try:
            (date, language, num_articles) = storage_class.get_metadata(path)
        except Exception, e:
            error = "<p>This directory could contain a broken " \
                    "Wikipedia dump.<br />" \
                    "Error reading metadata file:<br />%s" % \
                            saxutils.escape(str(e))
            import traceback
            traceback.print_exc()
            pass
        if num_articles is not None:
            num_articles = ', %s articles' % num_articles
        else:
            num_articles = ''
        if date is not None:
            self.wfile.write(('<a href=/set_data?path=%s>' +
                    'Use this Wikipedia dump from ' +
                    '%s, language: %s%s</a>') %
                    (quote(path.encode('utf-8')), date,
                     language, num_articles))
        if error is not None:
            self.wfile.write(error.encode('utf-8'))

        self.wfile.write('<ul>')
        text = ('<li><a href="/choose_data?path=%s/..">..</a></li>'
                        % quote(path.encode('utf-8')))
        self.wfile.write(text.encode('utf-8'))

        try:
            for f in sorted([d for d in os.listdir(path)
                                            if not d.startswith('.')]):
                dir = os.path.join(path, f)
                if not os.path.isdir(dir):
                    continue
                quotedpath = quote(dir.encode('utf-8'))
                quotedname = saxutils.escape(f)
                text = '<li><a href="/choose_data?path=%s">%s</a></li>' % (
                                            quotedpath, quotedname)
                self.wfile.write(text.encode('utf-8'))
        except OSError:
            self.wfile.write('Could not list directory.')

        self.wfile.write('</ul>')
        with open(os.path.join(static_path, 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)

    def write_header(self, content_type='text/html', charset='UTF-8',
                        expires=False):
        self.send_response(200)
        if charset is not None:
            charset = '; charset=' + charset
        else:
            charset = ''
        self.send_header('Content-type', content_type + charset)
        if expires:
            exp_time = time.time() + 3600 * 24
            self.send_header('Expires',
                time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                    time.gmtime(exp_time)))
        self.end_headers()

    def do_exit(self):
        global static_path
        global gps_handler

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(os.path.join(static_path, 'header.html')) as head:
            shutil.copyfileobj(head, self.wfile)
        self.wfile.write("</div><h2>Closing Evopedia</h2>")
        self.wfile.write("<p>Releasing GPS (if used) and "
                        "shutting down server.</p>")
        self.wfile.write("<p>You can close the browser window now.</p>")
        with open(os.path.join(static_path, 'footer.html')) as foot:
            shutil.copyfileobj(foot, self.wfile)

        if gps_handler is not None:
            pos = gps_handler.release_gps()

        # the following is not available before Python 2.6
        # so we need to do it the hard way.
        # better ideas?
        try:
            self.server.shutdown()
        except AttributeError:
            os._exit(0)

    def decode(self, s):
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError:
            try:
                s = s.decode('latin-1')
            except UnicodeDecodeError:
                pass
        return s

    def do_GET(self):
        global storage
        global static_path

        dict = None
        i = self.path.rfind('?')
        if i >= 0:
            self.path, query = self.path[:i], self.path[i + 1:]
            if query:
                dict = cgi.parse_qs(query)

        if self.path.endswith('/skins/common/images/magnify-clip.png'):
            # compatibility with older versions
            self.path = '/static/magnify-clip.png'

        parts = [self.decode(unquote(i)) for i in self.path.split('/') if i]

        if len(parts) == 0:
            if not storage.is_readable():
                self.send_response(302)
                self.send_header('Location', '/choose_data')
                return
            self.write_header()
            with open(os.path.join(static_path, 'search.html')) as search:
                data = search.read()
                num_articles = storage.get_num_articles()
                if num_articles is not None:
                    num_articles = ', %s articles' % num_articles
                else:
                    num_articles = ''
                data = data.replace("EVOPEDIA_INFO",
                            ('<a href="%s">Wikipedia (%s)</a>, ' +
                                '<a href="/choose_data">%s%s</a> '
                                '<small>via ' + EVOPEDIA_VERSION +
                                            '</small>') %
                            (storage.get_orig_url(''),
                                 storage.get_language(),
                                 storage.get_date(),
                                 num_articles))
                self.wfile.write(data)
            return
        elif parts[0] == 'static':
            if len(parts) == 2 and parts[1] in set(['search.js', 'main.css',
                    'magnify-clip.png', 'mapclient.js', 'zoomin.png',
                    'zoomout.png', 'search.png', 'wikipedia.png', 'close.png',
                    'random.png', 'map.png', 'maparticle.png', 'home.png',
                    'crosshairs.png', 'exit.png']):
                if parts[1].endswith('.png'):
                    self.write_header('image/png', expires=True)
                elif parts[1].endswith('.css'):
                    self.write_header('text/css', expires=True)
                elif parts[1].endswith('.js'):
                    self.write_header('application/javascript', expires=True)
                else:
                    self.write_header(expires=True)
                with open(os.path.join(static_path, parts[1])) as fobj:
                    shutil.copyfileobj(fobj, self.wfile)
                return
        elif parts[0] == 'search':
            if not storage.is_readable():
                return
            try:
                query = self.decode(dict['q'][0])
            except (UnicodeDecodeError, TypeError, KeyError):
                query = ''
            self.output_search_result(query, 50)
            return
        elif parts[0] == 'map':
            try:
                coords = (float(dict['lat'][0]), float(dict['lon'][0]))
            except (ValueError, KeyError, TypeError):
                coords = (50, 10)

            try:
                zoom = int(dict['zoom'][0])
            except (ValueError, KeyError, TypeError):
                zoom = 3

            self.output_map(coords, zoom)
            return
        elif parts[0] == 'maptile':
            try:
                (repoindex, z, x, y) = parts[1:5]
                y = y.split('.')[0]
                global tile_repository
                tile_repository[int(repoindex)]\
                        .output_map_tile(self, int(x), int(y), int(z))
            except Exception, e:
                self.output_error_msg_page('Invalid URL')
                import traceback
                traceback.print_exc()
            return
        elif parts[0] == 'geo':
            if not storage.is_readable():
                return
            try:
                minx = int(dict['minx'][0])
                miny = int(dict['miny'][0])
                maxx = int(dict['maxx'][0])
                maxy = int(dict['maxy'][0])
                zoom = int(dict['zoom'][0])
            except (ValueError, KeyError, TypeError):
                self.output_error_msg_page('Invalid URL')
                return
            self.output_geo_articles(zoom, minx, miny, maxx, maxy)
            return
        elif parts[0] == 'gpspos':
            try:
                zoom = int(dict['zoom'][0])
            except (ValueError, KeyError, TypeError):
                self.output_error_msg_page('Invalid URL')
                return

            global gps_handler

            self.write_header('text/xml')
            self.wfile.write("<?xml version='1.0' encoding='UTF-8' ?>\n")
            if gps_handler is not None:
                pos = gps_handler.get_gps_pos()
                if pos is False:
                    self.wfile.write('<error>No GPS Fix</error>')
                    return

                (coordx, coordy) = self.coords2pixel(zoom, pos)

                self.wfile.write('<position x="%f" y="%f" zoom="%d"/>' %
                                 (coordx, coordy, zoom))
            else:
                self.wfile.write('<error>GPS deactivated ' +
                                'in configuration file</error>')
            return
        elif parts[0] == 'random':
            if not storage.is_readable():
                self.send_response(302)
                self.send_header('Location', '/choose_data')
                return
            title = storage.get_random_article()
            if title is not None:
                self.send_response(302)
                self.send_header('Location', pathname2url('/wiki/' +
                                                title.encode('utf-8')))
                self.end_headers()
            else:
                self.output_error_msg_page("Error finding random page...")
            return
        elif parts[0] == 'choose_data':
            self.output_data_selector(parts, dict)
            return
        elif parts[0] == 'set_data':
            data_dir = dict['path'][0]
            print "Changing datafile storage to %s." % data_dir
            global storage_class
            from datafile_storage import DatafileStorage, \
                                DatafileInitializationError
            storage_class = DatafileStorage
            storage = DatafileStorage()
            try:
                storage.storage_init_read(data_dir)
            except Exception, e:
                self.output_error_msg_page('Error opening datafile storage '
                        'at %s:<br />%s' % (data_dir, str(e)))
                return

            if storage.is_readable():
                global config
                global configfile
                config.set('evopedia', 'data_directory', data_dir)
                with open(os.path.expanduser(configfile), 'wb') as f:
                    config.write(f)
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            return
        elif parts[0] == 'math' or (
                        parts[0] == 'wiki' and parts[1] == 'math'):
            # second case is workaround for bug in dumps
            if not storage.is_readable():
                self.send_response(302)
                self.send_header('Location', '/choose_data')
                return

            self.write_header('image/png', charset=None, expires=True)
            data = storage.get_math_image(parts[-1][:32])
            if data is not None:
                self.wfile.write(data)
            return
        elif parts[0] in ('wiki', 'articles'):
            if not storage.is_readable():
                self.send_response(302)
                self.send_header('Location', '/choose_data')
                return

            url = '/'.join(parts[1:])

            if parts[-1].startswith("File:"):
                self.send_response(302)
                self.send_header('Location', storage.get_orig_url(url))
                return

            self.output_wiki_page(url)
            return
        elif parts[0] == 'exit':
            self.do_exit()
            return

        self.output_error_page()


class GPSHandler(object):

    def __init__(self):
        self.gps_activated = False
        self.last_gps_usage = 0

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while True:
            try:
                if self.gps_activated and \
                            self.last_gps_usage < time.time() - 5 * 60:
                    self.release_gps()
                time.sleep(60)
            except Exception, e:
                print e

    def get_gps_pos(self):
        self.last_gps_usage = time.time()
        if not self.gps_activated:
            if not self.request_gps():
                return False
            self.gps_activated = True

        return self.get_gps_pos_internal()

    @staticmethod
    def handler_factory():
        if GPSHandlerLiblocation.is_usable():
            print("Accessing GPS via liblocation")
            return GPSHandlerLiblocation()
        if GPSHandlerGypsy.is_usable():
            print("Accessing GPS via Gypsy")
            return GPSHandlerGypsy()
        return None


class GPSHandlerGypsy(GPSHandler):

    def __init__(self):
        self.dbus = None
        self.ousaged = None
        self.gypsy = None

        GPSHandler.__init__(self)

    @staticmethod
    def is_usable():
        try:
            import dbus
            # we could check if gypsy exists on the bus, but that
            # would directly activate GPS
            return True
        except ImportError:
            return False

    def init_dbus(self):
        import dbus
        try:
            if self.dbus is None:
                self.dbus = dbus.SystemBus()
            gypsy_object = self.dbus.get_object("org.freedesktop.Gypsy",
                    "/org/freedesktop/Gypsy")
            self.gypsy = dbus.Interface(gypsy_object,
                    "org.freedesktop.Gypsy.Position")
            ousaged_object = self.dbus.get_object("org.freesmartphone.ousaged",
                    "/org/freesmartphone/Usage")
            self.ousaged = dbus.Interface(ousaged_object,
                    "org.freesmartphone.Usage")
        except dbus.exceptions.DBusException, e:
            print e
            if self.gypsy is None:
                return False
            return True

    def request_gps(self):
        self.last_gps_usage = time.time()
        if self.gps_activated:
            return True
        if self.gypsy is None:
            self.init_dbus()
        try:
            self.ousaged.RequestResource("GPS")
            self.gps_activated = True
            return True
        except Exception, e:
            print e
        return False

    def get_gps_pos_interal(self):
        (valid, tstamp, lat, lng, alt) = self.gypsy.GetPosition()

        if lat != 0 and lng != 0:
            return (lat, lng)
        else:
            return False

    def release_gps(self):
        self.gps_activated = False
        if self.ousaged is None:
            return
        print("Releasing GPS...")
        self.ousaged.ReleaseResource("GPS")


class GPSHandlerLiblocation(GPSHandler):

    def __init__(self):
        import location
        self.control = location.GPSDControl.get_default()
        self.device = location.GPSDevice()

        GPSHandler.__init__(self)

    @staticmethod
    def is_usable():
        try:
            import location
            return True
        except ImportError:
            return False

    def request_gps(self):
        self.control.start()
        return True

    def get_gps_pos_internal(self):
        (lat, lon) = self.device.fix[4:6]
        if lat == lat and lon == lon:
            return (lat, lon)
        else:
            return False

    def release_gps(self):
        self.gps_activated = False
        print("Releasing GPS...")
        self.control.stop()


class TileRepo(object):

    def __init__(self, title, tileurl, tilepath, zoom_last=False):
        self.title = title
        self.tileurl = saxutils.unescape(tileurl)
        self.tilepath = tilepath
        self.zoom_last = zoom_last

    def __str__(self):
        return u'Tile Repository "%s" (%s, %s)' % (self.title, self.tilepath,
                self.tileurl)

    def output_map_tile(self, request_handler, x, y, zoom):
        if self.tilepath is not None:
            if self.get_local_tile(request_handler, x, y, zoom):
                return
            # no local file found, so download it
            try:
                self.download_remote_tile(request_handler, x, y, zoom)
            except OSError, URLError:
                print("Downloading tile or saving of downloaded" +
                        "tile could have failed.")
            if self.get_local_tile(request_handler, x, y, zoom):
                return

        # no local repository or error in it
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
            request_handler.write_header(
                    content_type='image/jpeg', expires=True)
        else:
            request_handler.write_header(
                    content_type='image/png', expires=True)
        request_handler.wfile.write(image)
        return True

    def get_remote_tile_url(self, x, y, zoom):
        # some special remote tile handlers copied from the tangogps source
        if self.tileurl == 'maps-for-free':
            return ('http://maps-for-free.com/layer/relief/' +
                    'z%d/row%d/%d_%d-%d.jpg' % (zoom, y, zoom, x, y))
        elif self.tileurl == 'openaerial':
            return ('http://tile.openaerialmap.org/tiles/1.0.0/' +
                    'openaerialmap-900913/%d/%d/%d.jpg' % (zoom, x, y))
        else:
            if self.zoom_last:
                return self.tileurl % (x, y, zoom)
            else:
                return self.tileurl % (zoom, x, y)

    def download_remote_tile(self, request_handler, x, y, zoom):
        url = self.get_remote_tile_url(x, y, zoom)
        print("Fetching tile %s..." % url)
        content = urllib2.urlopen(url).read()

# XXX in maemo, don't do this as long as MyDocs is not mounted...

        tiledir = os.path.join(self.tilepath, str(zoom), str(x))
        if not os.path.exists(tiledir):
            os.makedirs(tiledir)

        tilefile = os.path.join(tiledir, '%d.png' % (y,))
        with open(tilefile, 'wb') as f:
            f.write(content)

    def redirect_to_remote_tile(self, request_handler, x, y, zoom):
        request_handler.send_response(301)
        request_handler.send_header('Location',
                self.get_remote_tile_url(x, y, zoom))
        request_handler.end_headers()

    def send_remote_tile(self, request_handler, x, y, zoom):
        url = self.get_remote_tile_url(x, y, zoom)
        print("Fetching %s..." % url)
        f = urllib2.urlopen(url)
        request_handler.write_header(f.info().get('Content-type'),
                                     charset=None, expires=True)
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
        except Exception:
            if len(repos) == 0:
                repos = [TileRepo('OSM',
                    'http://tile.openstreetmap.org/%d/%d/%d.png',
                    None, False)]
        return repos


class ThreadingHTTPServer(SocketServer.ThreadingMixIn, HTTPServer):
    daemon_threads = True


def get_default_repositories():
    import os

    maep_path = '/home/user/MyDocs/.maps/'

    if os.path.exists(maep_path):
        # maep is installed, use its repository
        # XXX make the repostrings as flexible as maep's (using mapping keys)
        return ('[' +
                'OpenStreetMap I|' +
                    'http://tile.openstreetmap.org/%d/%d/%d.png|' +
                    maep_path + '/OpenStreetMap I/|0,' +
                'OpenStreetMap II|' +
                    'http://tah.openstreetmap.org/Tiles/tile/%d/%d/%d.png|' +
                    maep_path + '/OpenStreetMap II/|0,' +
                'OpenCycleMap|' +
                    'http://c.andy.sandbox.cloudmade.com/' +
                                'tiles/cycle/%d/%d/%d.png|' +
                    maep_path + '/OpenCycleMap/|0,' +
                'Public Transport|' +
                    'http://tile.xn--pnvkarte-m4a.de/tilegen/%d/%d/%d.png|' +
                    maep_path + '/Public Transport/|0]')
    else:
        return ''


def start_server():
    import sys

    global config
    global configfile

    configfile_expanded = os.path.expanduser(configfile)

    if not os.path.exists(configfile_expanded):
        with open(configfile_expanded, 'wb') as c:
            # write minimal default config
            c.write("[evopedia]\n" +
                    "version = 0.3.0\n" +
                    "listen_address = 127.0.0.1\n" +
                    "port = 8080\n" +
                    "use_gps = yes\n" +
                    "maptile_repositories = " +
                        get_default_repositories() + "\n" +
                    "data_directory = ~/\n")

    config = ConfigParser.RawConfigParser()
    config.read(configfile_expanded)

    port = config.getint('evopedia', 'port')
    address = config.get('evopedia', 'listen_address')
    use_gps = config.get('evopedia', 'use_gps')
    repostring = config.get('evopedia', 'maptile_repositories')
    if repostring == '':
        config.set('evopedia', 'maptile_repositories',
                get_default_repositories())
        try:
            with open(configfile_expanded, 'wb') as f:
                config.write(f)
        except:
            print("Unable to write config file.")
    data_dir = config.get('evopedia', 'data_directory')

    data_dir = os.path.expanduser(data_dir)
    if not os.path.exists(data_dir):
        print("Data directory %s not found." % data_dir)

    global tile_repository
    tile_repository = TileRepo.parse_tilerepos(repostring)
    print "Using map tile repositories " + str([x.title
                                            for x in tile_repository])

    global gps_handler
    if use_gps == 'yes' or use_gps == '1':
        print("Enabling GPS...")
        gps_handler = GPSHandler.handler_factory()

    global storage
    global storage_class
    print "Using datafile storage."
    from datafile_storage import DatafileStorage, DatafileInitializationError
    storage_class = DatafileStorage
    storage = DatafileStorage()
    try:
        storage.storage_init_read(data_dir)
    except DatafileInitializationError:
        print("Error opening storage.")
        import traceback
        traceback.print_exc()
    except Exception:
        print("Error opening storage.")
        import traceback
        traceback.print_exc()

    import socket

    try:
        server = ThreadingHTTPServer((address, port), EvopediaHandler)
    except socket.error:
        print 'Socket error. Perhaps there is already some server ' + \
                'running. Exiting.'
        sys.exit(1)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
        sys.exit(0)
