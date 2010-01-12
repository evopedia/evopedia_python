#!/bin/bash

# mediawiki mysql settings
dbuser=root
password=PASSWORD
database=wikidb

# directory where this script and the contents of the scripts archive are
SCRIPTDIR="/mnt/storage/scripts"

# directory where mediawiki is installed
MEDIAWIKIDIR="/var/www/wikipedia"

# temporary and target directories
SOURCEDUMPDIR="/mnt/storage/source_dumps"
IMPORTTEMPDIR="/mnt/storage/import_temp"
DESTDUMPTEMPDIR="/mnt/storage/dumps_temp"
DESTDUMPDIR="/mnt/storage/dumps"

# also see the end of this script

getSourceDumps()
{
	LANG="$1"
	echo "Downloading dumps for language $LANG."
	DATE="$2"
	[ e"$DATE" = e ] && DATE="latest"

	DESTDIR="$SOURCEDUMPDIR/$LANG"
	mkdir "$DESTDIR"
	wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-pages-articles.xml.bz2-rss.xml" -O "$DESTDIR/info.rss"
	wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-pages-articles.xml.bz2" -O "$DESTDIR/wiki-latest-pages-articles.xml.bz2"
	wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-image.sql.gz" -O "$DESTDIR/wiki-latest-image.sql.gz"
	wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-category.sql.gz" -O "$DESTDIR/wiki-latest-category.sql.gz"
}


createTables()
{
	PREFIX="$1"
	echo "(Re-)creating db tables for prefix \"$PREFIX""\"."
	cat "$SCRIPTDIR/wikidb.sql" | sed -e 's/__PREFIX__/'"$PREFIX"'/' | mysql -u "$dbuser" --password=$password "$database"
	cat "$SCRIPTDIR/wikipedia-interwiki.sql" | sed -e 's/__PREFIX__/'"$PREFIX"'/' | mysql -u "$dbuser" --password=$password "$database"
}


importLanguage()
{
	LANG="$1"
	PREFIX="$2"

	echo "Importing wikipedia $LANG"

	createTables "$PREFIX"

	echo "Extracting xml dump..."
	rm "$IMPORTTEMPDIR"/*

	bunzip2 < "$SOURCEDUMPDIR/$LANG/"wiki-latest-pages-articles.xml.bz2 | \
	grep -v '<redirect />' | "$SCRIPTDIR"/xml2sql -o "$IMPORTTEMPDIR" -v
	# we have to remove all <redirect /> tags because xml2sql cannot handle them
	# (the bug does not occur with wikipedia dumps prior to july 2009)

	for x in page revision text
	do
		echo "Importing table $x..."
		DUMPFILE="$IMPORTTEMPDIR/$PREFIX""$x.txt"
		[ x"$PREFIX" != x ] && mv "$IMPORTTEMPDIR/$x.txt" "$DUMPFILE"
		mysqlimport -u "$dbuser" --password="$password" --local "$database" "$DUMPFILE"
		rm "$DUMPFILE"
	done

	echo "Importing images..."
	(
	if [ x"$PREFIX" != x ]
	then
		echo "DROP TABLE IF EXISTS image_switch_temp;"
		echo "RENAME TABLE image TO image_switch_temp;"
		echo "RENAME TABLE $PREFIX""image TO image;"
	fi

	gunzip -c < "$SOURCEDUMPDIR/$LANG/wiki-latest-image.sql.gz" | \
	awk -- '/DROP TABLE/,/-- Dumping data/ {next}; {print};'
	# remove the drop and recreate table (with potentially other engine) statements

	if [ x"$PREFIX" != x ]
	then
		echo "RENAME TABLE image TO $PREFIX""image;"
		echo "RENAME TABLE image_switch_temp TO image;"
	fi
	) | mysql -u "$dbuser" --password=$password "$database"

	echo "Importing categories..."
	(
	gunzip -c < "$SOURCEDUMPDIR/$LANG/wiki-latest-category.sql.gz" | \
	awk -- '/DROP TABLE/,/-- Dumping data/ {next}; {print};'
	# remove the drop and recreate table (with potentially other engine) statements
	) | mysql -u "$dbuser" --password=$password "$database"

	echo "Import done, changing mediawiki settings..."
	(
	cat "$MEDIAWIKIDIR/LocalSettings.in.php"
	echo '$wgLanguageCode = "'$LANG'";
		$wgLocalFileRepo = array(
		    "class" => "ForeignDBRepo",
		    "name" => "local",
		    "url" => "http://upload.wikimedia.org/wikipedia/'$LANG'",
		    "hashLevels" => 2, // This must be the same for the other family member
		    //"thumbScriptUrl" => "http://wiki.example.com/thumb.php",
		    "transformVia404" => true,//!$wgGenerateThumbnailOnParse,
		    "dbType" => $wgDBtype,
		    "dbServer" => $wgDBserver,
		    "dbUser" => $wgDBuser,
		    "dbPassword" => $wgDBpassword,
		    "dbName" => $wgDBname,
		    "tablePrefix" => "",
		    "hasSharedCache" => false,
		    "descBaseUrl" => "http://'$LANG'.wikimedia.org/wiki/File:",
		    "fetchDescription" => false
		);'
	) > "$MEDIAWIKIDIR/LocalSettings.php"
	#echo "Populating some tables..."
	#php "$MEDIAWIKIDIR/maintenance/refreshLinks.php"
	#php "$MEDIAWIKIDIR/maintenance/populateCategory.php"
	echo "done."

}

dumpWiki()
{
	LANG="$1"

	rm -r "$DESTDUMPTEMPDIR/$LANG" 2>/dev/null
	mkdir "$DESTDUMPTEMPDIR/$LANG"
	mkdir "$DESTDUMPDIR/$LANG"
	#php "$MEDIAWIKIDIR/extensions/DumpHTML/dumpHTML.php" --checkpoint "/tmp/dump_checkpoint_$LANG" -d "$DESTDUMPTEMPDIR/$LANG"
	slices=40
	for i in `seq 1 $slices`
	do
		echo "Doing slice $i of $slices"
		php "$MEDIAWIKIDIR/extensions/DumpHTML/dumpHTML.php" -d "$DESTDUMPTEMPDIR/$LANG" --slice $i/$slices
	done
}

packageDump()
{
	LANG="$1"

        rm -r "$DESTDUMPTEMPDIR/$LANG/raw"
        rm -r "$DESTDUMPTEMPDIR/$LANG/misc"
        #rm -r "$DESTDUMPTEMPDIR/$LANG/skins"
        #rm -r "$DESTDUMPTEMPDIR/$LANG/dumpHTML.version"
        #rm -r "$DESTDUMPTEMPDIR/$LANG/index.html"
        # XXX localize that
        #cp "$DESTDUMPTEMPDIR/$LANG/index.html" "$DESTDUMPTEMPDIR/$LANG/Hauptseite"

	dumpdate=`cat "$SOURCEDUMPDIR/$LANG/info.rss" | \
        grep '<title>http://download.wikimedia.org/dewiki/' | \
        sed -e 's/.*download.wikimedia.org\/dewiki\/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)<\/title>.*/\1-\2-\3/'`

        (
        cd "$DESTDUMPDIR/$LANG/"
        $SCRIPTDIR/datafile_storage.py --convert "$DESTDUMPTEMPDIR/$LANG/" "$dumpdate" "$LANG" "http://$LANG.wikipedia.org/wiki/"
        tar czvf "$DESTDUMPDIR/$LANG"/wikipedia_"$LANG"_"$DATE".tar.gz "$DESTDUMPDIR/$LANG"/*.idx "$DESTDUMPDIR/$LANG"/*.dat "$DESTDUMPDIR/$LANG/metadata.txt"
        )

	#rm -r "$DESTDUMPTEMPDIR/$LANG"
        # XXX remove other files
}


# initialize the database by loading wikimedia commons (images)
# if you run the script multiple times for multiple languages
# you can comment out these two lines after the first run
getSourceDumps "commons"
importLanguage "commons" "commons_"

for language in fr # you can put more languages here
do
	getSourceDumps $language
	importLanguage $language
	dumpWiki $language
        packageDump $language
done
