#!/bin/bash

# mediawiki mysql settings
dbuser=USER
password=PASSWORD
database=wikidb
MYSQL_OPTS=""

# SUDOCMD is used to access the database files directly
SUDOCMD="sudo"
MYSQLDIR="/var/lib/mysql/wikidb"
# directory where the git repository is checked out
REPODIR="/home/user/evopedia/"
LIBDIR="$REPODIR/evopedia/evopedia/"
SCRIPTDIR="$REPODIR/dumpscripts/"
MEDIAWIKIDIR="$REPODIR/mediawiki-1.14.0-evopediamod/"

# temporary and target directories
DUMPDIR="/tmp/evopedia_dumps/"
SOURCEDUMPDIR="$DUMPDIR/source_dumps"
IMPORTTEMPDIR="$DUMPDIR/import_temp"
DESTDUMPTEMPDIR="$DUMPDIR/dumps_temp"
DESTDUMPDIR="$DUMPDIR/dumps"

# use this for distributed dump generation
SLICENUMBER=$1

. "$SCRIPTDIR/dumplib.sh"

mkdir "$DUMPDIR" "$SOURCEDUMPDIR" "$IMPORTTEMPDIR" "$DESTDUMPTEMPDIR" "$DESTDUMPDIR" 2>/dev/null

# initialize the database by loading wikimedia commons (images)
# if you run the script multiple times for multiple languages
# you can comment out these two lines after the first run
getSourceDumps "commons"
importLanguage "commons" "commons_"

for language in de # you can put more languages here
do
	getSourceDumps $language
	importLanguage $language
	dumpWiki $language "$SLICENUMBER"
        if [ ! -n "$SLICENUMBER" ]
        then
            packageDump $language
        fi
done
