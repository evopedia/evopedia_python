#!/bin/sh

HTTP_PORT="8080"
BROWSER="/usr/bin/midori"
[ -f /etc/evopedia.conf ] && . /etc/evopedia.conf

/etc/init.d/evopedia start

"$BROWSER" "http://127.0.0.1:$HTTP_PORT"
