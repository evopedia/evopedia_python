#!/usr/bin/python
# -*- encoding: utf-8

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
    
    storage_init_read or storage_init_create have to be called to really use the
    Storage."""


    def storage_init_read(self, titles_file, coordinates_file,
                            data_files_schema, metadata_file):
        self.titles_file = titles_file
        self.coordinates_file = coordinates_file
        self.data_files_schema = data_files_schema

        parser = ConfigParser.RawConfigParser()
        parser.read(metadata_file)

        self.dump_date = parser.get('dump', 'date')
        self.dump_language = parser.get('dump', 'language')
        self.dump_orig_url = parser.get('dump', 'orig_url')
        self.dump_version = parser.get('dump', 'version')

        self.titles_file_size = os.path.getsize(self.titles_file)

    def storage_create(self, image_dir, titles_file, coordinates_file,
                            data_files_schema, metadata_file,
                            dump_date, dump_language, dump_orig_url):
        self.titles_file = titles_file
        self.coordinates_file = coordinates_file
        self.data_files_schema = data_files_schema
        print("Converting image...")

        (articles, redirects) = self.convert_articles(image_dir)
        title_positions = self.generate_index(articles.items(),
                                              redirects.items(), 50)
        self.convert_coordinates(image_dir, 10, title_positions)

        print("Writing metadata file...")
        config = ConfigParser.RawConfigParser()
        config.add_section('dump')
        config.set('dump', 'date', dump_date)
        config.set('dump', 'language', dump_language)
        config.set('dump', 'orig_url', dump_orig_url)
        config.set('dump', 'version', '3.0')
        with open(metadata_file, 'wb') as md_f:
            config.write(md_f)

    # --- storage interface ---
    def get_date(self):
        return self.dump_date

    def get_language(self):
        return self.dump_language

    def get_orig_url(self, title):
        return self.dump_orig_url + urllib.quote(title.encode('utf-8'))

    def get_article_by_name(self, name):
        """Get the text of an article.
        
        Returns the text of the article with the (exact) specified name or
        None if the article does not exist.
        """
        for (title, articlepos) in self.get_titles_with_prefix(name):
            if title == name:
                return self.get_article_by_pos(articlepos)
        return None

    def get_titles_with_prefix(self, prefix):
        """Generator that returns all titles with the specified prefix.

        The generated items are pairs of title and position specifier. Note that
        the prefix and the titles are only compared in their normalized (i.e.
        with special symbols translated) form.
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
        with open(self.coordinates_file, 'rb') as coordf:
            with open(self.titles_file, 'rb') as titlesf:
                for item in self.titles_in_coords_int(coordf, 0, titlesf,
                                mincoords, maxcoords,
                                -91.0, 91.0, -181.0, 181.0):
                    yield item
    # --- end of storage interface ---

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
                (title, articlepos) = sef.titleentry_decode(titlesf.readline())
                yield (title, lat, lon, '/wiki/' + title.encode('utf-8'))


    # also handles redirects
    def get_article_by_pos(self, articlepos):
        print articlepos
        if articlepos[0] == 0xff: # redirect
            if articlepos[1] == 0xffffffff:
                return None
            offset = articlepos[1]
            print("redir...")
            (title, articlepos) = self.title_at_offset(offset)

        print articlepos
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
        escapes |= 1 << 15 # ensure that escapes != '\n'
        return struct.pack('<H', escapes) + escaped_pos + \
                                title.encode('utf-8') + '\n'

    def titleentry_decode(self, data):
        """Decodes the position specification and title of an article as encoded
        by titleentry_encode."""
        (escapes,) = struct.unpack('<H', data[:2])
        escaped_position = data[2:15]
        title = data[15:-1].decode('utf-8')
        position = ''
        for (i, c) in enumerate(escaped_position):
            if escapes & (1 <<  i) != 0:
                position += '\n'
            else:
                position += c
        return (title, struct.unpack('<BIII', position))

    def titleentry_encodedlen(self, title):
        """Returns the length of the position specification and title of an
        article as encoded by titleentry_encode."""
        return struct.calcsize('<HBIII') + len(title.encode('utf-8')) + 1

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

    def generate_index(self, articles, redirects, max_articles_per_prefix):
        self.max_articles_per_prefix = max_articles_per_prefix

        print "Normalizing titles and redirects..."
        # [title, normalized title, article position (or redirect signal and
        # position), is redirect]
        self.titles = [[title, evopediautils.normalize(title),
                        None, article_pos, False]
                        for (title, article_pos) in articles]
        self.titles += [[title, evopediautils.normalize(title),
                        None, destination, True]
                        for (title, destination) in redirects]

        print "Sorting titles and redirects..."
        self.titles.sort(key=operator.itemgetter(1))

        print "Writing titles index..."
        title_positions = self.write_titles_file()

        return title_positions

    def write_titles_file(self):
        title_positions = {}

        title_pos = 0
        for (i, title) in enumerate(self.titles):
            title[2] = title_pos
            title_positions[title[0]] = title_pos
            title_pos += self.titleentry_encodedlen(title[0])

        print("Resolving redirects and writing title index...")

        with open(self.titles_file, 'wb') as f_titles:
            for title in self.titles:
                if title[4]: # redirect
                    filenr = 0xff
                    try:
                        dest_pos = title_positions[title[3]]
                    except KeyError:
                        dest_pos = 0xffffffff
                    articlepos = (0xff, dest_pos, 0, 0)
                else:
                    articlepos = title[3]

                data = self.titleentry_encode(articlepos, title[0])
                f_titles.write(data)
        return title_positions

    def article_compressor_multi_bz2(self, datafiles_size,
                                     block_size, level=9):
        filenr = 0
        datafile_pos = 0
        full_size = 0

        datafile = open(self.data_files_schema % filenr, 'wb')
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
                    datafile = open(self.data_files_schema % filenr, 'wb')
                    full_size = 0
        finally:
            datafile.close()

    def convert_articles(self, image_dir):
        import re
        endpattern = re.compile('(_[0-9a-f]{4})?(\.html(\.redir)?)?$')

        datafiles_size = 500 * 1024 * 1024
        block_size = 512 * 1024

        articles = {}
        redirects = {}

        print("Compressing articles...")

        compressor = self.article_compressor_multi_bz2(
                            datafiles_size, block_size)
        (filenr, datafile_pos, block_pos) = compressor.next()

        for (dirpath, dirnames, filenames) in os.walk(image_dir):
            if 'coords' in dirnames:
                dirnames.remove('coords')
            for fname in filenames:
                if fname in ('creation_date', 'evopedia_version',
                             'index.html'):
                    break
                title = fname.decode('utf-8')
                title = endpattern.sub('', title).replace('_', ' ')

                f = os.path.join(dirpath, fname)
                if os.path.islink(f):
                    destination = endpattern.sub('', os.path.basename(
                                           os.readlink(f))).replace('_', ' ')
                    redirects[title] = destination.decode('utf-8')
                else:
                    with open(os.path.join(dirpath, fname), 'rb') as fd:
                        fdata = fd.read()
                    articles[title] = (filenr,
                                        datafile_pos, block_pos, len(fdata))
                    (filenr, datafile_pos, block_pos) = compressor.send(fdata)
        compressor.close()

        if __debug__:
            with open("article_list.txt", "wb") as articlelist:
                for (title, article_pos) in articles.items():
                    articlelist.write("%s\t%s\n" %
                                (title.encode("utf-8"), article_pos))

            with open("redirect_list.txt", "wb") as redirectlist:
                for (title, destination) in redirects.items():
                    redirectlist.write("%s\t%s\n" % (title.encode("utf-8"),
                                        destination.encode("utf-8")))
        return (articles, redirects)

    def convert_coordinates(self, image_dir, max_articles_per_section,
                            title_positions):
        import re
        endpattern = re.compile('(_[0-9a-f]{4})?(\.html(\.redir)?)?$')
        items = []

        print "Reading coordinates..."
        for (dirpath, dirnames, filenames) in os.walk(
                                        os.path.join(image_dir, 'coords')):
            for fname in filenames:
                f = os.path.join(dirpath, fname)
                if not os.path.islink(f):
                    continue
                (lat, lon, name) = fname.split(',', 2)
                lat = float(lat)
                lon = float(lon)
                title = name.decode('utf-8')
                title = endpattern.sub('', title).replace('_', ' ')
                if title not in title_positions:
                    continue
                else:
                    items += [(lat, lon, title_positions[title])]

        print "Generating quadtrees..."
        data = self.get_quadtree_index_table(items,
                                      -91.0, 91.0, -181.0, 181.0,
                                      max_articles_per_section)
        with open(self.coordinates_file, 'wb') as coord_file:
            coord_file.write(data)

    def get_quadtree_index_table(self, items,
                                 minlat, maxlat, minlon, maxlon,
                                 maxitems):
        print("Entered %f %f %f %f." % (minlat, maxlat, minlon, maxlon))
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
                print("Storing %f %f %d" % (lat, lon, title_pos))
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
        print("Usage: %s --convert <dir> <date> <language> <orig url>\n"
              "              converts an evopedia 2.0 article image\n"
              "              mounted at <dir> to evopedia 3.0 format\n"
              "          --article <text>\n"
              "              returns article with name <text>\n"
              "          <text>\n"
              "              searches for <text>" % sys.argv[0])
    else:
        backend = DatafileStorage()

        if sys.argv[1] == '--convert':
            backend.storage_create(sys.argv[2],
                                'titles.idx', 'coordinates.idx',
                                'wikipedia_%02d.dat', 'metadata.txt',
                                sys.argv[3], sys.argv[4], sys.argv[5])
        elif sys.argv[1] == '--article':
            backend.storage_init_read('titles.idx', 'coordinates.idx',
                                    'wikipedia_%02d.dat', 'metadata.txt')
            print backend.get_article_by_name(sys.argv[2].decode('utf-8'))
        else:
            backend.storage_init_read('titles.idx', 'coordinates.idx',
                                    'wikipedia_%02d.dat', 'metadata.txt')
            prefix = sys.argv[1].decode('utf-8')
            titles = backend.get_titles_with_prefix(prefix)
            for title, pos in itertools.islice(titles, 10):
                print "%s - %s" % (title.encode('utf-8'), pos)
