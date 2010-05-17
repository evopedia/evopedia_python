#!/usr/bin/python

from evopedia import evopedia
import sys

evopedia.start_server('--maemo-browser' in sys.argv)
