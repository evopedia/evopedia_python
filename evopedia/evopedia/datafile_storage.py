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

from __future__ import with_statement

import os
import sys
import struct
import operator
import itertools
import bz2
import random
import urllib
import ConfigParser

import evopediautils

__all__ = ["DatafileStorage"]


class DatafileStorage(object):
    """Class for reading from and creating compressed wikipedia images.

    storage_init_read or storage_create have to be called to really
    use the Storage."""

    def storage_init_read(self, directory):
        self.readable = 0

        self.data_dir = directory
        self.titles_file = os.path.join(directory, 'titles.idx')
        self.data_files_schema = os.path.join(directory, 'wikipedia_%02d.dat')
        self.math_data_file = os.path.join(directory, 'math.dat')
        self.math_index_file = os.path.join(directory, 'math.idx')

        if not os.path.exists(self.math_index_file) or \
                not os.path.exists(self.math_data_file):
            self.math_index_file = None
            self.math_data_file = None

        parser = ConfigParser.RawConfigParser()
        parser.read(os.path.join(directory, 'metadata.txt'))

        self.dump_date = parser.get('dump', 'date')
        self.dump_language = parser.get('dump', 'language')
        self.dump_orig_url = parser.get('dump', 'orig_url')
        self.dump_version = parser.get('dump', 'version')
        try:
            self.num_articles = parser.get('dump', 'num_articles')
        except:
            self.num_articles = None

        self.initialize_coords(parser)

        if self.math_index_file is not None:
            self.math_index_size = os.path.getsize(self.math_index_file)
        self.titles_file_size = os.path.getsize(self.titles_file)

        self.readable = 1

    def initialize_coords(self, parser):
        coordfiles = []
        i = 1
        while True:
            try:
                file = parser.get('coordinates', 'file_%02d' % i)
            except:
                break
            coordfiles += [os.path.join(self.data_dir, file)]
            i += 1
        self.coordinate_files = coordfiles

    def storage_create(self, image_dir, titles_file, coordinates_files_schema,
                            data_files_schema,
                            math_data_file, math_index_file,
                            metadata_file,
                            dump_date, dump_language, dump_orig_url):
        self.titles_file = titles_file
        self.coordinates_files_schema = coordinates_files_schema
        self.data_files_schema = data_files_schema
        self.math_data_file = math_data_file
        self.math_index_file = math_index_file
        print("Converting image...")

        num_articles = self.convert_articles(image_dir, write=True)
        self.generate_index(write=True)
        coord_files = self.write_coordinates(10)

        print("Writing metadata file...")
        config = ConfigParser.RawConfigParser()
        config.add_section('dump')
        config.set('dump', 'date', dump_date)
        config.set('dump', 'language', dump_language)
        config.set('dump', 'orig_url', dump_orig_url)
        config.set('dump', 'version', '0.3')
        config.set('dump', 'num_articles', num_articles)
        config.add_section('coordinates')
        for (i, file) in enumerate(coord_files):
            config.set('coordinates', 'file_%02d' % (i + 1), file)
        with open(metadata_file, 'wb') as md_f:
            config.write(md_f)

    # --- storage interface ---
    def get_num_articles(self):
        return self.num_articles

    def get_datadir(self):
        return self.data_dir

    def is_readable(self):
        return self.readable

    def get_date(self):
        return self.dump_date

    def get_language(self):
        return self.dump_language

    def get_orig_url(self, title):
        if self.dump_version == '0.2':
            title = self.transform_path_from_v2(title)
        return self.dump_orig_url + urllib.quote(title.encode('utf-8'))

    def get_article_by_name(self, name):
        """Get the text of an article.

        Returns the text of the article with the (exact) specified name or
        None if the article does not exist.
        """
        if self.dump_version == '0.2':
            name = self.transform_path_from_v2(name)
        for (title, articlepos) in self.get_titles_with_prefix(name):
            if title == name:
                return self.get_article_by_pos(articlepos)
        return None

    def get_titles_with_prefix(self, prefix):
        """Generator that returns all titles with the specified prefix.

        The generated items are pairs of title and position specifier. Note
        that the prefix and the titles are only compared in their normalized
        (i.e. with special symbols translated) form.
        """
        prefix = evopediautils.normalize(prefix)

        lo = 0
        hi = self.titles_file_size
        with open(self.titles_file, 'rb') as f_titles:
            while lo < hi:
                mid = (lo + hi) // 2
                f_titles.seek(mid)
                line = f_titles.readline()
                aftermid = mid + len(line)
                if mid > 0: # potentially incomplete line
                    line = f_titles.readline()
                    aftermid += len(line)
                if line == '': # end of file
                    hi = mid
                    continue
                (title, articlepos) = self.titleentry_decode(line)
                title = evopediautils.normalize(title)
                if title < prefix:
                    # position lo just before the next entry
                    lo = aftermid - 1
                else:
                    hi = mid

            if lo > 0:
                # let lo point to the start of an entry
                lo += 1

            for (title, articlepos) in self.titlestream_at_offset(lo,
                                            titlefile=f_titles):
                title_n = evopediautils.normalize(title)
                if title_n.startswith(prefix):
                    yield (title, articlepos)
                else:
                    return

    def get_random_article(self):
        """Returns the title of a random article."""
        size = self.titles_file_size

        # long titles are preferred by this method, oh well...
        pos = random.randint(0, size)

        with open(self.titles_file, 'rb') as f_titles:
            f_titles.seek(pos, os.SEEK_SET)
            pos += len(f_titles.readline())
            if pos >= size:
                f_titles.seek(0, os.SEEK_SET)
            entry = f_titles.readline()
            (title, articlepos) = self.titleentry_decode(entry)
            return title

    def titles_in_coords(self, mincoords, maxcoords):
        """Generates the titles with coordinates in the given area.

        The two edges of the rectangle are given in latitude, longitude order
        and the generator returns tuples (title, latitude, longitude, url).
        """
        for f in self.coordinate_files:
            with open(f, 'rb') as coordf:
                with open(self.titles_file, 'rb') as titlesf:
                    for item in self.titles_in_coords_int(coordf, 0, titlesf,
                                    mincoords, maxcoords,
                                    -91.0, 91.0, -181.0, 181.0):
                        yield item

    def get_math_image(self, hash):
        """Returns a PNG file typically containing a math formula based on a
        32-character hex string."""

        if self.math_index_file is None or self.math_data_file is None:
            return None

        try:
            hash = hash.decode('hex')
        except TypeError:
            return None
        if len(hash) != 16:
            return None

        entrysize = 16 + 4 + 4
        pos = None

        lo = 0
        hi = self.math_index_size / entrysize
        with open(self.math_index_file, 'rb') as f:
            while lo < hi:
                mid = (lo + hi) // 2
                f.seek(mid * entrysize, os.SEEK_SET)
                entry = f.read(entrysize)
                e_hash = entry[:16]
                if e_hash == hash:
                    pos = entry[16:24]
                    break
                elif hash < e_hash:
                    hi = mid
                else:
                    lo = mid + 1
        if pos is None:
            return None

        (pos, datalen) = struct.unpack('<II', pos)
        with open(self.math_data_file, "rb") as f:
            f.seek(pos, os.SEEK_SET)
            return f.read(datalen)

    @staticmethod
    def get_metadata(dir):
        metadata_file = os.path.join(dir, 'metadata.txt')
        if not os.path.exists(metadata_file):
            return (None, None, None)
        parser = ConfigParser.RawConfigParser()
        parser.read(metadata_file)
        num_articles = None
        try:
            num_articles = parser.get('dump', 'num_articles')
        except:
            pass
        return (parser.get('dump', 'date'), parser.get('dump', 'language'),
                num_articles)
    # --- end of storage interface ---

    def transform_path_from_v2(self, pathname):
        import re
        title = pathname.split('/')[-1]
        endpattern = re.compile('(_[0-9a-f]{4})?(\.html(\.redir)?)?$')
        return endpattern.sub('', title)

    def titles_in_coords_int(self, coordf, filepos, titlesf,
                               mintarget, maxtarget,
                               minlat, maxlat, minlon, maxlon):
        if (maxtarget[0] < minlat or maxlat <= mintarget[0]) or \
                (maxtarget[1] < minlon or maxlon <= mintarget[1]):
            # target rectangle does not overlap with current rectangle
            return

        coordf.seek(filepos, os.SEEK_SET)
        (selector,) = struct.unpack('<H', coordf.read(2))
        if selector == 0xffff:
            # another subdivision needed
            (clat, clon, lensw, lense, lennw) = struct.unpack('<ffIII',
                                                            coordf.read(20))
            pos0 = filepos + 22
            pos1 = pos0 + lensw
            pos2 = pos1 + lense
            pos3 = pos2 + lennw
            for item in self.titles_in_coords_int(coordf, pos0, titlesf,
                                    mintarget, maxtarget,
                                    minlat, clat, minlon, clon):
                yield item
            for item in self.titles_in_coords_int(coordf, pos1, titlesf,
                                    mintarget, maxtarget,
                                    minlat, clat, clon, maxlon):
                yield item
            for item in self.titles_in_coords_int(coordf, pos2, titlesf,
                                    mintarget, maxtarget,
                                    clat, maxlat, minlon, clon):
                yield item
            for item in self.titles_in_coords_int(coordf, pos3, titlesf,
                                    mintarget, maxtarget,
                                    clat, maxlat, clon, maxlon):
                yield item
        else:
            data = coordf.read(selector * 12)
            for i in range(selector):
                chunk = data[i * 12:(i + 1) * 12]
                (lat, lon, title_pos) = struct.unpack('<ffI', chunk)
                if not (mintarget[0] <= lat <= maxtarget[0] and
                        mintarget[1] <= lon <= maxtarget[1]):
                    continue
                titlesf.seek(title_pos, os.SEEK_SET)
                (title, articlepos) = self.titleentry_decode(titlesf.readline())
                yield (title, lat, lon)

    def get_article_by_pos(self, articlepos):
        """Returns the text of the article referenced by articlepos, even if
        articlepos specifies a redirection."""
        if articlepos[0] == 0xff: # redirect
            if articlepos[1] == 0xffffffff:
                return None
            offset = articlepos[1]
            (title, articlepos) = self.title_at_offset(offset)

        (filenr, block_start, block_offset, article_len) = articlepos

        with open(self.data_files_schema % filenr) as datafile:
            datafile.seek(block_start, os.SEEK_SET)

            bytes_read = 0
            article_data = ''

            dec = bz2.BZ2Decompressor()
            while bytes_read < block_offset + article_len:
                try:
                    data = dec.decompress(datafile.read(20480))
                except EOFError:
                    break
                if bytes_read + len(data) > block_offset:
                    dstart = block_offset - bytes_read
                    dend = dstart + article_len
                    article_data += data[dstart:dend]
                bytes_read += len(data)

            return article_data

    def titleentry_encode(self, articlepos, title):
        """Encodes the position specification of an article and its title.

        The resulting data will only contain a line break at the end and the
        encoded position specification will have constant size.

        title must be utf-8 encoded.
        """
        (filenr, block_start, block_offset, article_len) = articlepos
        pos = struct.pack('<BIII', filenr, block_start,
                                        block_offset, article_len)
        escapes = 0
        escaped_pos = ''
        for (i, c) in enumerate(pos):
            if c == '\n':
                escaped_pos += '\x00'
                escapes |= 1 << i
            else:
                escaped_pos += c
        if escapes & 0xff == ord('\n'):
            # escape lower byte
            escapes &= 0xff00
            escapes |= 1 << 14
        escapes |= 1 << 15 # ensure that higher byte of escapes != '\n'
        return struct.pack('<H', escapes) + escaped_pos + title + '\n'

    def titleentry_decode(self, data):
        """Decodes the position specification and title of an article as
        encoded by titleentry_encode."""
        (escapes,) = struct.unpack('<H', data[:2])
        if escapes & (1 << 14) != 0:
            escapes |= ord('\n')
        escaped_position = data[2:15]
        title = data[15:-1].decode('utf-8')
        position = ''
        for (i, c) in enumerate(escaped_position):
            if escapes & (1 << i) != 0:
                position += '\n'
            else:
                position += c
        return (title, struct.unpack('<BIII', position))

    def titleentry_encodedlen(self, title):
        """Returns the length of the position specification and title of an
        article as encoded by titleentry_encode."""
        return struct.calcsize('<HBIII') + len(title) + 1

    def title_at_offset(self, offset):
        with open(self.titles_file, 'rb') as f_titles:
            f_titles.seek(offset, os.SEEK_SET)
            return self.titleentry_decode(f_titles.readline())

    def titlestream_at_offset(self, offset, titlefile=None):
        if titlefile is None:
            f_titles = open(self.titles_file, 'rb')
        else:
            f_titles = titlefile

        try:
            f_titles.seek(offset, os.SEEK_SET)
            for line in f_titles:
                yield self.titleentry_decode(line)
        finally:
            if titlefile is None:
                f_titles.close()

    def data_compressor_multi_bz2(self, datafiles_schema,
                                     datafiles_size, block_size, level=9):
        filenr = 0
        datafile_pos = 0
        full_size = 0

        datafile = open(datafiles_schema % filenr, 'wb')
        queued_data = ''
        try:
            while True:
                try:
                    while len(queued_data) < block_size:
                        queued_data += yield (filenr, datafile_pos,
                                              len(queued_data))
                finally:
                    data = bz2.compress(queued_data, level)
                    full_size += len(queued_data)
                    queued_data = ''
                    datafile.write(data)
                    datafile_pos += len(data)
                    data = ''
                if datafile_pos >= datafiles_size:
                    print("Finished datafile %d (compression ratio %f)." %
                            (filenr, float(full_size) / float(datafile_pos)))
                    datafile.close()
                    filenr += 1
                    datafile_pos = 0
                    datafile = open(datafiles_schema % filenr, 'wb')
                    full_size = 0
        finally:
            datafile.close()

    def convert_articles(self, image_dir, write=True):
        datafiles_size = 500 * 1024 * 1024
        block_size = 512 * 1024

        # speed optimization
        parse_coords = evopediautils.parse_coordinates_in_article

        import re
        endpattern = re.compile('(_[0-9a-f]{4})?(\.html(\.redir)?)?$')

        num_articles = 0

        titles = []
        images = []

        print("Compressing articles and math images...")

        # because of memory efficiency, all strings are utf-8 encoded and not
        # unicode

        if write:
            article_compressor = self.data_compressor_multi_bz2(
                                self.data_files_schema,
                                datafiles_size, block_size)
            (art_filenr, art_datafile_pos, art_block_pos) = \
                    article_compressor.next()
            math_data = open(self.math_data_file, "wb")
            math_data_pos = 0

        for (dirpath, dirnames, filenames) in os.walk(image_dir):
            if 'coords' in dirnames:
                dirnames.remove('coords')
            print("%d files in dir %s" % (len(filenames), repr(dirpath)))
            for fname in filenames:
                if fname in ('creation_date', 'evopedia_version',
                             'index.html'):
                    continue
                title = fname
                if title.endswith('.html') or title.endswith('.redir'):
                    # old dump software
                    title = endpattern.sub('', title)

                f = os.path.join(dirpath, fname)
                if os.path.islink(f):
                    destination = os.path.basename(os.readlink(f))
                    destination = destination
                    if destination.endswith('.html'):
                        destination = os.path.basename(destination)
                        destination = endpattern.sub('', destination)
                    titles += [[title, None, destination,
                                (None, None, None)]]
                elif fname.endswith('.redir'):
                    with open(f) as ff:
                        destination = ff.read()
                    destination = os.path.basename(destination)
                    destination = endpattern.sub('', destination)
                    titles += [[title, None, destination,
                                (None, None, None)]]
                elif fname.endswith('.png'):
                    try:
                        hash = fname[:-4].decode('hex')
                    except ValueError:
                        print("Invalid math image name: %s" % fname)
                        continue
                    if write:
                        with open(os.path.join(dirpath, fname), 'rb') as fd:
                            fdata = fd.read()
                        images += [hash + struct.pack('<II',
                                            math_data_pos, len(fdata))]
                        math_data.write(fdata)
                        math_data_pos += len(fdata)
                    else:
                        images += [hash]
                else:
                    num_articles += 1
                    if write:
                        with open(os.path.join(dirpath, fname), 'rb') as fd:
                            fdata = fd.read()
                        (lat, lng, zoom) = parse_coords(fdata)
                        article_pos = (art_filenr, art_datafile_pos,
                                        art_block_pos, len(fdata))
                        titles += [[title, None, article_pos,
                                        (lat, lng, zoom)]]
                        (art_filenr, art_datafile_pos, art_block_pos) = \
                                article_compressor.send(fdata)
                    else:
                        titles += [[title, None, (0, 0, 0, 0),
                                    (None, None, None)]]
        if write:
            article_compressor.close()
            math_data.close()

            print("Sorting and storing math images...")
            images.sort()
            with open(self.math_index_file, "wb") as mathindex:
                mathindex.write(''.join(images))

        if __debug__:
            with open("title_list.txt", "wb") as titlelist:
                for t in titles:
                    titlelist.write('\t'.join([repr(x) for x in t]) + '\n')

        self.titles = titles
        # format for titles:
        # [title, pos in index, article pos (or redirect data),
        #  coordinates]

        return num_articles

    def generate_index(self, write=True):
        n = evopediautils.normalize # speed optimization
        print "Sorting titles and redirects..."
        self.titles.sort(key=lambda x: n(x[0].decode('utf-8')))

        # format for titles:
        # [title, pos in index, article pos (or redirect data),
        #  coordinates]
        print "Writing titles index..."
        title_positions = {}

        title_pos = 0
        for (i, title) in enumerate(self.titles):
            title[1] = title_pos
            title_positions[title[0]] = title_pos
            title_pos += self.titleentry_encodedlen(title[0])

        self.title_positions = title_positions
        if not write:
            return

        print("Resolving redirects and writing title index...")

        with open(self.titles_file, 'wb') as f_titles:
            for title in self.titles:
                if type(title[2]) == type(''): # redirect
                    try:
                        dest_pos = title_positions[title[2]]
                    except KeyError:
                        dest_pos = 0xffffffff
                    articlepos = (0xff, dest_pos, 0, 0)
                else:
                    articlepos = title[2]

                data = self.titleentry_encode(articlepos, title[0])
                f_titles.write(data)

    def write_coordinates(self, max_articles_per_section):
        # format for titles:
        # [title, pos in index, article pos (or redirect data),
        #  coordinates]

        coords_by_zoom = [[] for i in range(20)]
        tpos = self.title_positions

        for title in self.titles:
            (lat, lng, zoom) = title[3]
            if lat is None:
                continue
            if title[0] not in tpos:
                print("Title %s not found (referenced by coordinates)."
                           % repr(title[0]))
                continue

            coords_by_zoom[zoom] += [(lat, lng, tpos[title[0]])]

        coord_files = []

        print "Generating quadtrees..."
        i = 1
        for items in coords_by_zoom:
            if not items:
                continue
            data = self.get_quadtree_index_table(items,
                                          -91.0, 91.0, -181.0, 181.0,
                                          max_articles_per_section)
            cfile = self.coordinates_files_schema % i
            with open(cfile, 'wb') as coord_file:
                coord_file.write(data)
            coord_files += [cfile]
            i += 1
        return coord_files

    def get_quadtree_index_table(self, items,
                                 minlat, maxlat, minlon, maxlon,
                                 maxitems):
        #print("Entered %f %f %f %f." % (minlat, maxlat, minlon, maxlon))
        items = [(lat, lon, title_pos) for (lat, lon, title_pos) in items
                                  if minlat <= lat < maxlat and
                                     minlon <= lon < maxlon]
        coords = set((lat, lon)
                                for (lat, lon, title_pos) in items)
        if len(coords) <= maxitems:
            if len(items) >= 0xffff:
                print("Too many articles at exactly the same point."
                        "Truncating list.")
                items = items[:0xffff - 1]
            data = struct.pack('<H', len(items))
            for (lat, lon, title_pos) in items:
                #print("Storing %f %f %d" % (lat, lon, title_pos))
                data += struct.pack('<ffI', lat, lon, title_pos)
            return data
        else:
            clat = (minlat + maxlat) / 2
            clon = (minlon + maxlon) / 2

            sw = self.get_quadtree_index_table(items, minlat, clat,
                                                      minlon, clon, maxitems)
            se = self.get_quadtree_index_table(items, minlat, clat,
                                                      clon, maxlon, maxitems)
            nw = self.get_quadtree_index_table(items, clat, maxlat,
                                                      minlon, clon, maxitems)
            ne = self.get_quadtree_index_table(items, clat, maxlat,
                                                      clon, maxlon, maxitems)
            return struct.pack('<HffIII', 0xffff, clat, clon,
                                          len(sw), len(se), len(nw)) + \
                    sw + se + nw + ne


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s\n"
              "          --convert <dir> <date> <language> <orig url>\n"
              "              converts an evopedia 2.0 article image\n"
              "              mounted at <dir> to evopedia 3.0 format\n"
              "          --searchgeo <minlat> <maxlat> <minlon> <maxlon>\n"
              "              search for articles in geographical area\n"
              "          --math <hash>\n"
              "              returns math image with hash <hash>\n"
              "          --article <text>\n"
              "              returns article with name <text>\n"
              "          <text>\n"
              "              searches for <text>" % sys.argv[0])
    else:
        backend = DatafileStorage()

        if sys.argv[1] == '--convert':
            backend.storage_create(sys.argv[2],
                                'titles.idx', 'coordinates_%02d.idx',
                                'wikipedia_%02d.dat',
                                'math.dat', 'math.idx',
                                'metadata.txt',
                                sys.argv[3], sys.argv[4], sys.argv[5])
        elif sys.argv[1] == '--article':
            backend.storage_init_read('./')
            print backend.get_article_by_name(sys.argv[2].decode('utf-8'))
        elif sys.argv[1] == '--searchgeo':
            backend.storage_init_read('./')
            (minlat, maxlat, minlon, maxlon) = (float(x) for x in sys.argv[2:6])
            titles = backend.titles_in_coords((minlat, minlon),
                                              (maxlat, maxlon))
            for (title, lat, lon) in titles:
                print "%s - %f, %f" % (title.encode('utf-8'), lat, lon)
        elif sys.argv[1] == '--math':
            backend.storage_init_read('./')
            data = backend.get_math_image(sys.argv[2])
            if data is None:
                print("Math image not found.")
            else:
                sys.stdout.write(data)
        else:
            backend.storage_init_read('./')
            prefix = sys.argv[1].decode('utf-8')
            titles = backend.get_titles_with_prefix(prefix)
            for title, pos in itertools.islice(titles, 10):
                print "%s - %s" % (title.encode('utf-8'), pos)
