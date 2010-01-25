#!/bin/bash

getSourceDumps()
{
        LANG="$1"
        echo "Downloading dumps for language $LANG."
        DATE="$2"
        [ e"$DATE" = e ] && DATE="latest"

        DESTDIR="$SOURCEDUMPDIR/$LANG"
        mkdir "$DESTDIR"
        wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-pages-articles.xml.bz2" -O "$DESTDIR/wiki-latest-pages-articles.xml.bz2" || exit 1
        wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-image.sql.gz" -O "$DESTDIR/wiki-latest-image.sql.gz" || exit 1
        if [ "$LANG" != commons ]
        then
            wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-pages-articles.xml.bz2-rss.xml" -O "$DESTDIR/info.rss" || exit 1
            wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-category.sql.gz" -O "$DESTDIR/wiki-latest-category.sql.gz" || exit 1
            wget -nv "http://download.wikimedia.org/""$LANG""wiki/""$DATE""/""$LANG""wiki-""$DATE""-categorylinks.sql.gz" -O "$DESTDIR/wiki-latest-categorylinks.sql.gz" || exit 1
        fi
}


createTables()
{
        PREFIX="$1"
        echo "(Re-)creating db tables for prefix \"$PREFIX""\"."
        cat "$SCRIPTDIR/wikidb.sql" | sed -e 's/__PREFIX__/'"$PREFIX"'/' | mysql "$MYSQL_OPTS" -u "$dbuser" --password=$password "$database"
        cat "$SCRIPTDIR/wikipedia-interwiki.sql" | sed -e 's/__PREFIX__/'"$PREFIX"'/' | mysql "$MYSQL_OPTS" -u "$dbuser" --password=$password "$database"
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
                mysqlimport "$MYSQL_OPTS" -u "$dbuser" --password="$password" --local "$database" "$DUMPFILE"
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
        # remove the drop and recreate table (with potentially different engine) statements

        if [ x"$PREFIX" != x ]
        then
                echo "RENAME TABLE image TO $PREFIX""image;"
                echo "RENAME TABLE image_switch_temp TO image;"
        fi
        ) | mysql "$MYSQL_OPTS" -u "$dbuser" --password=$password "$database"

        if [ "$LANG" != commons ]
        then
            echo "Importing categories..."
            (
            gunzip -c < "$SOURCEDUMPDIR/$LANG/wiki-latest-category.sql.gz" | \
            awk -- '/DROP TABLE/,/-- Dumping data/ {next}; {print};'
            # remove the drop and recreate table (with potentially different engine) statements
            ) | mysql "$MYSQL_OPTS" -u "$dbuser" --password=$password "$database"
            (
            gunzip -c < "$SOURCEDUMPDIR/$LANG/wiki-latest-categorylinks.sql.gz" | \
            awk -- '/DROP TABLE/,/-- Dumping data/ {next}; {print};'
            # remove the drop and recreate table (with potentially different engine) statements
            ) | mysql "$MYSQL_OPTS" -u "$dbuser" --password=$password "$database"

            WIKIUSERSETTINGS='$wgDBname = "'"$database"'"; $wgDBuser = "'"$dbuser"'"; $wgDBpassword = "'"$password"'";'

            echo "Import done, changing mediawiki settings..."
            (
            cat "$MEDIAWIKIDIR/LocalSettings.in.php" | sed -e 's/__WIKIUSERSETTINGS__/'"$WIKIUSERSETTINGS"'/'
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
        fi
        echo "done."
}

dumpWiki()
{
        LANG="$1"
        SLICENUMBER="$2"

        rm -r "$DESTDUMPTEMPDIR/$LANG" 2>/dev/null
        mkdir "$DESTDUMPTEMPDIR/$LANG"
        mkdir "$DESTDUMPDIR/$LANG"
        #php "$MEDIAWIKIDIR/extensions/DumpHTML/dumpHTML.php" --checkpoint "/tmp/dump_checkpoint_$LANG" -d "$DESTDUMPTEMPDIR/$LANG"
        slices=40
        if [ -n "$SLICENUMBER" ]
        then
            php "$MEDIAWIKIDIR/extensions/DumpHTML/dumpHTML.php" -d "$DESTDUMPTEMPDIR/$LANG" --slice $SLICENUMBER/$slices
        else
            for i in `seq 1 $slices`
            do
                echo "Doing slice $i of $slices"
                php "$MEDIAWIKIDIR/extensions/DumpHTML/dumpHTML.php" -d "$DESTDUMPTEMPDIR/$LANG" --slice $i/$slices
            done
        fi
}

packageDump()
{
        LANG="$1"

        dumpdate=`cat "$SOURCEDUMPDIR/$LANG/info.rss" | \
        grep '<title>http://download.wikimedia.org/' | \
        sed -e 's/.*download.wikimedia.org\/.*\/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)<\/title>.*/\1-\2-\3/'`

        (
        cd "$DESTDUMPDIR/$LANG/"
        $LIBDIR/datafile_storage.py --convert "$DESTDUMPTEMPDIR/$LANG/" "$dumpdate" "$LANG" "http://$LANG.wikipedia.org/wiki/"
        zip -1 wikipedia_"$LANG"_"$dumpdate".zip *.idx *.dat metadata.txt
        )

        #rm -r "$DESTDUMPTEMPDIR/$LANG"
        # XXX remove other files
}
